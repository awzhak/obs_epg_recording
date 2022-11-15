import yaml
from logging import config, getLogger


yaml_data = yaml.safe_load(open("logging_config.yaml").read())
config.dictConfig(yaml_data)
logger = getLogger('defaultLogger')
