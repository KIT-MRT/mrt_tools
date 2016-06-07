from mrt_tools.CredentialManager import *

USER = "pytest_user"
PASSW = "pytest_pw"
TOKEN = "pytest_token"


def test_base_credential_manager():
    cm = BaseCredentialManager()
    cm.store(USER, USER)
    cm.store(PASSW, PASSW)
    cm.store(TOKEN, TOKEN)

    assert cm.get(USER) == ""
    assert cm.get(PASSW) == ""
    assert cm.get(TOKEN) == ""

    cm.delete(USER)
    cm.delete(PASSW)
    cm.delete(TOKEN)

    assert cm.get(USER) == ""
    assert cm.get(PASSW) == ""
    assert cm.get(TOKEN) == ""


def test_gnome_credential_manager():
    # cm = GnomeCredentialManager()
    # cm.store(USER, USER)
    # cm.store(PASSW, PASSW)
    # cm.store(TOKEN, TOKEN)
    #
    # assert cm.get(USER) == USER
    # assert cm.get(PASSW) == PASSW
    # assert cm.get(TOKEN) == TOKEN
    #
    # cm.delete(USER)
    # cm.delete(PASSW)
    # cm.delete(TOKEN)
    #
    # assert cm.get(USER) is None
    # assert cm.get(PASSW) is None
    # assert cm.get(TOKEN) is None
    # TODO This is not working yet
    pass


def test_file_credential_manager():
    cm = FileCredentialManager()
    cm.store(USER, USER)
    cm.store(PASSW, PASSW)
    cm.store(TOKEN, TOKEN)

    assert cm.get(USER) == USER
    assert cm.get(PASSW) == PASSW
    assert cm.get(TOKEN) == TOKEN

    cm.delete(USER)
    cm.delete(PASSW)
    cm.delete(TOKEN)

    assert cm.get(USER) is None
    assert cm.get(PASSW) is None
    assert cm.get(TOKEN) is None


if __name__ == '__main__':
    test_base_credential_manager()
    test_file_credential_manager()
    test_gnome_credential_manager()
