import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

_config: dict | None = None


def _load_config() -> dict:
    global _config
    if _config is None:
        config_path = Path(__file__).parent / "models.json"
        with open(config_path) as f:
            _config = json.load(f)
    return _config


def get_llm(agent_name: str):
    config = _load_config()
    agent_config = config[agent_name]

    api_key = os.getenv(agent_config["api_key_env"])
    if not api_key:
        raise ValueError(
            f"Missing API key env var: {agent_config['api_key_env']}"
        )

    return init_chat_model(
        model=agent_config["model"],
        model_provider=agent_config["provider"],
        base_url=agent_config["base_url"],
        api_key=api_key,
        temperature=agent_config["temperature"],
        max_tokens=agent_config.get("max_tokens"),
    )
