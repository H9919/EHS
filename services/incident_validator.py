from typing import Dict, Tuple, List

# Required category coverage by incident type
REQUIRED_BY_TYPE = {
    "injury":        ["people", "legal"],
    "vehicle":       ["people", "cost", "legal", "reputation"],
    "security":      ["legal", "reputation", "cost"],
    "environmental": ["environment", "legal", "reputation"],
    "depot":         ["people", "cost", "legal", "reputation"],
    "near_miss":     ["people", "environment"],
    "property":      ["cost", "legal"],
    "other":         ["people", "environment", "cost", "legal", "reputation"],
}

ALL_CATS = ["people", "environment", "cost", "legal", "reputation"]

def compute_completeness(rec: Dict) -> int:
    answers = rec.get("answers", {})
    filled = sum(1 for c in ALL_CATS if (answers.get(c) or "").strip())
    return int(100 * filled / len(ALL_CATS))

def validate_record(rec: Dict) -> Tuple[bool, List[str]]:
    itype = (rec.get("type") or "other").lower().replace(" ", "_")
    required = REQUIRED_BY_TYPE.get(itype, REQUIRED_BY_TYPE["other"])
    answers = rec.get("answers", {})
    missing = [c for c in required if not (answers.get(c) or "").strip()]
    return (len(missing) == 0, missing)

