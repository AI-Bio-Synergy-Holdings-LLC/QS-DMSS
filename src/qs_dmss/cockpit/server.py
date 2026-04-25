from __future__ import annotations

from pathlib import Path

import uvicorn

from qs_dmss.cockpit.api import create_app


def run_cockpit_server(
    host: str = "127.0.0.1",
    port: int = 8001,
    output_root: str | Path | None = None,
) -> int:
    app = create_app(output_root=output_root)
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0
