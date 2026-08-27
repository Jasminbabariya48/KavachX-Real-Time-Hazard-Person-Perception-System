"""Configuration Loader."""
import os
import json

def load_config(config_path: str = None) -> dict:
    if config_path is None:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        config_path = os.path.join(root, "config/production.json")
        if not os.path.exists(config_path):
            config_path = os.path.join(root, "config/production_config.json")
    with open(config_path, "r") as f:
        return json.load(f)
