# Items API

A small Flask app with two endpoints:

- `GET /items` — list all items.
- `GET /items/<id>` — get a single item by integer ID.

Items have an `id`, `name`, and `category`. The data lives in `db.py` as an
in-memory list; `models.py` defines the `Item` dataclass.
