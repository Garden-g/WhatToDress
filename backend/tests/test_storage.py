from __future__ import annotations

from backend.storage.json_store import JsonListStore


def test_json_list_store_upsert_and_delete(tmp_path):
    store = JsonListStore(tmp_path / "wardrobe.json")

    store.upsert({"item_id": "a-1", "name": "白 T"}, "item_id")
    store.upsert({"item_id": "a-1", "name": "白 T 恤"}, "item_id")

    records = store.list_all()
    assert len(records) == 1
    assert records[0]["name"] == "白 T 恤"

    deleted = store.delete("a-1", "item_id")
    assert deleted is True
    assert store.list_all() == []

