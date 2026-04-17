import math
import pytest
from random_resolution_picker.random_resolution_picker import (
    _parse_resolutions,
    RandomResolutionPicker,
)


# ---------------------------------------------------------------------------
# _parse_resolutions — valid input
# ---------------------------------------------------------------------------

def test_parse_basic():
    assert _parse_resolutions("1328,1328\n1664,928") == [(1328, 1328), (1664, 928)]


def test_parse_skips_blank_lines():
    assert _parse_resolutions("\n1328,1328\n\n928,1664\n") == [(1328, 1328), (928, 1664)]


def test_parse_skips_comment_lines():
    assert _parse_resolutions("# square\n1328,1328") == [(1328, 1328)]


def test_parse_strips_surrounding_whitespace():
    assert _parse_resolutions("  1328 , 1328  ") == [(1328, 1328)]


def test_parse_duplicate_lines_kept_as_weighted_entries():
    # Duplicates are intentional — they increase selection probability.
    result = _parse_resolutions("512,512\n512,512\n1024,1024")
    assert result == [(512, 512), (512, 512), (1024, 1024)]


# ---------------------------------------------------------------------------
# _parse_resolutions — invalid input
# ---------------------------------------------------------------------------

def test_parse_raises_missing_comma_includes_line_number():
    with pytest.raises(ValueError, match=r"Line 2:.*exactly one comma"):
        _parse_resolutions("# ok\n1328")


def test_parse_raises_too_many_commas_includes_line_number():
    with pytest.raises(ValueError, match=r"Line 1:.*exactly one comma"):
        _parse_resolutions("1328,928,64")


def test_parse_raises_non_integer_width_includes_line_number():
    with pytest.raises(ValueError, match=r"Line 3:.*integers"):
        _parse_resolutions("512,512\n1024,1024\nabc,512")


def test_parse_raises_non_integer_height_includes_line_number():
    with pytest.raises(ValueError, match=r"Line 1:.*integers"):
        _parse_resolutions("512,abc")


def test_parse_raises_zero_width_includes_line_number():
    with pytest.raises(ValueError, match=r"Line 2:.*positive"):
        _parse_resolutions("512,512\n0,1328")


def test_parse_raises_zero_height_includes_line_number():
    with pytest.raises(ValueError, match=r"Line 1:.*positive"):
        _parse_resolutions("512,0")


def test_parse_raises_negative_value_includes_line_number():
    with pytest.raises(ValueError, match=r"Line 1:.*positive"):
        _parse_resolutions("-512,1024")


def test_parse_raises_empty_list_all_comments():
    with pytest.raises(ValueError, match="empty"):
        _parse_resolutions("# comment only\n\n")


def test_parse_raises_empty_string():
    with pytest.raises(ValueError, match="empty"):
        _parse_resolutions("")


def test_parse_raises_whitespace_only():
    with pytest.raises(ValueError, match="empty"):
        _parse_resolutions("   \n\t\n  ")


# ---------------------------------------------------------------------------
# RandomResolutionPicker.pick — determinism and output shape
# ---------------------------------------------------------------------------

def test_pick_same_seed_returns_same_result():
    node = RandomResolutionPicker()
    r1 = node.pick("1328,1328\n1664,928", auto_randomize=False, seed=42)
    r2 = node.pick("1328,1328\n1664,928", auto_randomize=False, seed=42)
    assert r1 == r2


def test_pick_different_seeds_can_return_different_results():
    node = RandomResolutionPicker()
    # With a two-entry list, seeds 0 and 1 should diverge eventually.
    results = {
        node.pick("1328,1328\n1664,928", auto_randomize=False, seed=s)[:2]
        for s in range(20)
    }
    assert len(results) > 1, "20 different seeds all produced the same pair — suspicious"


