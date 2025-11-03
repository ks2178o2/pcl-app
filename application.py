"""
Elastic Beanstalk WSGI entrypoint.

This wrapper exposes the FastAPI app as a module-level variable named
`application`, which EB expects when a Procfile is not used or for health
checks. It adjusts sys.path so we can import the app from apps/app-api.
"""

import os
import sys

# Add the FastAPI service directory to Python path
BASE_DIR = os.path.dirname(__file__)
SERVICE_DIR = os.path.join(BASE_DIR, "apps", "app-api")
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

# Import the FastAPI app and expose it as `application`
try:
    from main import app as application  # type: ignore
except Exception as exc:  # pragma: no cover
    # Provide a minimal fallback app so EB health checks don't crash with 500
    from fastapi import FastAPI

    fallback = FastAPI()

    @fallback.get("/health")
    def health():  # noqa: D401
        return {"status": "ok", "detail": str(exc)}

    application = fallback


