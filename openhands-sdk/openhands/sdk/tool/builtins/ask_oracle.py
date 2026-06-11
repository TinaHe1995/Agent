from collections.abc import Sequence
from typing import TYPE_CHECKING, Self

from pydantic import Field
from rich.text import Text

from openhands.sdk.llm.llm_profile_store import PROFILE_NAME_REGEX, LLMProfileStore
from openhands.sdk.tool.registry import register_tool
from openhands.sdk.tool.tool import (
    Action,
    Observation,
    ToolAnnotations,
    ToolDefinition,
    ToolExecutor,
)


if TYPE_CHECKING:
    from openhands.sdk.conversation.impl.local_conversation import LocalConversation
    from openhands.sdk.conversation.state import ConversationState


class AskOracleAction(Action):
    """Action for asking a configured Oracle LLM profile for advice."""

    question: str = Field(
        description=(
            "The specific question or dilemma to ask the Oracle about. Use this "
            "when you are stuck, uncertain, or need a second opinion."
        )
    )
    context: str | None = Field(
        default=None,
        description=(
            "Optional extra context, such as approaches already tried, constraints, "
            "or the recommendation you are considering."
        ),
    )

    @property
    def visualize(self) -> Text:
        content = Text()
        content.append("Ask Oracle: ", style="bold cyan")
        content.append(self.question)
        if self.context:
            content.append("\nContext: ", style="bold")
            content.append(self.context)
        return content


class AskOracleObservation(Observation):
    """Observation returned by the Oracle consultation."""

    profile_name: str = Field(description="LLM profile used for the Oracle call.")
    oracle_model: str | None = Field(
        default=None,
        description="Model configured by the Oracle profile, when available.",
    )

    @property
    def visualize(self) -> Text:
        content = Text()
        if self.is_error:
            content.append("Oracle consultation failed", style="bold red")
        else:
            content.append("Oracle recommendation", style="bold green")
        content.append(f": {self.profile_name}")
        if self.oracle_model:
            content.append(f" ({self.oracle_model})")
        if self.text:
            content.append("\n")
            content.append(self.text)
        return content


_DESCRIPTION_TEMPLATE = (
    "Ask the Oracle for a second opinion. The Oracle is a configured, saved LLM "
    "profile intended to be more capable for difficult reasoning.\n\n"
    "Use this when you are stuck, uncertain, comparing approaches, or need a "
    "higher-quality recommendation before proceeding. The Oracle receives the "
    "current conversation context plus your question, but this consultation does "
    "not switch the active LLM profile.\n\n"
    "Treat the Oracle's response as strong guidance and follow its recommendation "
    "unless you have a clear reason not to.\n\n"
    "Configured Oracle profile: {profile_name}"
)

_ORACLE_PROMPT_TEMPLATE = """\
You are the Oracle: a highly capable reviewer giving a second opinion to an \
OpenHands agent.

The agent is working in an existing conversation. Use the conversation context you \
receive to answer the agent's question. Do not call tools. Do not perform work \
directly. Give a concrete recommendation the agent can follow, including important \
risks or caveats.

Question:
{question}
{context_section}"""


