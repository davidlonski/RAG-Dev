import os
import json
import time
from typing import List, Dict, Optional, Tuple

STORE_DIR = os.path.join(os.path.dirname(__file__), "homework_store")
META_FILE = os.path.join(STORE_DIR, "index.json")


def ensure_store() -> None:
    os.makedirs(STORE_DIR, exist_ok=True)
    if not os.path.exists(META_FILE):
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump({"items": []}, f)


def _load_index() -> Dict:
    ensure_store()
    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"items": []}


def _save_index(index: Dict) -> None:
    ensure_store()
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def save_homework(
    *,
    owner_id: str,
    owner_name: Optional[str],
    homework_name: str,
    excel_bytes: bytes,
) -> str:
    """Save a homework spreadsheet and metadata; returns a homework_id."""
    ensure_store()
    timestamp = int(time.time())
    homework_id = f"{timestamp}_{abs(hash((owner_id, homework_name, timestamp))) % (10**8)}"
    xlsx_path = os.path.join(STORE_DIR, f"{homework_id}.xlsx")
    meta = {
        "id": homework_id,
        "name": homework_name,
        "owner_id": owner_id,
        "owner_name": owner_name,
        "created_at": timestamp,
        "file": os.path.basename(xlsx_path),
    }

    with open(xlsx_path, "wb") as xf:
        xf.write(excel_bytes)

    index = _load_index()
    items = index.get("items", [])
    items.insert(0, meta)
    index["items"] = items
    _save_index(index)
    return homework_id


def list_homework(*, owner_id: Optional[str] = None) -> List[Dict]:
    """List homework metadata; optionally filter by owner_id."""
    index = _load_index()
    items = index.get("items", [])
    if owner_id:
        items = [it for it in items if it.get("owner_id") == owner_id]
    return items


def load_homework_file(homework_id: str) -> Optional[Tuple[bytes, Dict]]:
    """Return file bytes and metadata for a homework id."""
    index = _load_index()
    items = index.get("items", [])
    for it in items:
        if it.get("id") == homework_id:
            path = os.path.join(STORE_DIR, it.get("file", ""))
            if os.path.exists(path):
                with open(path, "rb") as xf:
                    return xf.read(), it
            return None
    return None