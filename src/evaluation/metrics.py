import re

def normalize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text.split()


def f1_score(pred, truth):
    pred_tokens = set(normalize(pred))
    truth_tokens = set(normalize(truth))

    if len(pred_tokens) == 0 or len(truth_tokens) == 0:
        return 0.0

    common = pred_tokens & truth_tokens

    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(truth_tokens)

    if precision + recall == 0:
        return 0.0

    f1 = 2 * (precision * recall) / (precision + recall)

    return precision, recall, f1