"""Interactive API documentation, independent of services and persistence."""
from pathlib import Path

from flask import Blueprint, render_template, send_file

bp = Blueprint("docs", __name__)
SPEC_PATH = Path(__file__).with_name("openapi.json")


@bp.get("/docs")
def swagger_ui():
    return render_template("swagger.html")


@bp.get("/openapi.json")
def openapi_spec():
    return send_file(SPEC_PATH, mimetype="application/json")
