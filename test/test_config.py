from mate import config
from pathlib import Path
from configparser import ConfigParser

TEST_DIR = Path(__file__).parent
TEST_CONFIGS = TEST_DIR / "test_config"

# def test_configparser_to_dict():
#     cfg = ConfigParser()
#     cfg.read_dict(config.DEFAULT_GLOBAL_CONFIG_CONTENT)

#     config_dict = (cfg)

#     assert config_dict == config.DEFAULT_GLOBAL_CONFIG_CONTENT



def test_load_config():
    print(f"TEST_DIR: {TEST_DIR}")
    global_config = (config.load_config(str(TEST_CONFIGS / "test-mate-global.conf")))
    local_config = (config.load_config(str(TEST_CONFIGS / "test-mate-local.conf")))

    assert global_config == config.DEFAULT_GLOBAL_CONFIG_CONTENT
    assert local_config == config.DEFAULT_LOCAL_CONFIG_CONTENT



def test_append_config_value_creates_missing_section():
    config_content = {}

    result = config.append_config_value(
        config_content,
        "folders",
        "exclude",
        "build"
    )

    assert result == {
        "folders": {
            "exclude": "build"
        }
    }



def test_append_config_value_creates_option_in_existing_section():
    config_content = {
        "folders": {}
    }

    result = config.append_config_value(
        config_content,
        "folders",
        "exclude",
        "build"
    )

    assert result == {
        "folders": {
            "exclude": "build"
        }
    }



def test_append_config_value_appends_to_existing_list():
    config_content = {
        "folders": {
            "exclude": [".git", ".mate"]
        }
    }

    result = config.append_config_value(
        config_content,
        "folders",
        "exclude",
        "build"
    )

    assert result == {
        "folders": {
            "exclude": [".git", ".mate", "build"]
        }
    }


def test_append_config_value_overrides_existing_string():
    config_content = {
        "shell": {
            "windows": "cmd"
        }
    }

    result = config.append_config_value(
        config_content,
        "shell",
        "windows",
        "powershell"
    )

    assert result == {
        "shell": {
            "windows": "powershell"
        }
    }


def test_append_config_value_returns_same_dict():
    config_content = {
        "shell": {
            "windows": "cmd"
        }
    }

    result = config.append_config_value(
        config_content,
        "shell",
        "windows",
        "powershell"
    )

    assert result is config_content
