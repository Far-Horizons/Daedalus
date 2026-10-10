import json
import pytest
import ProteusConfig as config_module
from ProteusConfig import ProteusConfig


# --- enforce_consistency (runs automatically through __post_init__) ---
# These tests only build the config and never call enforce_consistency() themselves,
# so they also fail if __post_init__ stops calling it.

def test_common_words_above_max_raises():
    with pytest.raises(ValueError):
        ProteusConfig(known_path="unused", max_common_words=600, max_permutation_words=500)


def test_common_words_equal_to_max_is_allowed():
    config = ProteusConfig(known_path="unused", max_common_words=500, max_permutation_words=500)
    assert config.max_common_words == 500


def test_common_words_below_max_is_kept():
    config = ProteusConfig(known_path="unused", max_common_words=100, max_permutation_words=500)
    assert config.max_common_words == 100


def test_unset_common_words_is_capped_at_max():
    config = ProteusConfig(known_path="unused", max_common_words=None, max_permutation_words=500)
    assert config.max_common_words == 500


def test_no_limits_stays_unlimited():
    config = ProteusConfig(known_path="unused", max_common_words=None, max_permutation_words=None)
    assert config.max_common_words is None


def test_common_limit_without_max_is_kept():
    config = ProteusConfig(known_path="unused", max_common_words=100, max_permutation_words=None)
    assert config.max_common_words == 100


def test_max_of_zero_caps_common_words_at_zero():
    # 0 is a real limit, not "no limit"; a truthiness check (if max_permutation_words:) would get this wrong
    config = ProteusConfig(known_path="unused", max_permutation_words=0)
    assert config.max_common_words == 0


# --- configure_depth (deep_all and the deep_* overrides) ---

def test_deep_all_on_by_default():
    config = ProteusConfig(known_path="unused")
    assert (config.deep_hyphenate, config.deep_concat, config.deep_add_numbers) == (True, True, True)


def test_deep_all_off_turns_every_depth_off():
    config = ProteusConfig(known_path="unused", deep_all=False)
    assert (config.deep_hyphenate, config.deep_concat, config.deep_add_numbers) == (False, False, False)


def test_override_on_while_deep_all_off():
    config = ProteusConfig(known_path="unused", deep_all=False, deep_hyphenate=True)
    assert (config.deep_hyphenate, config.deep_concat, config.deep_add_numbers) == (True, False, False)


def test_override_off_while_deep_all_on():
    config = ProteusConfig(known_path="unused", deep_all=True, deep_concat=False)
    assert (config.deep_hyphenate, config.deep_concat, config.deep_add_numbers) == (True, False, True)


# --- from_json ---

def write_json(tmp_path, data):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data))
    return path


def test_json_overrides_defaults(tmp_path):
    path = write_json(tmp_path, {"max_permutation_words": 10, "common_word_priority": False})
    config = ProteusConfig.from_json("known.txt", path)
    assert config.max_permutation_words == 10
    assert config.common_word_priority is False


def test_json_leaves_unlisted_settings_at_default(tmp_path):
    path = write_json(tmp_path, {"max_permutation_words": 10})
    config = ProteusConfig.from_json("known.txt", path)
    assert config.min_word_occurrence is None
    assert config.enable_prepend is True


def test_json_config_goes_through_post_init(tmp_path):
    # values from JSON must get the same consistency check and depth resolution as values passed directly
    path = write_json(tmp_path, {"max_permutation_words": 10, "deep_all": False})
    config = ProteusConfig.from_json("known.txt", path)
    assert config.max_common_words == 10
    assert config.deep_hyphenate is False


def test_json_inconsistent_values_raise(tmp_path):
    path = write_json(tmp_path, {"max_common_words": 600, "max_permutation_words": 500})
    with pytest.raises(ValueError):
        ProteusConfig.from_json("known.txt", path)


def test_json_unknown_setting_raises(tmp_path):
    # a typo in the JSON (like the old "min_word_occurence") must fail loudly, not be silently ignored
    path = write_json(tmp_path, {"min_word_occurence": 2})
    with pytest.raises(TypeError):
        ProteusConfig.from_json("known.txt", path)


def test_json_sets_known_path(tmp_path):
    path = write_json(tmp_path, {})
    config = ProteusConfig.from_json("known.txt", path)
    assert config.known_path == "known.txt"


def test_missing_explicit_json_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ProteusConfig.from_json("known.txt", tmp_path / "does_not_exist.json")


def test_missing_default_json_falls_back_to_defaults(tmp_path, monkeypatch):
    # point the default config path at a file that doesn't exist, so the real proteus_config.json can't affect this test
    monkeypatch.setattr(config_module, "PROTEUS_CONFIG", tmp_path / "does_not_exist.json")
    config = ProteusConfig.from_json("known.txt")
    assert config.max_permutation_words == 500


def test_default_json_is_used_when_no_path_given(tmp_path, monkeypatch):
    path = write_json(tmp_path, {"max_permutation_words": 10})
    monkeypatch.setattr(config_module, "PROTEUS_CONFIG", path)
    config = ProteusConfig.from_json("known.txt")
    assert config.max_permutation_words == 10
