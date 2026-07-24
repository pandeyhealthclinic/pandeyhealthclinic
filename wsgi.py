"""
Pandey Health Clinic — WSGI application entrypoint.

Local development:
    python wsgi.py

Production (Render, or any WSGI host):
    gunicorn wsgi:app

NOTE: this file is intentionally named `wsgi.py`, not `app.py`. This
project's package is also named `app/` (the app/ directory) — naming
this file `app.py` too creates an ambiguous "app" module name that
works fine with `python app.py` (Python resolves the import correctly
when this file is run directly as __main__) but breaks under
`gunicorn app:app`, because gunicorn imports "app" as a plain module
and resolves it to the app/ package instead of this file, then can't
find an `app` attribute inside it. Keeping this file's name distinct
from the package name avoids that collision entirely.
"""
import os
from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