class AskOracleExecutor(ToolExecutor[AskOracleAction, AskOracleObservation]):
    def __init__(self, profile_name: str | None, profile_store_dir: str | None) -> None:
        self.profile_name = profile_name
        self.profile_store_dir = profile_store_dir

    def __call__(
        self,
        action: AskOracleAction,
        conversation: "LocalConversation | None" = None,
    ) -> AskOracleObservation:
        if not self.profile_name:
            return AskOracleObservation.from_text(
                text="No Oracle LLM profile is configured.",
                is_error=True,
                profile_name="",
            )
        if conversation is None:
            return AskOracleObservation.from_text(
                text="Cannot ask Oracle without an active conversation.",
                is_error=True,
                profile_name=self.profile_name,
            )

        try:
            oracle_llm = LLMProfileStore(self.profile_store_dir).load(
                self.profile_name, cipher=conversation._cipher
            )
        except FileNotFoundError:
            return AskOracleObservation.from_text(
                text=f"Oracle LLM profile '{self.profile_name}' was not found.",
                is_error=True,
                profile_name=self.profile_name,
            )
        except ValueError as exc:
            return AskOracleObservation.from_text(
                text=str(exc),
                is_error=True,
                profile_name=self.profile_name,
            )
        except Exception as exc:
            return AskOracleObservation.from_text(
                text=(
                    f"Failed to load Oracle LLM profile '{self.profile_name}': "
                    f"{type(exc).__name__}: {exc}"
                ),
                is_error=True,
                profile_name=self.profile_name,
            )

        # Lazy import avoids a startup cycle while built-in tools are registered.
        from openhands.sdk.agent.utils import (
            make_llm_completion,
            prepare_llm_messages,
        )
        from openhands.sdk.llm import Message, TextContent

        conversation._ensure_agent_ready()
        context_section = (
            f"\nAdditional context from the agent:\n{action.context}\n"
            if action.context
            else ""
        )
        oracle_prompt = _ORACLE_PROMPT_TEMPLATE.format(
            question=action.question,
            context_section=context_section,
        )
        user_message = Message(
            role="user",
            content=[TextContent(text=oracle_prompt)],
        )
        messages = prepare_llm_messages(
            conversation.state.view, additional_messages=[user_message]
        )

        try:
            response = make_llm_completion(
                oracle_llm.model_copy(
                    update={"usage_id": f"oracle-profile:{self.profile_name}"},
                    deep=True,
                ),
                messages,
                tools=list(conversation.agent.tools_map.values()),
            )
        except Exception as exc:
            return AskOracleObservation.from_text(
                text=(
                    f"Oracle LLM profile '{self.profile_name}' failed: "
                    f"{type(exc).__name__}: {exc}"
                ),
                is_error=True,
                profile_name=self.profile_name,
                oracle_model=oracle_llm.model,
            )

        oracle_text = "".join(
            content.text
            for content in response.message.content
            if isinstance(content, TextContent)
        ).strip()
        if not oracle_text:
            return AskOracleObservation.from_text(
                text="Oracle did not return a text recommendation.",
                is_error=True,
                profile_name=self.profile_name,
                oracle_model=oracle_llm.model,
            )

        return AskOracleObservation.from_text(
            text=oracle_text,
            profile_name=self.profile_name,
            oracle_model=oracle_llm.model,
        )


class AskOracleTool(ToolDefinition[AskOracleAction, AskOracleObservation]):
    """Tool for consulting a configured Oracle LLM profile."""

    @classmethod
    def create(
        cls,
        conv_state: "ConversationState | None" = None,  # noqa: ARG003
        profile_name: str | None = None,
        profile_store_dir: str | None = None,
        **params,
    ) -> Sequence[Self]:
        if params:
            raise ValueError(
                "AskOracleTool only accepts profile_name and profile_store_dir"
            )
        if profile_name is not None and not PROFILE_NAME_REGEX.match(profile_name):
            raise ValueError(
                "Invalid Oracle profile name. Profile names must be 1-64 "
                "characters, start with a letter or digit, and contain only "
                "letters, digits, '.', '_', or '-'."
            )

        profile_display = profile_name or "not configured"
        return [
            cls(
                description=_DESCRIPTION_TEMPLATE.format(profile_name=profile_display),
                action_type=AskOracleAction,
                observation_type=AskOracleObservation,
                executor=AskOracleExecutor(profile_name, profile_store_dir),
                annotations=ToolAnnotations(
                    readOnlyHint=True,
                    destructiveHint=False,
                    idempotentHint=False,
                    openWorldHint=False,
                ),
            )
        ]


register_tool(AskOracleTool.name, AskOracleTool)
