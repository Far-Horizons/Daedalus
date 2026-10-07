import pytest
from ProteusConfig import ProteusConfig


# --- enforce_consistency ---

def test_common_words_above_max_raises():
    with pytest.raises(ValueError):
        config = ProteusConfig(known_path="unused", max_common_words=600, max_permutation_words=500)
        config.enforce_consistency()


def test_common_words_equal_to_max_is_allowed():
    config = ProteusConfig(known_path="unused", max_common_words=500, max_permutation_words=500)
    config.enforce_consistency()
    assert config.max_common_words == 500


def test_common_words_below_max_is_kept():
    config = ProteusConfig(known_path="unused", max_common_words=100, max_permutation_words=500)
    config.enforce_consistency()
    assert config.max_common_words == 100


def test_unset_common_words_is_capped_at_max():
    config = ProteusConfig(known_path="unused", max_common_words=None, max_permutation_words=500)
    config.enforce_consistency()
    assert config.max_common_words == 500


def test_no_limits_stays_unlimited():
    config = ProteusConfig(known_path="unused", max_common_words=None, max_permutation_words=None)
    config.enforce_consistency()
    assert config.max_common_words is None


def test_common_limit_without_max_is_kept():
    config = ProteusConfig(known_path="unused", max_common_words=100, max_permutation_words=None)
    config.enforce_consistency()
    assert config.max_common_words == 100
