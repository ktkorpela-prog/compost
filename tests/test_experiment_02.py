"""Synthetic fixture tests for Experiment 02 structural induction.

These are the correctness oracle required by EXPERIMENT_02.md §3.3. Expected
skeletons and counts are written here, deterministically, and failure blocks
further work. HC3 is not an oracle: nobody knows its true frame inventory.
"""

from compost.canonical import (
    AMBIGUOUS_CONTRACTIONS,
    NEGATIVE_CONTRACTIONS,
    anchors_sha256,
    load_anchors,
    skeletonise,
    structural_tokens,
)
from compost.echo import build_echo_sets, partition_lexical, partition_structural
from compost.extractor import extract_ngrams
from compost.induction import (
    CROSS_SENTENCE,
    WITHIN_SENTENCE,
    Skeleton,
    group_by_exposure,
    induce_pair,
    induce_single,
    scan_texts,
)

ANCHORS = load_anchors()


# --- anchor set integrity -------------------------------------------------

def test_anchor_set_is_exactly_117():
    assert len(ANCHORS) == 117


def test_anchor_set_hash_is_recordable():
    digest = anchors_sha256()
    assert len(digest) == 64 and int(digest, 16) >= 0


def test_inherited_and_extension_terms_present():
    for term in ("the", "not", "but", "is"):            # inherited
        assert term in ANCHORS
    for term in ("isn't", "whether", "instead", "toward"):  # project-defined
        assert term in ANCHORS
    assert "such" not in ANCHORS  # deliberately absent; not tuned to Experiment 01


# --- four known structural frames (recovery test) -------------------------

def test_recovers_not_but_frame():
    found = induce_single("It is not a bug but a feature.", ANCHORS)
    assert found[Skeleton(WITHIN_SENTENCE, "not a <X> but a <X>")] == 1


def test_recovers_not_only_but_also_frame():
    found = induce_single("It is not only fast but also cheap.", ANCHORS)
    assert found[Skeleton(WITHIN_SENTENCE, "not only <X> but also <X>")] == 1


def test_recovers_isnt_its_frame_across_sentences():
    first = "The real question isn't whether AI will replace us."
    second = "It's what happens when it does."
    found = induce_pair(first, second, ANCHORS)
    crossing = [s.text for s in found if "not" in s.text and "it's" in s.text]
    assert crossing, "no cross-sentence skeleton spans the reframe"
    assert all(s.exposure == CROSS_SENTENCE for s in found)


def test_recovers_isnt_about_its_about_frame():
    found = induce_pair("This isn't about speed.", "It's about control.", ANCHORS)
    assert found[Skeleton(CROSS_SENTENCE, "about <X> . it's about")] == 1


# --- contracted vs expanded equivalence -----------------------------------

def test_contracted_and_expanded_skeletons_are_identical():
    assert skeletonise("It isn't broken.", ANCHORS) == skeletonise("It is not broken.", ANCHORS)


def test_every_unambiguous_negative_contraction_canonicalises():
    for contraction, (first, second) in NEGATIVE_CONTRACTIONS.items():
        expanded = f"{first} {second}"
        assert skeletonise(f"They {contraction} ready.", ANCHORS) == \
               skeletonise(f"They {expanded} ready.", ANCHORS), contraction


def test_contracted_and_expanded_occurrences_aggregate_not_split():
    stats = scan_texts("agg", ["It isn't broken.", "It is not broken."], ANCHORS)
    target = Skeleton(WITHIN_SENTENCE, "it is not <X>")
    assert stats.occurrences[target] == 2
    assert stats.documents_with[target] == 2


def test_cannot_is_not_produced_by_canonicalisation():
    """can't -> can not, two tokens. `cannot` is not an anchor and would slot."""
    assert skeletonise("They can't wait.", ANCHORS) == skeletonise("They can not wait.", ANCHORS)
    assert "cannot" not in skeletonise("They can't wait.", ANCHORS)


# --- ambiguous-contraction non-equivalence --------------------------------

def test_ambiguous_contractions_are_not_unified():
    assert skeletonise("It's broken.", ANCHORS) != skeletonise("It is broken.", ANCHORS)
    assert skeletonise("That's settled.", ANCHORS) != skeletonise("That is settled.", ANCHORS)


