import json
from pathlib import Path

DATA_DIR = Path("data")

for file_path in sorted(DATA_DIR.glob("*.json")):
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    print(f"\n=== {file_path.name} ===")
    print(f"Type: {type(data).__name__}")

    if isinstance(data, dict):
        print(f"Top-level keys: {list(data.keys())}")
        print(f"Records/keys: {len(data)}")

    elif isinstance(data, list):
        print(f"Records: {len(data)}")

        if data:
            first_record = data[0]
            if isinstance(first_record, dict):
                print(f"Record fields: {list(first_record.keys())}")