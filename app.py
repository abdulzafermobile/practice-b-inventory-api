import os
from flask import Flask, jsonify, abort

app = Flask(__name__)

# Set by systemd from build.env; "local" when you run it on your laptop
BUILD = os.environ.get("APP_BUILD", "local")

ITEMS = {
    1: {"id": 1, "name": "keyboard", "qty": 10},
    2: {"id": 2, "name": "monitor", "qty": 4},
    3: {"id": 3, "name": "headset", "qty": 7},
}


@app.get("/healthz")
def healthz():
    return jsonify(status="ok", build=BUILD)


@app.get("/api/items")
def list_items():
    return jsonify(list(ITEMS.values()))


@app.get("/api/items/<int:item_id>")
def get_item(item_id):
    item = ITEMS.get(item_id)
    if item is None:
        abort(404)
    return jsonify(item)


@app.get("/")
def index():
    return f"Inventory API - build {BUILD}\n"
