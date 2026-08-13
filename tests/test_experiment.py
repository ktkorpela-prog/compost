from compost.extractor import (
    Pattern,
    extract_patterns,
    extract_segment_patterns,
    extract_structural,
)
from compost.normalizer import sentences
from compost.scorer import scan_texts, smoothed_lift
from compost.experiment import build_rows

REFRAME = Pattern("reframe_isnt_its", "isn't <X> it's <Y>")
NOT_BUT = Pattern("contrast_not_but", "not <X> but <Y>")

FLAGSHIP = "The real question isn't whether AI will replace us. It's what happens when it does."


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


# --- regression: structural frames across adjacent sentences ---------------


def test_cross_sentence_reframe_is_detected():
    """The flagship example spans a full stop and must still be visible."""
    segs = sentences(FLAGSHIP)
    assert len(segs) == 2, "precondition: the example is two sentences"
    assert extract_structural(segs)[REFRAME] == 1


def test_single_sentence_reframe_still_detected():
    """The within-sentence form must keep working."""
    segs = sentences("The real question isn't speed, it's who gets to decide.")
    assert len(segs) == 1
    assert extract_structural(segs)[REFRAME] == 1


def test_non_adjacent_sentences_do_not_manufacture_a_frame():
    """A frame must not be stitched together from sentences 1 and 3."""
    text = (
        "The real question isn't whether AI will replace us. "
        "Adoption timelines vary by sector. "
        "It's what happens when it does."
    )
    segs = sentences(text)
    assert len(segs) == 3, "precondition: three sentences, halves are non-adjacent"
    assert extract_structural(segs)[REFRAME] == 0


def test_overlapping_extraction_paths_count_once():
    """Seen inside one sentence and inside the pair containing it: one occurrence."""
    segs = sentences(
        "The issue is not speed, but who gets to decide. Governance is the harder problem."
    )
    assert len(segs) == 2
    assert extract_structural(segs[:1])[NOT_BUT] == 1, "precondition: visible in sentence 1 alone"
    assert extract_structural(segs)[NOT_BUT] == 1


def test_cross_sentence_frame_counts_once_against_both_sentences():
    """One structural occurrence; the denominator still records two sentences."""
    stats = scan_texts("denominator", [FLAGSHIP])
    assert stats.documents == 1
    assert stats.sentences == 2
    assert stats.occurrences[REFRAME] == 1
    assert stats.per_10k_sentences(REFRAME) == 5_000.0


def test_paragraph_boundary_blocks_adjacency():
    """The last sentence of a paragraph is not adjacent to the first of the next."""
    text = "The real question isn't whether AI will replace us.\n\nIt's what happens when it does."
    stats = scan_texts("paragraphs", [text])
    assert stats.paragraphs == 2
    assert stats.sentences == 2
    assert stats.occurrences[REFRAME] == 0


def test_whether_or_frame_is_withdrawn():
    """`whether <X> or <Y>` was removed as ordinary grammar, not rhetoric."""
    patterns = extract_patterns("We asked whether the model was ready or not.")
    assert not any(p.kind == "whether_or" for p in patterns)


def test_segment_ngrams_do_not_cross_sentence_boundaries():
    """Only structural frames span sentences; n-grams stay inside one."""
    segs = sentences("Alpha beta gamma. Delta epsilon zeta.")
    patterns = extract_segment_patterns(segs)
    assert not any(p.kind == "ngram" and "gamma delta" in p.text for p in patterns)
