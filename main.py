from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

import os
import yaml

app = FastAPI()

# -------------------------------------------------
# CORS
# -------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-m9xwro.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Load .env
# -------------------------------------------------

load_dotenv()

# -------------------------------------------------
# Default Config
# -------------------------------------------------

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


# -------------------------------------------------
# YAML Layer
# -------------------------------------------------

def load_yaml_layer():
    try:
        with open("config.development.yaml", "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


# -------------------------------------------------
# .env Layer
# -------------------------------------------------

def load_dotenv_layer():
    config = {}

    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, config_key in mapping.items():
        value = os.getenv(env_key)
        if value is not None:
            config[config_key] = value

    # Special Alias
    alias = os.getenv("NUM_WORKERS")
    if alias is not None:
        config["workers"] = alias

    return config


# -------------------------------------------------
# OS Environment Layer
# -------------------------------------------------

def load_os_layer():
    config = {}

    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for key, value in os.environ.items():
        if key in mapping:
            config[mapping[key]] = value

    return config


# -------------------------------------------------
# Type Conversion
# -------------------------------------------------

def convert_value(key, value):

    if key in ["port", "workers"]:
        return int(value)

    if key == "debug":
        return str(value).lower() in [
            "true",
            "1",
            "yes",
            "on",
        ]

    return str(value)


# -------------------------------------------------
# Endpoint
# -------------------------------------------------

@app.get("/effective-config")
def effective_config(
    set: list[str] | None = Query(default=None)
):

    config = DEFAULTS.copy()

    # YAML
    yaml_layer = load_yaml_layer()
    for k, v in yaml_layer.items():
        config[k] = convert_value(k, v)

    # .env
    dotenv_layer = load_dotenv_layer()
    for k, v in dotenv_layer.items():
        config[k] = convert_value(k, v)

    # OS Environment
    os_layer = load_os_layer()
    for k, v in os_layer.items():
        config[k] = convert_value(k, v)

    # CLI Overrides
    if set:
        for item in set:
            if "=" in item:
                key, value = item.split("=", 1)
                config[key] = convert_value(key, value)

    # Mask Secret
    config["api_key"] = "****"

    return config