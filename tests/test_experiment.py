from compost.extractor import Pattern, extract_patterns
from compost.scorer import scan_texts, smoothed_lift
from compost.experiment import build_rows


def test_structural_not_but_extraction():
    patterns = extract_patterns("The issue is not speed, but who gets to decide.")
    assert patterns[Pattern("contrast_not_but", "not <X> but <Y>")] == 1


def test_denominators_are_recorded():
    stats = scan_texts("tiny", ["One sentence. Another sentence.", "Third sentence."])
    assert stats.documents == 2
    assert stats.sentences == 3
    assert stats.tokens > 0


def test_lift_is_finite_when_reference_has_zero_occurrences():
    lift = smoothed_lift(target_occ=4, target_n=100, reference_occ=0, reference_n=100)
    assert lift > 1
    assert lift != float("inf")


def test_rows_compare_both_human_baselines():
    pre = scan_texts("pre", ["People wrote in many different ways.", "Language changes over time."])
    contemporary = scan_texts(
        "contemporary", ["Writers still choose their own framing.", "Language changes over time."]
    )
    ai = scan_texts(
        "ai",
        [
            "This is not about speed, but agency.",
            "The debate is not about tools, but ownership.",
        ],
    )
    rows = build_rows(pre, contemporary, ai, min_ai_docs=2, min_ai_occurrences=2)
    row = next(r for r in rows if r["pattern"] == "not <X> but <Y>")
    assert row["lift_vs_pre_human_smoothed"] > 1
    assert row["lift_vs_contemporary_human_smoothed"] > 1