def test_ambiguous_contractions_survive_as_anchors():
    for token in AMBIGUOUS_CONTRACTIONS:
        assert token in ANCHORS
        assert token in skeletonise(f"{token} a problem.", ANCHORS)


# --- slot collapse --------------------------------------------------------

def test_consecutive_content_words_collapse_to_one_slot():
    long_form = skeletonise("The very large red ball is not round.", ANCHORS)
    short_form = skeletonise("The ball is not round.", ANCHORS)
    assert long_form == short_form == ["the", "<X>", "is", "not", "<X>", "."]


def test_slot_collapse_makes_frames_length_invariant():
    a = induce_single("It is not a bug but a feature.", ANCHORS)
    b = induce_single("It is not a catastrophic regression but a deliberate feature.", ANCHORS)
    target = Skeleton(WITHIN_SENTENCE, "not a <X> but a <X>")
    assert a[target] == b[target] == 1


# --- numerals -------------------------------------------------------------

def test_numerals_become_num_slot():
    assert skeletonise("It was 2 of the 3.", ANCHORS) == \
           ["it", "was", "<NUM>", "of", "the", "<NUM>", "."]


def test_numeral_frame_is_induced_without_literal_digits():
    found = induce_single("It was 2 of the 3.", ANCHORS)
    assert found[Skeleton(WITHIN_SENTENCE, "was <NUM> of the")] == 1
    assert all("2" not in s.text and "3" not in s.text for s in found)


def test_recipe_quantities_do_not_become_lexical_skeletons():
    """`1 cup` and `ingredients 1` were Experiment 01 genre artifacts."""
    assert "1" not in skeletonise("Add 1 cup of flour.", ANCHORS)


# --- negative controls ----------------------------------------------------

def test_all_content_sentence_induces_nothing():
    assert induce_single("Quantum entanglement fascinates researchers.", ANCHORS) == {}


def test_single_anchor_sentence_induces_nothing():
    """Fewer than two anchors cannot qualify, whatever the slot count."""
    assert induce_single("Researchers publish papers and conference abstracts.", ANCHORS) == {}


def test_no_slot_means_no_frame():
    found = induce_single("It is what it is.", ANCHORS)
    assert found == {}


# --- lexical non-interference ---------------------------------------------

def test_lexical_extraction_still_sees_original_surface_forms():
    grams = extract_ngrams("The question isn't speed.")
    texts = {p.text for p in grams}
    assert "isn't speed" in texts
    assert "is not speed" not in texts


def test_canonicalisation_does_not_leak_into_lexical_tokens():
    assert "isn't" in structural_tokens("It isn't broken.")
    grams = {p.text for p in extract_ngrams("It isn't broken.")}
    assert any("isn't" in t for t in grams)


# --- no cross-paragraph adjacency ----------------------------------------

def test_paragraph_break_blocks_cross_sentence_frame():
    joined = "This isn't about speed. It's about control."
    split = "This isn't about speed.\n\nIt's about control."
    target = Skeleton(CROSS_SENTENCE, "about <X> . it's about")
    assert scan_texts("joined", [joined], ANCHORS).occurrences[target] == 1
    assert scan_texts("split", [split], ANCHORS).occurrences[target] == 0


def test_non_adjacent_sentences_never_combine():
    text = ("The real question isn't whether AI will replace us. "
            "Adoption timelines vary by sector. "
            "It's what happens when it does.")
    stats = scan_texts("gap", [text], ANCHORS)
    crossing = [s for s in stats.occurrences if s.exposure == CROSS_SENTENCE
                and "not" in s.text and "it's" in s.text]
    assert crossing == []


# --- exposure denominators ------------------------------------------------

def test_exposure_families_tracked_separately():
    stats = scan_texts("exposure", ["One sentence. Two sentence. Three sentence."], ANCHORS)
    assert stats.exposure.documents == 1
    assert stats.exposure.paragraphs == 1
    assert stats.exposure.sentences == 3
    assert stats.exposure.adjacent_pairs == 2


