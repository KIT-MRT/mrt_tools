from mrt_tools.CredentialManager import *

USER = "pytest_user"
PASSW = "pytest_pw"
TOKEN = "pytest_token"
PLACEHOLDER = "placeholder"
click.prompt = lambda _, default=None, hide_input=False: PLACEHOLDER


def store_credentials(cm):
    cm.store("username", USER)
    cm.store("password", PASSW)
    cm.store("token", TOKEN)

    assert cm.get("username") == USER
    assert cm.get("password") == PASSW
    assert cm.get("token") == TOKEN
    assert cm.get_credentials(quiet=True) == (USER, PASSW)
    assert cm.get_username(quiet=True) == USER
    assert cm.get_username(quiet=False) == USER
    assert cm.get_password(USER, quiet=True) == PASSW
    assert cm.get_password(USER, quiet=False) == PASSW
    assert cm.get_token() == TOKEN


def delete_credentials(cm):
    cm.delete("username")
    cm.delete("password")
    cm.delete("token")

    assert cm.get("username") is None
    assert cm.get("password") is None
    assert cm.get("token") is None
    assert cm.get_credentials(quiet=True) == (None, None)
    assert cm.get_username(quiet=True) is None
    assert cm.get_password(USER, quiet=True) is None
    assert cm.get_token() is None


def test_base_credential_manager():
    cm = BaseCredentialManager()
    delete_credentials(cm)
    store_credentials(cm)
    delete_credentials(cm)


def test_dummy_credential_manager():
    cm = DummyCredentialManager()

    delete_credentials(cm)

    cm.store("username", USER)
    cm.store("password", PASSW)
    cm.store("token", TOKEN)
    assert cm.get("username") is None
    assert cm.get("password") is None
    assert cm.get("token") is None
    assert cm.get_credentials(quiet=True) == (None, None)
    assert cm.get_username(quiet=True) is None
    assert cm.get_username(quiet=False) is None
    assert cm.get_password(USER, quiet=True) is None
    assert cm.get_password(USER, quiet=False) is None
    assert cm.get_token() is None

    delete_credentials(cm)


def test_gnome_credential_manager():
    cm = GnomeCredentialManager()
    delete_credentials(cm)
    store_credentials(cm)
    delete_credentials(cm)
    assert cm.get_username(quiet=False) == PLACEHOLDER
    assert cm.get_password(USER, quiet=False) == PLACEHOLDER
    delete_credentials(cm)


def test_file_credential_manager():
    cm = FileCredentialManager()
    delete_credentials(cm)
    store_credentials(cm)
    delete_credentials(cm)


if __name__ == '__main__':
    test_base_credential_manager()
    test_file_credential_manager()
    test_gnome_credential_manager()
