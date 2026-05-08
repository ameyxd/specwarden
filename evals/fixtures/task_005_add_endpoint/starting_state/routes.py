from flask import Flask, jsonify
from db import get_item, list_items

app = Flask(__name__)


@app.route("/items/<int:item_id>")
def show(item_id: int):
    item = get_item(item_id)
    if item is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(item)


@app.route("/items")
def index():
    return jsonify(list_items())


if __name__ == "__main__":
    app.run(debug=True)
