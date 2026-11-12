"""Score the classifier against the saved eval set: how many did it get right?"""
import json
import sys

from app.nodes import BATCH_SIZE, classify_batch

sys.stdout.reconfigure(encoding="utf-8")
EVAL_FILE = "evals/eval_set.json"


def main():
    with open(EVAL_FILE, encoding="utf-8") as f:
        cases = json.load(f)
    cases = [c for c in cases if c["expected"]]  # skip rows without a right answer yet

    predictions = []
    for i in range(0, len(cases), BATCH_SIZE):
        predictions += classify_batch(cases[i : i + BATCH_SIZE])  # same code path as the real run

    correct = 0
    for case, got in zip(cases, predictions):
        ok = got == case["expected"]
        correct += ok
        mark = "PASS" if ok else "FAIL"
        print(f"{mark}  expected={case['expected']:<12} got={got:<12} {case['subject'][:50]}")

    print("-" * 60)
    print(f"Score: {correct}/{len(cases)} = {correct / len(cases):.0%}")  # the number you track over time


if __name__ == "__main__":
    main()
