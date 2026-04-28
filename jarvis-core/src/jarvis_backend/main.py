from __future__ import annotations

import argparse

import uvicorn

from jarvis_backend.config import load_settings
from jarvis_backend.server.app import build_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    settings = load_settings(args.config)
    app = build_app(settings)
    uvicorn.run(app, host=settings.server.host, port=settings.server.port)


if __name__ == "__main__":
    main()
