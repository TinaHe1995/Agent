"""ToolExecutor shims that connect ExecCommandTool / WriteStdinTool to the manager."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from openhands.sdk.tool import ToolExecutor
from openhands.tools.interactive_terminal.definition import (
    ExecCommandAction,
    InteractiveTerminalObservation,
    WriteStdinAction,
)


if TYPE_CHECKING:
    from openhands.sdk.conversation import LocalConversation
    from openhands.tools.interactive_terminal.impl import InteractiveTerminalManager


_log = logging.getLogger(__name__)


def _mask_output(output: str, conversation: LocalConversation | None) -> str:
    """Apply registered-secret masking to *output* if a conversation is available."""
    if not output or conversation is None:
        return output
    try:
        masked = conversation.state.secret_registry.mask_secrets_in_output(output)
        return masked or output
    except Exception:  # noqa: BLE001
        # Masking must never break tool execution — return raw output on any error
        # (e.g. malformed registry state, missing attribute on mock objects in tests).
        # Log the failure so a buggy masker does not leak secrets silently.
        _log.warning("Secret masking failed; returning unmasked output", exc_info=True)
        return output


def _resolve_env_vars(
    command: str, conversation: LocalConversation | None
) -> dict[str, str]:
    """Resolve secrets referenced by *command* into env vars for session export.

    Mirrors ``TerminalExecutor._export_envs``: secrets whose names appear in
    the command are resolved from the conversation's secret registry and
    returned as a ``{name: value}`` dict for ``InteractiveTerminalManager`` to
    export before the command runs.
    """
    if not command.strip() or conversation is None:
        return {}
    try:
        return conversation.state.secret_registry.get_secrets_as_env_vars(command)
    except Exception:  # noqa: BLE001
        _log.warning("Failed to resolve env vars for command", exc_info=True)
        return {}


class ExecCommandExecutor(
    ToolExecutor[ExecCommandAction, InteractiveTerminalObservation]
):
    def __init__(self, manager: InteractiveTerminalManager) -> None:
        self._manager = manager

    def __call__(
        self,
        action: ExecCommandAction,
        conversation: LocalConversation | None = None,
    ) -> InteractiveTerminalObservation:
        env_vars = _resolve_env_vars(action.cmd, conversation)
        output, wall, session_id, exit_code, original_token_count = (
            self._manager.exec_command(
                action.cmd,
                workdir=action.workdir,
                yield_time_ms=action.yield_time_ms,
                max_output_tokens=action.max_output_tokens,
                env_vars=env_vars or None,
            )
        )
        output = _mask_output(output, conversation)
        return InteractiveTerminalObservation.create(
            output, wall, session_id, exit_code, original_token_count
        )

    def close(self) -> None:
        self._manager.close()

    def interrupt(self) -> None:
        self._manager.interrupt()


class WriteStdinExecutor(
    ToolExecutor[WriteStdinAction, InteractiveTerminalObservation]
):
    def __init__(self, manager: InteractiveTerminalManager) -> None:
        self._manager = manager

    def __call__(
        self,
        action: WriteStdinAction,
        conversation: LocalConversation | None = None,
    ) -> InteractiveTerminalObservation:
        output, wall, session_id, exit_code, original_token_count = (
            self._manager.write_stdin(
                action.session_id,
                chars=action.chars,
                yield_time_ms=action.yield_time_ms,
                max_output_tokens=action.max_output_tokens,
            )
        )
        output = _mask_output(output, conversation)
        return InteractiveTerminalObservation.create(
            output, wall, session_id, exit_code, original_token_count
        )

    def close(self) -> None:
        self._manager.close()

    def interrupt(self) -> None:
        self._manager.interrupt()
