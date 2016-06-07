def test_import_gnome_keyring():
    import keyring
    keyring.set_keyring(keyring.backends.Gnome.Keyring())
    keyring.get_password("test", "test")


if __name__ == '__main__':
    test_import_gnome_keyring()