def test_pair_exposure_is_sentences_minus_paragraphs():
    text = "A one. A two.\n\nB one. B two. B three."
    stats = scan_texts("p", [text], ANCHORS)
    assert stats.exposure.paragraphs == 2
    assert stats.exposure.sentences == 5
    assert stats.exposure.adjacent_pairs == stats.exposure.sentences - stats.exposure.paragraphs


def test_rate_uses_the_matching_denominator():
    stats = scan_texts("rate", ["It is not a bug but a feature. It's fine."], ANCHORS)
    within = Skeleton(WITHIN_SENTENCE, "not a <X> but a <X>")
    assert stats.exposure.sentences == 2 and stats.exposure.adjacent_pairs == 1
    assert stats.rate_per_10k(within) == stats.occurrences[within] / 2 * 10_000


def test_exposure_families_are_not_pooled():
    stats = scan_texts("g", ["This isn't about speed. It's about control."], ANCHORS)
    grouped = group_by_exposure(stats.occurrences)
    assert set(grouped) == {WITHIN_SENTENCE, CROSS_SENTENCE}
    assert all(s.exposure == WITHIN_SENTENCE for s in grouped[WITHIN_SENTENCE])
    assert all(s.exposure == CROSS_SENTENCE for s in grouped[CROSS_SENTENCE])


# --- prompt/title echo ----------------------------------------------------

def test_lexical_echo_detected_from_prompt():
    echo = build_echo_sets("Write a news article titled Bees", "Bees", ANCHORS)
    assert partition_lexical("news article", 3, echo).echoing == 3
    assert partition_lexical("unrelated phrase", 3, echo).echoing == 0


def test_structural_echo_catches_what_lexical_misses():
    """Different words, same skeleton — invisible to n-gram echo detection.

    The prompt and the generation share no 2-5-gram, so lexical echo detection
    cannot see the reuse. They collapse to the same skeleton, so structural echo
    detection can. This is the case §4 exists for.
    """
    echo = build_echo_sets("It is not about speed but about control.", "", ANCHORS)

    shared_skeleton = "not about <X> but about"
    assert echo.contains_structural(shared_skeleton), "structural echo missed the shared frame"
    assert partition_structural(shared_skeleton, 2, echo).echoing == 2

    # The generation rewords every content slot; no lexical n-gram survives.
    for gram in ("about cost but", "not about cost", "but about value"):
        assert partition_lexical(gram, 1, echo).echoing == 0, gram


def test_echo_counts_retain_full_and_primary():
    echo = build_echo_sets("a news article", "", ANCHORS)
    counts = partition_lexical("news article", 4, echo)
    assert counts.total == 4 and counts.primary == 0 and counts.echo_fraction == 1.0
    assert counts.prompt_derived is True


def test_non_echo_pattern_is_untouched():
    echo = build_echo_sets("a news article", "", ANCHORS)
    counts = partition_lexical("not a <X> but", 4, echo)
    assert counts.total == 4 and counts.primary == 4 and counts.prompt_derived is False


def test_structural_echo_partition_uses_skeleton_membership():
    echo = build_echo_sets("It is not a bug but a feature.", "", ANCHORS)
    counts = partition_structural("not a <X> but a <X>", 2, echo)
    assert counts.echoing == 2 and counts.primary == 0


# --- power-gate boundary behaviour ----------------------------------------
# Regression cover for a specification defect found in Phase 1: the §8 gate asks
# for >=80% power at lift 1.5 while §6 qualifies cells at lift >= 1.5. A true
# effect sitting exactly on the decision boundary passes ~50% of the time per
# cell however large N grows, so the gate is unreachable by construction rather
# than by sample size.

import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path

_spec = _ilu.spec_from_file_location(
    "sim_for_tests", _Path(__file__).resolve().parent.parent / "scripts" / "simulate_power.py"
)
_sim = _ilu.module_from_spec(_spec)
_sys.modules["sim_for_tests"] = _sim
_spec.loader.exec_module(_sim)

_PARAMS = _sim.ClusterParams(
    base_rate_per_unit=0.0132, exposure_per_doc=15.0,
    source_dispersion=1.476, model_dispersion=0.026,
    provenance="fixture values approximating the Phase 1 calibration measurement",
)


