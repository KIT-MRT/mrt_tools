from mrt_tools.settings import rw_config
import pytest
import os


@pytest.fixture(scope="module")
def working_directory(request):
    import tempfile
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    os.chdir(t)
    def fin():
        print ("Removing temporary directory")
        os.chdir(cwd)
        try:
            import shutil
            shutil.rmtree(t)
        except (OSError, IOError):
            pass
    request.addfinalizer(fin)
    return t

@pytest.fixture
def config_file(working_directory):
    return os.path.join(working_directory, "mrt.cfg")


@pytest.fixture
def default_settings():
    return {
        'Section1': {
            'Value_String': "Test",
            'Value_Bool': True,
            'Value_Int': 42,
        },
        'Section2': {
            'Key1': "Test",
        }
    }


def test_create_config(config_file, default_settings):
    # Make sure file doesn't exist before
    assert not os.path.isfile(config_file)
    # Create default config
    settings = default_settings
    rw_config(settings, config_file)
    # Make sure config file exists now
    assert os.path.isfile(config_file)


def test_read_config(config_file, default_settings):
    # Create default config
    settings = default_settings
    rw_config(settings, config_file)
    # Make sure default values get overwritten when reading config
    settings['Section1']['Value_String'] = "altered_string"
    settings['Section1']['Value_Bool'] = False
    settings['Section1']['Value_Int'] = 7
    # Now when reading the config, these altered values should be overwritten by user specified values (which are
    #  the old default values
    rw_config(settings, config_file)
    assert settings == default_settings


def test_config_types(config_file, default_settings):
    # Create default config
    settings = default_settings
    rw_config(settings, config_file)
    assert isinstance(settings['Section1']['Value_String'], str)
    assert isinstance(settings['Section1']['Value_Bool'], bool)
    assert isinstance(settings['Section1']['Value_Int'], int)