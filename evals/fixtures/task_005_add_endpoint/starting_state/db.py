from models import Item

ITEMS = [
    Item(1, "Widget", "tools"),
    Item(2, "Sprocket", "tools"),
    Item(3, "Apple", "food"),
    Item(4, "Wrench", "tools"),
    Item(5, "Banana", "food"),
]


def get_item(item_id: int):
    for item in ITEMS:
        if item.id == item_id:
            return item.as_dict()
    return None


def list_items():
    return [item.as_dict() for item in ITEMS]