def test_pick_result_is_always_from_the_list():
    node = RandomResolutionPicker()
    valid = {(1328, 1328), (1664, 928), (928, 1664)}
    for seed in range(50):
        w, h, label = node.pick("1328,1328\n1664,928\n928,1664", auto_randomize=False, seed=seed)
        assert (w, h) in valid
        assert label == f"{w}x{h}"


def test_pick_single_entry_always_returns_it():
    node = RandomResolutionPicker()
    for seed in range(10):
        w, h, _ = node.pick("512,768", auto_randomize=False, seed=seed)
        assert (w, h) == (512, 768)


def test_pick_label_format():
    node = RandomResolutionPicker()
    w, h, label = node.pick("1024,768", auto_randomize=False, seed=0)
    assert label == "1024x768"


# ---------------------------------------------------------------------------
# IS_CHANGED — cache invalidation contract
# ---------------------------------------------------------------------------

def test_is_changed_returns_nan_when_auto_randomize():
    result = RandomResolutionPicker.IS_CHANGED("1328,1328", auto_randomize=True, seed=0)
    assert math.isnan(result), "auto_randomize=True must return NaN to force re-execution"


def test_is_changed_returns_equal_value_for_same_inputs():
    r1 = RandomResolutionPicker.IS_CHANGED("1328,1328", auto_randomize=False, seed=5)
    r2 = RandomResolutionPicker.IS_CHANGED("1328,1328", auto_randomize=False, seed=5)
    assert r1 == r2


def test_is_changed_differs_when_seed_changes():
    r1 = RandomResolutionPicker.IS_CHANGED("1328,1328", auto_randomize=False, seed=5)
    r2 = RandomResolutionPicker.IS_CHANGED("1328,1328", auto_randomize=False, seed=6)
    assert r1 != r2


def test_is_changed_differs_when_resolutions_text_changes():
    r1 = RandomResolutionPicker.IS_CHANGED("1328,1328", auto_randomize=False, seed=5)
    r2 = RandomResolutionPicker.IS_CHANGED("1664,928", auto_randomize=False, seed=5)
    assert r1 != r2


def test_is_changed_auto_randomize_false_is_not_nan():
    result = RandomResolutionPicker.IS_CHANGED("1328,1328", auto_randomize=False, seed=0)
    assert result == ("1328,1328", 0)


# ---------------------------------------------------------------------------
# extra_pnginfo — metadata embedding
# ---------------------------------------------------------------------------

def test_pick_writes_metadata_to_extra_pnginfo():
    node = RandomResolutionPicker()
    meta = {}
    w, h, label = node.pick("512,768", auto_randomize=False, seed=0, extra_pnginfo=meta)
    assert "RandomResolutionPicker" in meta
    data = meta["RandomResolutionPicker"]
    assert data["resolution"] == label
    assert data["resolution_width"] == w
    assert data["resolution_height"] == h
    assert data["resolution_seed"] == 0


def test_pick_extra_pnginfo_none_does_not_raise():
    node = RandomResolutionPicker()
    # Must not raise even when ComfyUI passes None (no Save Image node downstream).
    node.pick("512,768", auto_randomize=False, seed=0, extra_pnginfo=None)


def test_pick_extra_pnginfo_non_dict_does_not_raise():
    node = RandomResolutionPicker()
    # ComfyUI may pass unexpected types; guard must be isinstance check, not truthiness.
    node.pick("512,768", auto_randomize=False, seed=0, extra_pnginfo="unexpected")


def test_pick_auto_randomize_true_picks_from_list_and_records_seed():
    node = RandomResolutionPicker()
    from random_resolution_picker.random_resolution_picker import MAX_SEED
    meta = {}
    w, h, label = node.pick("512,768\n1024,1024", auto_randomize=True, seed=0, extra_pnginfo=meta)
    assert (w, h) in {(512, 768), (1024, 1024)}
    assert label == f"{w}x{h}"
    assert 0 <= meta["RandomResolutionPicker"]["resolution_seed"] <= MAX_SEED
