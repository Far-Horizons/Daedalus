from collections import Counter
from ProteusConfig import ProteusConfig
from ProteusPermutator import ProteusPermutator


def make_permutator(common_words=None, harvested_words=None, max_words=None, priority=True, min_occurrence=None,
                    harvested_domains=None, enable_prepend=True):
    # known_path is required by the config, but the permutator never reads it
    config = ProteusConfig(
        known_path="unused",
        max_permutation_words=max_words,
        common_word_priority=priority,
        min_word_occurrence=min_occurrence,
        enable_prepend=enable_prepend,
    )
    return ProteusPermutator(
        config,
        harvested_domains=harvested_domains or set(),
        common_words=common_words,
        harvested_words=Counter(harvested_words) if harvested_words is not None else None,
    )


# --- Basic behaviour ---

def test_no_limit_uses_all_words():
    p = make_permutator(common_words=["www", "api"], harvested_words={"staging": 2, "dev": 1})
    p.build_wordlist()
    assert p.wordlist == {"www", "api", "staging", "dev"}


def test_no_words_gives_empty_wordlist():
    p = make_permutator(common_words=None, harvested_words=None)
    p.build_wordlist()
    assert p.wordlist == set()


def test_only_common_words():
    p = make_permutator(common_words=["www", "api"], harvested_words=None)
    p.build_wordlist()
    assert p.wordlist == {"www", "api"}


def test_only_harvested_words():
    p = make_permutator(common_words=None, harvested_words={"staging": 2, "dev": 1})
    p.build_wordlist()
    assert p.wordlist == {"staging", "dev"}


def test_word_in_both_sources_only_takes_one_slot():
    # "api" is in both lists; the wordlist is a set, so it must not use up two slots of the cap
    p = make_permutator(common_words=["www", "api"], harvested_words={"api": 3, "dev": 1}, max_words=3)
    p.build_wordlist()
    assert p.wordlist == {"www", "api", "dev"}


# --- Max permutation words (the cap) ---

def test_cap_with_priority_on():
    p = make_permutator(common_words=["www", "api", "mail"], harvested_words={"staging": 5}, max_words=2, priority=True)
    p.build_wordlist()
    assert len(p.wordlist) == 2


def test_cap_with_priority_off():
    p = make_permutator(common_words=["www"], harvested_words={"staging": 5, "dev": 4, "qa": 3}, max_words=2, priority=False)
    p.build_wordlist()
    assert len(p.wordlist) == 2


def test_cap_keeps_top_of_common_list():
    # not alphabetical on purpose: the cap must keep the first common words, not a random subset
    p = make_permutator(common_words=["www", "mail", "api", "dev"], max_words=2)
    p.build_wordlist()
    assert p.wordlist == {"www", "mail"}


def test_cap_keeps_most_frequent_harvested_words():
    # inserted least frequent first, so insertion order and frequency order disagree
    p = make_permutator(harvested_words={"rare": 1, "common": 10, "medium": 5}, max_words=2)
    p.build_wordlist()
    assert p.wordlist == {"common", "medium"}


# --- Common word priority ---

def test_priority_on_fills_common_words_first():
    p = make_permutator(common_words=["www", "api"], harvested_words={"staging": 5, "dev": 4}, max_words=3, priority=True)
    p.build_wordlist()
    assert p.wordlist == {"www", "api", "staging"}


def test_priority_off_fills_harvested_words_first():
    p = make_permutator(common_words=["www", "api"], harvested_words={"staging": 5, "dev": 4}, max_words=3, priority=False)
    p.build_wordlist()
    assert p.wordlist == {"staging", "dev", "www"}


def test_priority_on_full_of_common_words_leaves_no_room():
    p = make_permutator(common_words=["www", "api"], harvested_words={"staging": 5}, max_words=2, priority=True)
    p.build_wordlist()
    assert p.wordlist == {"www", "api"}


