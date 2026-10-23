from mate import config
from pathlib import Path


TEST_DIR = Path(__file__).parent
TEST_CONFIGS = TEST_DIR / "test_config"



# def test_load_config():
#     print(f"TEST_DIR: {TEST_DIR}")
#     global_config = (config.load_config(str(TEST_CONFIGS / "test-mate-global.conf")))
#     local_config = (config.load_config(str(TEST_CONFIGS / "test-mate-local.conf")))

#     assert global_config == config.DEFAULT_GLOBAL_CONFIG_CONTENT
#     assert local_config == config.DEFAULT_LOCAL_CONFIG_CONTENT



# def test_append_config_value_creates_missing_section():
#     config_content = {}

#     result = config.append_value(
#         config_content,
#         "folders",
#         "exclude",
#         "build"
#     )

#     assert result == {
#         "folders": {
#             "exclude": "build"
#         }
#     }



def test_append_config_value_creates_option_in_existing_section():
    config_content = {
        "folders": {}
    }

    result = config.append_value(
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

    result = config.append_value(
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

    result = config.append_value(
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

    result = config.append_value(
        config_content,
        "shell",
        "windows",
        "powershell"
    )

    assert result == config_content


def test_override_single_value():
    config_content = {
        "shell": {
            "windows": "cmd"
        }
    }
    config_expected = {
        "shell": {
            "windows": "powershell"
        }
    }    

    result = config.override_value(
        config_content,
        "shell",
        "windows",
        "powershell"
    )

    assert result == config_expected


def test_override_list_str_value():
    config_content = {
        "shell": {
            "windows": ["val1", "val2"]
        }
    }
    config_expected = {
        "shell": {
            "windows": ["powershell"]
        }
    }    

    result = config.override_value(
        config_content,
        "shell",
        "windows",
        "powershell"
    )

    assert result == config_expected    


def test_override_list_list_value():
    config_content = {
        "shell": {
            "windows": ["val1", "val2"]
        }
    }
    config_expected = {
        "shell": {
            "windows": ["val3", "val4"]
        }
    }    

    result = config.override_value(
        config_content,
        "shell",
        "windows",
        ["val3", "val4"]
    )

    assert result == config_expected        



def test_remove_value_single():
    config_content = {
        "shell": {
            "windows": ["val1", "val2"]
        }
    }
    config_expected = {
        "shell": {
            "windows": ["val2"]
        }
    }    

    result = config.remove_value(
        config_content,
        "shell",
        "windows",
        "val1"
    )

    assert result == config_expected         



def test_remove_value_list():
    config_content = {
        "shell": {
            "windows": ["val1", "val2", "val3"]
        }
    }
    config_expected = {
        "shell": {
            "windows": ["val2"]
        }
    }    

    result = config.remove_value(
        config_content,
        "shell",
        "windows",
        ["val1", "val3"]
    )

    assert result == config_expected      


def test_remove_option():
    config_content = {
        "shell": {
            "windows": ["val1", "val2", "val3"],
            "linux": "something"
        }
    }
    config_expected = {
        "shell": {
            "linux": "something"
        }
    }    

    result = config.remove_value(
        config_content,
        "shell",
        "windows",
        ""
    )

    assert result == config_expected


def test_remove_section():
    config_content = {
        "others": {
            "thing": "thing"
        },
        "shell": {
            "windows": ["val1", "val2", "val3"],
            "linux": "something"
        }
    }
    config_expected = {
        "others": {
                    "thing": "thing"
        }
    }    

    result = config.remove_value(
        config_content,
        "shell",
        "",
        ""
    )

    assert result == config_expected       