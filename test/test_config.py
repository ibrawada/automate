from mate import config
from pathlib import Path
from configparser import ConfigParser

TEST_DIR = Path(__file__).parent
TEST_CONFIGS = TEST_DIR / "test_config"

def test_configparser_to_dict():
    cfg = ConfigParser()
    cfg.read_dict(config.DEFAULT_GLOBAL_CONFIG_CONTENT)

    config_dict = config.configparser_to_dict(cfg)

    assert config_dict == config.DEFAULT_GLOBAL_CONFIG_CONTENT



def test_load_config():
    print(f"TEST_DIR: {TEST_DIR}")
    global_config = config.configparser_to_dict(config.load_config(str(TEST_CONFIGS / "test-mate-global.conf")))
    local_config = config.configparser_to_dict(config.load_config(str(TEST_CONFIGS / "test-mate-local.conf")))

    assert global_config == config.DEFAULT_GLOBAL_CONFIG_CONTENT
    assert local_config == config.DEFAULT_LOCAL_CONFIG_CONTENT