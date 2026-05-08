from dataclasses import dataclass


@dataclass
class Item:
    id: int
    name: str
    category: str

    def as_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "category": self.category}
