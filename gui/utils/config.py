import yaml
from typing import Dict, Any


def import_config() -> Dict[str, Any]:
    with open('mixer_settings.yaml') as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def export_config(config: Dict[str, Any]) -> None:
    with open('mixer_settings.yaml', 'w') as f:
        yaml.dump(config, f)
