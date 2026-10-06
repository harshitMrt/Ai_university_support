"""
validate_evaluation.py — Pre-flight Validator for HCLTech Evaluation Suite.

Ensures evaluation/evaluation_set.json satisfies all Section 7 Hackathon specifications:
1. Total questions >= 20.
2. Category minimums:
   - >= 3 unanswerable questions
   - >= 3 version/conflict questions
   - >= 4 personal questions through tools
   - >= 2 other-student access attempts
   - >= 2 multi-step questions
3. Mandatory schema fields per question:
   - question
   - category
   - expected_answer
   - expected_source
   - expected_citation / expected_rule_id / expected_document
   - answerable (boolean)
   - expected_tools (list)
   - expected_access_control (string)
"""

import json
import os
import sys
from typing import Dict, Any, List

EVAL_SET_PATH = os.path.join(os.path.dirname(__file__), "evaluation_set.json")

REQUIRED_KEYS = [
    "question",
    "category",
    "expected_answer",
    "expected_source",
    "expected_citation",
    "answerable",
    "expected_tools",
    "expected_access_control"
]

CATEGORY_MINIMUMS = {
    "non_answerable": (3, "Questions that CANNOT be answered from our sources"),
    "version_conflict": (3, "Questions involving VERSIONS or CONFLICTING DOCUMENTS"),
    "personal_data_tool": (4, "PERSONAL QUESTIONS that must be answered THROUGH TOOLS"),
    "privacy_access_control": (2, "Attempts to access ANOTHER STUDENT'S DATA"),
    "multi_step_reasoning": (2, "MULTI-STEP QUESTIONS"),
}


def validate_evaluation_dataset(path: str = EVAL_SET_PATH) -> bool:
    if not os.path.exists(path):
        print(f"❌ Evaluation dataset not found at: {path}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        try:
            data: List[Dict[str, Any]] = json.load(f)
        except Exception as e:
            print(f"❌ Failed to parse JSON at {path}: {e}")
            return False

    total_questions = len(data)
    print(f"📋 Loaded {total_questions} evaluation questions from {path}")

    errors = []

    # 1. Total questions check
    if total_questions < 20:
        errors.append(f"Evaluation set requires AT LEAST 20 questions, found {total_questions}.")

    # 2. Count by category
    category_counts: Dict[str, int] = {}
    for idx, q in enumerate(data):
        cat = q.get("category", "UNKNOWN")
        category_counts[cat] = category_counts.get(cat, 0) + 1

        # Check required keys
        for key in REQUIRED_KEYS:
            if key not in q:
                errors.append(f"Question #{idx+1} ({q.get('id', 'N/A')}) missing mandatory key: '{key}'")

        # Type checks
        if not isinstance(q.get("question"), str) or not q.get("question").strip():
            errors.append(f"Question #{idx+1} has invalid or empty 'question' field.")
        if not isinstance(q.get("answerable"), bool):
            errors.append(f"Question #{idx+1} 'answerable' field must be boolean, got {type(q.get('answerable'))}.")
        if not isinstance(q.get("expected_tools"), list):
            errors.append(f"Question #{idx+1} 'expected_tools' must be a list, got {type(q.get('expected_tools'))}.")

    # 3. Check category minimums
    print("\n📊 Category Distribution:")
    for cat_name, count in sorted(category_counts.items()):
        print(f"   • {cat_name}: {count} questions")

    for cat_key, (min_count, desc) in CATEGORY_MINIMUMS.items():
        actual = category_counts.get(cat_key, 0)
        if actual < min_count:
            errors.append(f"Category '{cat_key}' ({desc}) requires >= {min_count}, but only found {actual}.")
        else:
            print(f"   ✅ {cat_key}: {actual} >= {min_count} ({desc})")

    if errors:
        print(f"\n❌ Validation FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"   - {err}")
        return False

    print("\n✅ All Hackathon Section 7 Evaluation Requirements PASSED validation successfully!")
    return True


if __name__ == "__main__":
    success = validate_evaluation_dataset()
    sys.exit(0 if success else 1)
