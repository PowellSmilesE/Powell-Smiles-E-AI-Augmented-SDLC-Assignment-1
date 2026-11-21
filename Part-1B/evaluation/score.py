"""Independent outcome scoring; never imports the production review service.
The labels are source-specific, frozen BEFORE final live evaluation.
"""

from __future__ import annotations

from typing import Any

WEIGHTS = {"finding_f1": 0.40, "severity": 0.25, "localization": 0.20, "remediation": 0.15}


def score_case(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    truths = expected["findings"]
    preds = actual.get("findings", [])
    if not isinstance(preds, list):
        raise ValueError("Invalid findings")
    # Match findings by type with one-to-one accounting: duplicate findings penalized.
    remaining = list(preds)
    pairs = []
    for truth in truths:
        options = [
            (i, item)
            for i, item in enumerate(remaining)
            if item.get("category") == truth["category"]
        ]
        if options:
            idx, predicted = min(
                options, key=lambda x: abs(x[1].get("start_line", -999) - truth["start_line"])
            )
            pairs.append((truth, predicted))
            remaining.pop(idx)
    tp = len(pairs)
    f1 = (
        1.0
        if not truths and not preds
        else (2 * tp / (len(truths) + len(preds)) if truths or preds else 1.0)
    )
    if not truths:
        severity = localization = remediation = 1.0 if not preds else 0.0
    else:
        severity = sum(t["severity"] == a.get("severity") for t, a in pairs) / len(truths)
        localization = sum(
            t["start_line"] == a.get("start_line") and t["end_line"] == a.get("end_line")
            for t, a in pairs
        ) / len(truths)
        remediation = sum(
            len(a.get("explanation", "").strip()) >= 25
            and len(a.get("remediation", "").strip()) >= 25
            and any(term in a["remediation"].lower() for term in t["remediation_terms"])
            for t, a in pairs
        ) / len(truths)
    components = {
        "finding_f1": f1,
        "severity": severity,
        "localization": localization,
        "remediation": remediation,
    }
    score = sum(components[key] * weight for key, weight in WEIGHTS.items())
    # designated critical case recall measures all expected findings in that case,
    # not only severity=Critical; full recall must be shown in every critical-tagged case.
    return {
        "score": score,
        "components": components,
        "found": tp,
        "expected": len(truths),
        "predicted": len(preds),
        "critical_recall": 1.0 if not truths else tp / len(truths),
    }
