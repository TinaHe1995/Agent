from pathlib import Path

import pytest
from pydantic import ValidationError

from openhands.sdk import LLM, LocalConversation, OpenHandsAgentSettings, Tool
from openhands.sdk.agent import Agent
from openhands.sdk.llm import Message, TextContent, llm_profile_store
from openhands.sdk.llm.llm_profile_store import LLMProfileStore
from openhands.sdk.testing import TestLLM
from openhands.sdk.tool.builtins import (
    AskOracleAction,
    AskOracleObservation,
    AskOracleTool,
)


def _make_llm(model: str, usage_id: str) -> LLM:
    return TestLLM.from_messages([], model=model, usage_id=usage_id)


def _assistant_message(text: str) -> Message:
    return Message(role="assistant", content=[TextContent(text=text)])


def _make_conversation(profile_name: str = "oracle") -> LocalConversation:
    return LocalConversation(
        agent=Agent(
            llm=_make_llm("default-model", "default"),
            tools=[
                Tool(name=AskOracleTool.name, params={"profile_name": profile_name})
            ],
            include_default_tools=[],
        ),
        workspace=Path.cwd(),
    )


def test_ask_oracle_tool_description_names_configured_profile() -> None:
    tool = AskOracleTool.create(profile_name="oracle")[0]

    assert "Ask the Oracle for a second opinion" in tool.description
    assert "Configured Oracle profile: oracle" in tool.description


def test_ask_oracle_tool_validates_profile_name() -> None:
    with pytest.raises(ValueError, match="Invalid Oracle profile name"):
        AskOracleTool.create(profile_name="../oracle")


def test_agent_settings_adds_ask_oracle_tool_when_profile_is_configured() -> None:
    agent = OpenHandsAgentSettings(
        llm=_make_llm("default-model", "default"),
        oracle_llm_profile="oracle",
    ).create_agent()

    assert any(
        tool.name == AskOracleTool.name and tool.params == {"profile_name": "oracle"}
        for tool in agent.tools
    )

    conversation = LocalConversation(agent=agent, workspace=Path.cwd())
    conversation._ensure_agent_ready()
    assert "ask_oracle" in agent.tools_map


def test_agent_settings_omits_ask_oracle_tool_without_profile() -> None:
    agent = OpenHandsAgentSettings(
        llm=_make_llm("default-model", "default"),
    ).create_agent()

    assert all(tool.name != AskOracleTool.name for tool in agent.tools)

    conversation = LocalConversation(agent=agent, workspace=Path.cwd())
    conversation._ensure_agent_ready()
    assert "ask_oracle" not in agent.tools_map


def test_agent_settings_rejects_invalid_oracle_profile_name() -> None:
    with pytest.raises(ValidationError, match="oracle_llm_profile"):
        OpenHandsAgentSettings(oracle_llm_profile="../oracle")


def test_ask_oracle_tool_returns_oracle_recommendation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oracle_llm = TestLLM.from_messages(
        [_assistant_message("Prefer the smaller, typed settings field.")],
        model="oracle-model",
        usage_id="oracle",
    )

    def load_profile(
        self: LLMProfileStore,
        name: str,
        *,
        cipher=None,
    ) -> LLM:
        assert name == "oracle"
        return oracle_llm

    monkeypatch.setattr(LLMProfileStore, "load", load_profile)
    conversation = _make_conversation()

    observation = conversation.execute_tool(
        "ask_oracle",
        AskOracleAction(
            question="Should I add one setting or two?",
            context="The tool needs an Oracle profile name.",
        ),
    )

    assert isinstance(observation, AskOracleObservation)
    assert not observation.is_error
    assert observation.profile_name == "oracle"
    assert observation.oracle_model == "oracle-model"
    assert observation.text == "Prefer the smaller, typed settings field."
    assert "Prefer the smaller" in observation.visualize.plain
    assert conversation.agent.llm.model == "default-model"
    assert conversation.state.agent.llm.model == "default-model"


def test_ask_oracle_tool_reports_missing_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()

    monkeypatch.setattr(llm_profile_store, "_DEFAULT_PROFILE_DIR", profile_dir)
    conversation = _make_conversation(profile_name="missing")

    observation = conversation.execute_tool(
        "ask_oracle",
        AskOracleAction(question="What should I do next?"),
    )

    assert isinstance(observation, AskOracleObservation)
    assert observation.is_error
    assert observation.profile_name == "missing"
    assert "was not found" in observation.text


def test_ask_oracle_tool_reports_empty_oracle_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oracle_llm = TestLLM.from_messages(
        [Message(role="assistant", content=[])],
        model="oracle-model",
        usage_id="oracle",
    )

    def load_profile(
        self: LLMProfileStore,
        name: str,
        *,
        cipher=None,
    ) -> LLM:
        return oracle_llm

    monkeypatch.setattr(LLMProfileStore, "load", load_profile)
    conversation = _make_conversation()

    observation = conversation.execute_tool(
        "ask_oracle",
        AskOracleAction(question="What should I do next?"),
    )

    assert isinstance(observation, AskOracleObservation)
    assert observation.is_error
    assert observation.oracle_model == "oracle-model"
    assert "did not return a text recommendation" in observation.text
