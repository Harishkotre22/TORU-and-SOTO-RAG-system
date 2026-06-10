import json
from src.qa import answer_question
from .metrics import f1_score


def run_evaluation():
    with open("src/evaluation/test_cases.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    results = []
    total_f1 = 0

    for case in test_cases:
        question = case["question"]
        expected = case["expected"]

        print("\n==============================")
        print("QUESTION:", question)

        generated = answer_question(question)

        precision, recall, f1 = f1_score(generated, expected)

        print("GENERATED:", generated)
        print("EXPECTED:", expected)
        print("F1:", round(f1, 3))

        results.append({
            "domain": case["domain"],
            "question": question,
            "expected": expected,
            "generated": generated,
            "precision": precision,
            "recall": recall,
            "f1": f1
        })

        total_f1 += f1

    overall_score = total_f1 / len(test_cases)

    output = {
        "overall_f1": overall_score,
        "results": results
    }

    with open("evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("\n==============================")
    print("FINAL RAG SCORE (F1):", round(overall_score, 3))