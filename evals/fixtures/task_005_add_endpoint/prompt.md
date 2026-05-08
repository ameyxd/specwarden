Add a new endpoint GET /items/by-category/<category> that returns all items
in the given category as a JSON array. If no items match, return an empty
array with HTTP 200 (not 404). Touch db.py and routes.py only — models.py
should not need to change.
