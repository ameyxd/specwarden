from flask import Flask, jsonify

app = Flask(__name__)

ITEMS = {"1": "alpha", "2": "beta"}


@app.route("/items")
def list_items():
    return jsonify(ITEMS)


@app.route("/items/<item_id>")
def get_item(item_id: str):
    if item_id not in ITEMS:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": item_id, "value": ITEMS[item_id]})


if __name__ == "__main__":
    app.run(debug=True)
