from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from openhands.sdk.extensions.installation import InstallationInfo
from openhands.sdk.utils.cipher import Cipher


@dataclass
class MockExtension:
    name: str
    version: str
    description: str


def test_installation_info_from_extension():
    """Test InstallationInfo construction from extensions populates as expected."""
    extension = MockExtension(
        name="name", version="0.1.2", description="Test extension please ignore"
    )
    source = "local"
    install_path = Path.cwd()
    info = InstallationInfo.from_extension(extension, source, install_path)

    assert info.name == extension.name
    assert info.version == extension.version
    assert info.description == extension.description

    assert info.source == source
    assert info.install_path == install_path

    assert info.enabled

    assert info.resolved_ref is None
    assert info.repo_path is None

    assert datetime.fromisoformat(info.installed_at)


def test_source_redacted_by_default_exposed_under_context():
    """Default dumps mask the credential; expose_secrets keeps the real source."""
    cred = "https://oauth2:SUPER_SECRET@github.com/org/repo.git"
    info = InstallationInfo(name="x", source=cred, install_path=Path("/tmp/x"))
    assert info.source == cred  # raw in memory
    assert "SUPER_SECRET" not in info.model_dump_json()  # default redacts
    assert info.model_dump(context={"expose_secrets": "plaintext"})["source"] == cred


def test_source_encrypts_at_rest_under_cipher():
    """A cipher context encrypts the source and decrypts it back on load."""
    cipher = Cipher("k")
    cred = "https://oauth2:SUPER_SECRET@github.com/org/repo.git"
    info = InstallationInfo(name="x", source=cred, install_path=Path("/tmp/x"))
    token = info.model_dump(context={"cipher": cipher})["source"]
    assert token.startswith("gAAAAA")
    assert "SUPER_SECRET" not in token
    back = InstallationInfo.model_validate(
        {"name": "x", "source": token, "install_path": "/tmp/x"},
        context={"cipher": cipher},
    )
    assert back.source == cred