def test_priority_off_full_of_harvested_words_leaves_no_room():
    p = make_permutator(common_words=["www"], harvested_words={"staging": 5, "dev": 4}, max_words=2, priority=False)
    p.build_wordlist()
    assert p.wordlist == {"staging", "dev"}


# --- Minimum word occurrence ---

def test_no_minimum_includes_words_seen_once():
    p = make_permutator(harvested_words={"once": 1}, min_occurrence=None)
    p.build_wordlist()
    assert p.wordlist == {"once"}


def test_word_at_minimum_is_included():
    p = make_permutator(harvested_words={"exact": 3}, min_occurrence=3)
    p.build_wordlist()
    assert p.wordlist == {"exact"}


def test_word_below_minimum_is_excluded():
    p = make_permutator(harvested_words={"above": 4, "exact": 3, "below": 2}, min_occurrence=3)
    p.build_wordlist()
    assert p.wordlist == {"above", "exact"}


def test_minimum_does_not_apply_to_common_words():
    # common words have no count, so the minimum only filters harvested words
    p = make_permutator(common_words=["www"], harvested_words={"rare": 1}, min_occurrence=2)
    p.build_wordlist()
    assert p.wordlist == {"www"}


def test_excluded_words_leave_room_for_common_words():
    # harvested words below the minimum must not use up the cap
    p = make_permutator(common_words=["www", "api"], harvested_words={"staging": 5, "rare": 1},
                        max_words=3, priority=False, min_occurrence=2)
    p.build_wordlist()
    assert p.wordlist == {"staging", "www", "api"}


# --- prepend ---

def test_prepend_puts_each_word_before_each_domain():
    p = make_permutator(harvested_domains={"example.com", "staging.example.com"})
    p.wordlist = {"api", "dev"}
    p.prepend()
    assert p.generated_domains == {
        "api.example.com",
        "dev.example.com",
        "api.staging.example.com",
        "dev.staging.example.com",
    }


def test_prepend_skips_known_domains():
    # api.example.com was harvested, so generating it again would not be a new find
    p = make_permutator(harvested_domains={"example.com", "api.example.com"})
    p.wordlist = {"api"}
    p.prepend()
    assert p.generated_domains == {"api.api.example.com"}


def test_prepend_skips_invalid_domains():
    # every label is within 63 chars, so only the 253 total length limit can reject the result
    long_domain = ".".join(["a" * 63, "a" * 63, "a" * 63, "a" * 58])
    assert len(long_domain) == 250
    p = make_permutator(harvested_domains={long_domain, "example.com"})
    p.wordlist = {"api"}  # "api." + long_domain is 254 characters
    p.prepend()
    assert p.generated_domains == {"api.example.com"}


def test_prepend_with_empty_wordlist_generates_nothing():
    p = make_permutator(harvested_domains={"example.com"})
    p.prepend()
    assert p.generated_domains == set()


# --- generate ---

def test_generate_runs_prepend_when_enabled():
    p = make_permutator(harvested_domains={"example.com"}, enable_prepend=True)
    p.wordlist = {"api"}
    p.generate()
    assert p.generated_domains == {"api.example.com"}


def test_generate_skips_prepend_when_disabled():
    p = make_permutator(harvested_domains={"example.com"}, enable_prepend=False)
    p.wordlist = {"api"}
    p.generate()
    assert p.generated_domains == set()


def test_generate_builds_wordlist_if_empty():
    p = make_permutator(common_words=["api"], harvested_domains={"example.com"})
    p.generate()
    assert p.wordlist == {"api"}
    assert p.generated_domains == {"api.example.com"}


def test_generate_keeps_existing_wordlist():
    # a wordlist that was already built (or set by hand) must not be rebuilt or added to
    p = make_permutator(common_words=["www"], harvested_domains={"example.com"})
    p.wordlist = {"api"}
    p.generate()
    assert p.wordlist == {"api"}
    assert p.generated_domains == {"api.example.com"}
