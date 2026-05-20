"""ACPToolCallEvent — surfaces ACP tool call trajectories as OpenHands events."""

from __future__ import annotations

from typing import Any

from rich.text import Text

from openhands.sdk.event.base import Event
from openhands.sdk.event.types import SourceType


_MAX_DISPLAY_CHARS = 500


def _block_field(block: Any, name: str) -> Any:
    """Read ``name`` from a content block that may be a model or a dict.

    ACP content blocks travel as Pydantic models in-process and as plain
    dicts after persistence (see ``_serialize_tool_content`` which calls
    ``model_dump``). Both shapes need to be readable.
    """
    if isinstance(block, dict):
        return block.get(name)
    return getattr(block, name, None)


class ACPToolCallEvent(Event):
    """Event representing a tool call executed by an ACP server.

    Captures the tool name, inputs, outputs, and status from ACP
    ``ToolCallStart`` / ``ToolCallProgress`` notifications so they can
    be surfaced in the OpenHands event stream and visualizer.

    This is *not* an ``LLMConvertibleEvent`` — ACP tool calls do not
    participate in LLM message conversion.
    """

    source: SourceType = "agent"
    tool_call_id: str
    title: str
    status: str | None = None
    tool_kind: str | None = None
    raw_input: Any | None = None
    raw_output: Any | None = None
    content: list[Any] | None = None
    is_error: bool = False

    @property
    def is_patch_edit(self) -> bool:
        """True if this event represents a patch/diff edit (not a full-file write).

        ACP-spec edit tools emit a ``diff`` content block whose ``old_text``
        field distinguishes the two cases:
          * patch edit (e.g. ``Edit``): ``old_text`` is set
          * full-file create (e.g. ``Write``): ``old_text`` is ``None``

        This check is provider-agnostic across Claude Code, Codex, and Gemini
        servers that follow the ACP spec.

        The content block is read defensively: it may arrive as a Pydantic
        model with attributes (live ACP notifications) or as a plain dict
        (after persistence — ``_serialize_tool_content`` stores blocks via
        ``model_dump``). Both shapes are accepted.

        For providers that omit the structured content block but still
        expose the diff intent through raw input keys, the check falls back
        to ``raw_input``. The fallback requires a non-empty ``old_string`` —
        a ``new_string``-only payload (or empty ``old_string``) describes a
        create/write, not a patch.
        """
        content = self.content or []
        if content:
            first = content[0]
            block_type = _block_field(first, "type")
            if block_type == "diff":
                return _block_field(first, "old_text") is not None
        raw = self.raw_input if isinstance(self.raw_input, dict) else {}
        old = raw.get("old_string")
        return isinstance(old, str) and len(old) > 0

    @property
    def visualize(self) -> Text:
        """Return Rich Text representation of this tool call event."""
        content = Text()
        content.append(self.title, style="bold")

        # Kind / status metadata line
        meta_parts: list[str] = []
        if self.tool_kind:
            meta_parts.append(f"kind={self.tool_kind}")
        if self.status:
            meta_parts.append(f"status={self.status}")
        if meta_parts:
            content.append(f"\n{' | '.join(meta_parts)}", style="dim")

        # Input (skip None and empty containers like {})
        if self.raw_input:
            input_str = str(self.raw_input)
            if len(input_str) > _MAX_DISPLAY_CHARS:
                input_str = input_str[:_MAX_DISPLAY_CHARS] + "..."
            content.append("\nInput: ", style="bold")
            content.append(input_str)

        # Output (skip None and empty containers)
        if self.raw_output:
            output_str = str(self.raw_output)
            if len(output_str) > _MAX_DISPLAY_CHARS:
                output_str = output_str[:_MAX_DISPLAY_CHARS] + "..."
            content.append("\nOutput: ", style="bold")
            content.append(output_str)

        return content

    def __str__(self) -> str:
        parts = [f"{self.__class__.__name__} ({self.source}): {self.title}"]
        if self.status:
            parts.append(f"[{self.status}]")
        if self.tool_kind:
            parts.append(f"({self.tool_kind})")
        return " ".join(parts)
