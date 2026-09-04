import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
RULES_FILE = ROOT_DIR / "data" / "rules.json"


def load_rules() -> dict:
    with RULES_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_rule(rule_id: str) -> dict:
    data = load_rules()

    for rule in data["rules"]:
        if rule["rule_id"] == rule_id:
            return rule

    raise ValueError(f"Unknown rule: {rule_id}")