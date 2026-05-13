"""Tests for the OH_EXTRA_PYTHON_PATH helper."""

import os
import sys
import textwrap

import pytest

from openhands.agent_server.extra_python_path import (
    OH_EXTRA_PYTHON_PATH_ENV,
    apply_extra_python_path,
    apply_extra_python_path_from_env,
)


@pytest.fixture
def sys_path_snapshot():
    """Restore sys.path to its pre-test state so tests don't leak into each other."""
    snapshot = list(sys.path)
    yield snapshot
    sys.path[:] = snapshot


class TestApplyExtraPythonPath:
    def test_none_is_noop(self, sys_path_snapshot):
        apply_extra_python_path(None)
        assert sys.path == sys_path_snapshot

    def test_empty_string_is_noop(self, sys_path_snapshot):
        apply_extra_python_path("")
        assert sys.path == sys_path_snapshot

    def test_single_path_is_prepended(self, tmp_path, sys_path_snapshot):
        apply_extra_python_path(str(tmp_path))
        assert sys.path[0] == str(tmp_path)

    def test_multiple_paths_separated_by_os_pathsep(self, tmp_path, sys_path_snapshot):
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()

        apply_extra_python_path(os.pathsep.join([str(a), str(b)]))

        assert str(a) in sys.path
        assert str(b) in sys.path

    def test_idempotent_for_already_present_path(self, tmp_path, sys_path_snapshot):
        apply_extra_python_path(str(tmp_path))
        before = list(sys.path)

        apply_extra_python_path(str(tmp_path))

        assert sys.path == before

    def test_empty_segments_and_whitespace_skipped(self, tmp_path, sys_path_snapshot):
        a = tmp_path / "a"
        a.mkdir()
        apply_extra_python_path(f"  {a}  {os.pathsep}{os.pathsep}  ")

        assert str(a) in sys.path
        assert "" not in sys.path


class TestApplyExtraPythonPathFromEnv:
    def test_reads_env_var(self, tmp_path, monkeypatch, sys_path_snapshot):
        monkeypatch.setenv(OH_EXTRA_PYTHON_PATH_ENV, str(tmp_path))

        apply_extra_python_path_from_env()

        assert str(tmp_path) in sys.path

    def test_missing_env_var_is_noop(self, monkeypatch, sys_path_snapshot):
        monkeypatch.delenv(OH_EXTRA_PYTHON_PATH_ENV, raising=False)

        apply_extra_python_path_from_env()

        assert sys.path == sys_path_snapshot


class TestExternalModuleBecomesImportable:
    """Integration: a .py file in a directory added via apply_extra_python_path
    must become importable, which is the whole point of the helper.
    """

    @pytest.fixture
    def external_tool_module(self, tmp_path, sys_path_snapshot):
        """Drop a fake custom-tool .py file outside sys.path."""
        module_name = "extra_python_path_test_tool_xyz"
        (tmp_path / f"{module_name}.py").write_text(
            textwrap.dedent(
                """\
                LOADED = True
                """
            )
        )
        sys.modules.pop(module_name, None)
        yield tmp_path, module_name
        sys.modules.pop(module_name, None)

    def test_module_unimportable_before_apply(self, external_tool_module):
        _, module_name = external_tool_module
        with pytest.raises(ModuleNotFoundError):
            __import__(module_name)

    def test_module_importable_after_apply(self, external_tool_module):
        tmp_path, module_name = external_tool_module

        apply_extra_python_path(str(tmp_path))
        imported = __import__(module_name)

        assert imported.LOADED is True


class TestMainCliWiring:
    """Verify the --extra-python-path flag and OH_EXTRA_PYTHON_PATH env var
    apply paths before preload_modules runs — the ordering this exists to
    fix.
    """

    def test_env_var_applied_before_preload(
        self, tmp_path, monkeypatch, sys_path_snapshot
    ):
        from unittest.mock import patch

        observed = {}

        def fake_preload(arg):
            observed["sys_path_at_preload"] = list(sys.path)

        monkeypatch.setenv(OH_EXTRA_PYTHON_PATH_ENV, str(tmp_path))

        with (
            patch("sys.argv", ["prog"]),
            patch(
                "openhands.agent_server.__main__.preload_modules",
                side_effect=fake_preload,
            ),
            patch("openhands.agent_server.__main__.LoggingServer") as mock_server_cls,
        ):
            mock_server_cls.return_value.run.side_effect = SystemExit(0)

            from openhands.agent_server.__main__ import main

            with pytest.raises(SystemExit):
                main()

        assert str(tmp_path) in observed["sys_path_at_preload"], (
            "OH_EXTRA_PYTHON_PATH must be applied to sys.path before "
            "preload_modules runs"
        )

    def test_cli_flag_overrides_env_default(
        self, tmp_path, monkeypatch, sys_path_snapshot
    ):
        from unittest.mock import patch

        flag_dir = tmp_path / "from_flag"
        env_dir = tmp_path / "from_env"
        flag_dir.mkdir()
        env_dir.mkdir()

        monkeypatch.setenv(OH_EXTRA_PYTHON_PATH_ENV, str(env_dir))

        with (
            patch(
                "sys.argv",
                ["prog", "--extra-python-path", str(flag_dir)],
            ),
            patch("openhands.agent_server.__main__.preload_modules"),
            patch("openhands.agent_server.__main__.LoggingServer") as mock_server_cls,
        ):
            mock_server_cls.return_value.run.side_effect = SystemExit(0)

            from openhands.agent_server.__main__ import main

            with pytest.raises(SystemExit):
                main()

        assert str(flag_dir) in sys.path
        assert str(env_dir) not in sys.path, (
            "--extra-python-path should take precedence over the env-var default"
        )