def test_power_at_the_threshold_does_not_improve_with_n():
    """Doubling N cannot rescue an effect sitting on the decision boundary."""
    small = _sim.power_at(_PARAMS, 200, 1.5, 30, 11)
    large = _sim.power_at(_PARAMS, 851, 1.5, 30, 11)
    assert small < 0.6 and large < 0.6
    assert abs(large - small) < 0.35, "boundary power should be flat in N, not rising"


def test_power_recovers_when_the_effect_clears_the_threshold():
    """The pipeline is not simply underpowered: lift 2.0 detects reliably."""
    assert _sim.power_at(_PARAMS, 200, 2.0, 30, 11) > 0.8


def test_stress_scenarios_produce_no_false_qualification():
    """Document-shape asymmetries alone must not manufacture a verdict."""
    for scenario in _sim.STRESS_SCENARIOS:
        rate = _sim.power_at(_PARAMS, 200, 1.0, 30, 11, scenario)
        assert rate == 0.0, scenario.name


def test_cluster_params_reject_blank_provenance():
    bad = _sim.ClusterParams(0.01, 15.0, 1.0, 0.1, "   ")
    try:
        bad.validate()
    except ValueError:
        return
    raise AssertionError("blank provenance must be rejected")


def test_n_above_the_verified_ceiling_is_refused():
    try:
        _sim.power_at(_PARAMS, _sim.MAX_N + 1, 1.5, 2, 1)
    except ValueError:
        return
    raise AssertionError(f"N above {_sim.MAX_N} must be refused")


# --- canonical-content hashing (platform independence) ---------------------
# Regression cover for Experiment 02 stop condition 3, which fired on a
# line-ending difference with identical anchor content. A raw-byte hash of a
# working-copy text file is platform-dependent under core.autocrlf; canonical
# hashing is not. See EXPERIMENT_02.md §8.5 and compost/integrity.py.

from compost.integrity import (  # noqa: E402
    canonical_json_sha256,
    canonical_text_sha256,
    canonicalise_text,
)


def test_lf_and_crlf_hash_identically():
    assert canonical_text_sha256("a\nb\nc\n") == canonical_text_sha256("a\r\nb\r\nc\r\n")


def test_classic_mac_cr_hashes_identically():
    assert canonical_text_sha256("a\nb\nc\n") == canonical_text_sha256("a\rb\rc\r")


def test_trailing_newline_handling_is_deterministic():
    base = canonical_text_sha256("a\nb\n")
    assert canonical_text_sha256("a\nb") == base
    assert canonical_text_sha256("a\nb\n\n\n") == base
    assert canonical_text_sha256("a\r\nb\r\n\r\n") == base


def test_empty_and_whitespace_only_are_stable():
    assert canonical_text_sha256("") == canonical_text_sha256("\n\n")
    assert canonicalise_text("\r\n\r\n") == b""


def test_anchor_file_hash_survives_line_ending_rewrite():
    """The exact failure that stopped the confirmatory run must not recur."""
    from compost.canonical import LEXICON_PATH
    text = LEXICON_PATH.read_text(encoding="utf-8")
    as_lf = text.replace("\r\n", "\n")
    as_crlf = as_lf.replace("\n", "\r\n")
    assert as_lf != as_crlf, "precondition: the two representations differ in bytes"
    assert canonical_text_sha256(as_lf) == canonical_text_sha256(as_crlf)
    import hashlib
    assert (hashlib.sha256(as_lf.encode()).hexdigest()
            != hashlib.sha256(as_crlf.encode()).hexdigest()), \
        "precondition: a raw-byte hash WOULD have differed"


def test_canonical_json_ignores_formatting():
    a = {"b": 1, "a": [1, 2, {"z": None, "y": True}]}
    b = {"a": [1, 2, {"y": True, "z": None}], "b": 1}
    assert canonical_json_sha256(a) == canonical_json_sha256(b)


def test_canonical_json_detects_real_content_change():
    assert canonical_json_sha256({"a": 1}) != canonical_json_sha256({"a": 2})


def test_canonical_anchor_hash_matches_committed_blob_form():
    """Canonical form equals the LF form git stores, so the two never diverge."""
    from compost.canonical import LEXICON_PATH, anchors_sha256
    lf = LEXICON_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert anchors_sha256() == canonical_text_sha256(lf)
