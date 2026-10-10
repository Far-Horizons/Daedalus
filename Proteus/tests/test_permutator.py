import pytest
from collections import Counter
from ProteusConfig import ProteusConfig
from ProteusPermutator import ProteusPermutator


# every strategy toggle in the config, including the ones generate() doesn't call yet
ALL_STRATEGIES = ("prepend", "insert", "hyphenate", "concat", "replace", "add_numbers", "replace_numbers")
IMPLEMENTED_STRATEGIES = ("prepend", "insert", "hyphenate", "concat", "replace", "add_numbers", "replace_numbers")


def make_permutator(common_words=None, harvested_words=None, max_words=None, priority=True, min_occurrence=None,
                    harvested_domains=None, strategies=(), deep_hyphenate=None, deep_concat=None,
                    deep_add_numbers=None, numbers_floor=0, numbers_ceiling=9, zero_padding=True, padding_depth=2):
    # strategies lists the ones generate() may run; every other strategy is switched off,
    # so adding a new strategy later can't leak extra domains into existing tests
    unknown = set(strategies) - set(ALL_STRATEGIES)
    assert not unknown, f"unknown strategy names: {unknown}"
    enable_toggles = {f"enable_{name}": name in strategies for name in ALL_STRATEGIES}

    # known_path is required by the config, but the permutator never reads it
    config = ProteusConfig(
        known_path="unused",
        max_permutation_words=max_words,
        common_word_priority=priority,
        min_word_occurrence=min_occurrence,
        deep_hyphenate=deep_hyphenate,
        deep_concat=deep_concat,
        deep_add_numbers=deep_add_numbers,
        numbers_floor=numbers_floor,
        numbers_ceiling=numbers_ceiling,
        numbers_zero_padding=zero_padding,
        numbers_zero_padding_depth=padding_depth,
        **enable_toggles,
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


def test_empty_sources_behave_like_none():
    p = make_permutator(common_words=[], harvested_words={})
    p.build_wordlist()
    assert p.wordlist == set()


# --- Max permutation words (the cap) ---

def test_cap_with_priority_on():
    p = make_permutator(common_words=["www", "api", "mail"], harvested_words={"staging": 5}, max_words=2, priority=True)
    p.build_wordlist()
    assert p.wordlist == {"www", "api"}


def test_cap_with_priority_off():
    p = make_permutator(common_words=["www"], harvested_words={"staging": 5, "dev": 4, "qa": 3}, max_words=2, priority=False)
    p.build_wordlist()
    assert p.wordlist == {"staging", "dev"}


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


def test_cap_of_zero_gives_empty_wordlist():
    # 0 is a real limit, not "no limit"; a truthiness check (if max_permutation_words:) would let everything in
    p = make_permutator(common_words=["www"], harvested_words={"api": 3}, max_words=0)
    p.build_wordlist()
    assert p.wordlist == set()


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
    # every label is within 63 chars, so only the 253 total length limit can reject the result.
    # it needs a real suffix: otherwise parse_domain drops it in __init__ and prepend never sees it
    long_domain = ".".join(["a" * 63, "a" * 63, "a" * 63, "a" * 46, "example", "com"])
    assert len(long_domain) == 250
    p = make_permutator(harvested_domains={long_domain, "example.com"})
    p.wordlist = {"api"}  # "api." + long_domain is 254 characters
    p.prepend()
    assert p.generated_domains == {"api.example.com"}


def test_prepend_with_empty_wordlist_generates_nothing():
    p = make_permutator(harvested_domains={"example.com"})
    p.prepend()
    assert p.generated_domains == set()


# --- insert ---

def test_insert_puts_word_between_labels_and_before_apex():
    p = make_permutator(harvested_domains={"api.main.example.com"})
    p.wordlist = {"dev"}
    p.insert()
    assert p.generated_domains == {"api.dev.main.example.com", "api.main.dev.example.com"}


def test_insert_never_goes_in_front_or_inside_the_apex():
    # position 0 is prepend's job, and co.uk is one suffix, so the only spot is between api and the apex
    p = make_permutator(harvested_domains={"api.example.co.uk"})
    p.wordlist = {"dev"}
    p.insert()
    assert p.generated_domains == {"api.dev.example.co.uk"}


def test_insert_uses_every_word():
    p = make_permutator(harvested_domains={"api.example.com"})
    p.wordlist = {"dev", "qa"}
    p.insert()
    assert p.generated_domains == {"api.dev.example.com", "api.qa.example.com"}


def test_insert_into_apex_domain_generates_nothing():
    p = make_permutator(harvested_domains={"example.com"})
    p.wordlist = {"dev"}
    p.insert()
    assert p.generated_domains == set()


def test_insert_skips_known_domains():
    # inserting dev into api.example.com gives api.dev.example.com, which was already harvested
    p = make_permutator(harvested_domains={"api.example.com", "api.dev.example.com"})
    p.wordlist = {"dev"}
    p.insert()
    assert p.generated_domains == {"api.dev.dev.example.com"}


# --- hyphenate ---

def test_hyphenate_shallow_only_changes_first_label():
    p = make_permutator(harvested_domains={"api.main.example.com"}, deep_hyphenate=False)
    p.wordlist = {"dev"}
    p.hyphenate()
    assert p.generated_domains == {"dev-api.main.example.com", "api-dev.main.example.com"}


def test_hyphenate_deep_changes_every_label():
    p = make_permutator(harvested_domains={"api.main.example.com"}, deep_hyphenate=True)
    p.wordlist = {"dev"}
    p.hyphenate()
    assert p.generated_domains == {
        "dev-api.main.example.com",
        "api-dev.main.example.com",
        "api.dev-main.example.com",
        "api.main-dev.example.com",
    }


def test_hyphenate_never_touches_the_apex():
    # two labels, so deep mode really does run over more than one position, but never reaches example or co.uk
    p = make_permutator(harvested_domains={"api.main.example.co.uk"}, deep_hyphenate=True)
    p.wordlist = {"dev"}
    p.hyphenate()
    assert p.generated_domains == {
        "dev-api.main.example.co.uk",
        "api-dev.main.example.co.uk",
        "api.dev-main.example.co.uk",
        "api.main-dev.example.co.uk",
    }


def test_hyphenate_skips_known_domains():
    # dev + api gives dev-api.example.com, which was already harvested
    p = make_permutator(harvested_domains={"dev-api.example.com", "api.example.com"}, deep_hyphenate=True)
    p.wordlist = {"dev"}
    p.hyphenate()
    assert p.generated_domains == {"api-dev.example.com", "dev-dev-api.example.com", "dev-api-dev.example.com"}


def test_hyphenate_follows_deep_all_when_not_set():
    # deep_hyphenate left unset, so deep_all=False should make hyphenate shallow
    config = ProteusConfig(known_path="unused", deep_all=False)
    p = ProteusPermutator(config, harvested_domains={"api.main.example.com"})
    p.wordlist = {"dev"}
    p.hyphenate()
    assert p.generated_domains == {"dev-api.main.example.com", "api-dev.main.example.com"}


def test_hyphenate_apex_domain_generates_nothing_when_shallow():
    # shallow always tries position 0, so an apex domain (no labels) must be skipped, not crash
    p = make_permutator(harvested_domains={"example.com"}, deep_hyphenate=False)
    p.wordlist = {"dev"}
    p.hyphenate()
    assert p.generated_domains == set()


def test_hyphenate_apex_domain_generates_nothing_when_deep():
    p = make_permutator(harvested_domains={"example.com"}, deep_hyphenate=True)
    p.wordlist = {"dev"}
    p.hyphenate()
    assert p.generated_domains == set()


def test_hyphenate_skips_labels_that_get_too_long():
    # 60 + len("-dev") = 64, one over the 63 character label limit
    long_label = "a" * 60
    p = make_permutator(harvested_domains={f"{long_label}.example.com", "api.example.com"}, deep_hyphenate=False)
    p.wordlist = {"dev"}
    p.hyphenate()
    assert p.generated_domains == {"dev-api.example.com", "api-dev.example.com"}


# --- concat ---

def test_concat_shallow_only_changes_first_label():
    p = make_permutator(harvested_domains={"api.main.example.com"}, deep_concat=False)
    p.wordlist = {"dev"}
    p.concat()
    assert p.generated_domains == {"devapi.main.example.com", "apidev.main.example.com"}


def test_concat_deep_changes_every_label():
    p = make_permutator(harvested_domains={"api.main.example.com"}, deep_concat=True)
    p.wordlist = {"dev"}
    p.concat()
    assert p.generated_domains == {
        "devapi.main.example.com",
        "apidev.main.example.com",
        "api.devmain.example.com",
        "api.maindev.example.com",
    }


def test_concat_uses_its_own_depth_setting():
    # concat must read deep_concat, not deep_hyphenate (they share a helper, so wiring them up wrong is easy)
    p = make_permutator(harvested_domains={"api.main.example.com"}, deep_concat=False, deep_hyphenate=True)
    p.wordlist = {"dev"}
    p.concat()
    assert p.generated_domains == {"devapi.main.example.com", "apidev.main.example.com"}


def test_concat_follows_deep_all_when_not_set():
    config = ProteusConfig(known_path="unused", deep_all=False)
    p = ProteusPermutator(config, harvested_domains={"api.main.example.com"})
    p.wordlist = {"dev"}
    p.concat()
    assert p.generated_domains == {"devapi.main.example.com", "apidev.main.example.com"}


def test_concat_never_touches_the_apex():
    p = make_permutator(harvested_domains={"api.example.co.uk"}, deep_concat=True)
    p.wordlist = {"dev"}
    p.concat()
    assert p.generated_domains == {"devapi.example.co.uk", "apidev.example.co.uk"}


def test_concat_apex_domain_generates_nothing():
    p = make_permutator(harvested_domains={"example.com"}, deep_concat=False)
    p.wordlist = {"dev"}
    p.concat()
    assert p.generated_domains == set()


# --- replace ---

def test_replace_swaps_out_a_label():
    p = make_permutator(harvested_domains={"api.main.example.com"})
    p.wordlist = {"dev"}
    p.replace()
    assert p.generated_domains == {"api.dev.example.com"}


def test_replace_every_label_except_the_first():
    # position 0 is skipped: dev.b.c.example.com would equal prepend on the parent b.c.example.com,
    # which the harvester always provides
    p = make_permutator(harvested_domains={"a.b.c.example.com"})
    p.wordlist = {"dev"}
    p.replace()
    assert p.generated_domains == {"a.dev.c.example.com", "a.b.dev.example.com"}


def test_replace_never_touches_the_apex():
    p = make_permutator(harvested_domains={"api.main.example.co.uk"})
    p.wordlist = {"dev"}
    p.replace()
    assert p.generated_domains == {"api.dev.example.co.uk"}


def test_replace_single_label_and_apex_domains_generate_nothing():
    p = make_permutator(harvested_domains={"api.example.com", "example.com"})
    p.wordlist = {"dev"}
    p.replace()
    assert p.generated_domains == set()


def test_replace_with_the_same_label_is_skipped():
    # swapping main for main gives back the harvested domain itself
    p = make_permutator(harvested_domains={"api.main.example.com"})
    p.wordlist = {"main"}
    p.replace()
    assert p.generated_domains == set()


# --- add_numbers ---

def test_add_numbers_appends_each_number_with_and_without_hyphen():
    p = make_permutator(harvested_domains={"api.example.com"}, numbers_floor=0, numbers_ceiling=2, zero_padding=False)
    p.add_numbers()
    assert p.generated_domains == {
        "api0.example.com", "api-0.example.com",
        "api1.example.com", "api-1.example.com",
        "api2.example.com", "api-2.example.com",
    }


def test_add_numbers_ceiling_is_inclusive():
    p = make_permutator(harvested_domains={"api.example.com"}, numbers_floor=8, numbers_ceiling=9, zero_padding=False)
    p.add_numbers()
    assert "api9.example.com" in p.generated_domains


def test_add_numbers_pads_up_to_padding_depth():
    p = make_permutator(harvested_domains={"api.example.com"}, numbers_floor=1, numbers_ceiling=1, padding_depth=3)
    p.add_numbers()
    assert p.generated_domains == {
        "api1.example.com", "api-1.example.com",
        "api01.example.com", "api-01.example.com",
        "api001.example.com", "api-001.example.com",
    }


def test_add_numbers_ignores_padding_depth_when_padding_is_off():
    p = make_permutator(harvested_domains={"api.example.com"}, numbers_floor=1, numbers_ceiling=1,
                        zero_padding=False, padding_depth=3)
    p.add_numbers()
    assert p.generated_domains == {"api1.example.com", "api-1.example.com"}


def test_add_numbers_keeps_numbers_wider_than_padding_depth():
    # 100 has 3 digits but the depth is 2; it must still be generated, just without padding
    p = make_permutator(harvested_domains={"api.example.com"}, numbers_floor=100, numbers_ceiling=100, padding_depth=2)
    p.add_numbers()
    assert p.generated_domains == {"api100.example.com", "api-100.example.com"}


def test_add_numbers_shallow_only_changes_first_label():
    p = make_permutator(harvested_domains={"api.main.example.com"}, deep_add_numbers=False,
                        numbers_floor=1, numbers_ceiling=1, zero_padding=False)
    p.add_numbers()
    assert p.generated_domains == {"api1.main.example.com", "api-1.main.example.com"}


def test_add_numbers_deep_changes_every_label():
    p = make_permutator(harvested_domains={"api.main.example.com"}, deep_add_numbers=True,
                        numbers_floor=1, numbers_ceiling=1, zero_padding=False)
    p.add_numbers()
    assert p.generated_domains == {
        "api1.main.example.com", "api-1.main.example.com",
        "api.main1.example.com", "api.main-1.example.com",
    }


def test_add_numbers_follows_deep_all_when_not_set():
    config = ProteusConfig(known_path="unused", deep_all=False, numbers_floor=1, numbers_ceiling=1,
                           numbers_zero_padding=False)
    p = ProteusPermutator(config, harvested_domains={"api.main.example.com"})
    p.add_numbers()
    assert p.generated_domains == {"api1.main.example.com", "api-1.main.example.com"}


def test_add_numbers_never_touches_the_apex():
    p = make_permutator(harvested_domains={"api.example.co.uk"}, deep_add_numbers=True,
                        numbers_floor=1, numbers_ceiling=1, zero_padding=False)
    p.add_numbers()
    assert p.generated_domains == {"api1.example.co.uk", "api-1.example.co.uk"}


@pytest.mark.parametrize("deep", (False, True))
def test_add_numbers_apex_domain_generates_nothing(deep):
    p = make_permutator(harvested_domains={"example.com"}, deep_add_numbers=deep)
    p.add_numbers()
    assert p.generated_domains == set()


def test_add_numbers_skips_known_domains():
    # api1.example.com was harvested, so only its hyphen version is new for api
    p = make_permutator(harvested_domains={"api.example.com", "api1.example.com"}, deep_add_numbers=False,
                        numbers_floor=1, numbers_ceiling=1, zero_padding=False)
    p.add_numbers()
    assert p.generated_domains == {"api-1.example.com", "api11.example.com", "api1-1.example.com"}


def test_add_numbers_skips_labels_that_get_too_long():
    # 62 + len("1") = 63 fits the label limit, 62 + len("-1") = 64 does not
    long_label = "a" * 62
    p = make_permutator(harvested_domains={f"{long_label}.example.com"}, numbers_floor=1, numbers_ceiling=1,
                        zero_padding=False)
    p.add_numbers()
    assert p.generated_domains == {f"{long_label}1.example.com"}


# --- replace_numbers ---

def test_replace_numbers_replaces_each_number_separately():
    # the worked example: 1 and 02 are each swapped on their own, never both at once
    p = make_permutator(harvested_domains={"db1-node02.example.com"}, numbers_floor=0, numbers_ceiling=2)
    p.replace_numbers()
    assert p.generated_domains == {
        "db0-node02.example.com", "db2-node02.example.com",
        "db1-node00.example.com", "db1-node01.example.com",
    }


def test_replace_numbers_keeps_original_width():
    p = make_permutator(harvested_domains={"web01.example.com"}, numbers_floor=0, numbers_ceiling=2)
    p.replace_numbers()
    assert p.generated_domains == {"web00.example.com", "web02.example.com"}


def test_replace_numbers_ignores_padding_settings():
    # the width comes from the harvested number, so padding depth 3 must not add web01 or web001
    p = make_permutator(harvested_domains={"web1.example.com"}, numbers_floor=0, numbers_ceiling=2,
                        zero_padding=True, padding_depth=3)
    p.replace_numbers()
    assert p.generated_domains == {"web0.example.com", "web2.example.com"}


def test_replace_numbers_keeps_numbers_wider_than_original():
    # 100 is wider than 01; zfill only pads, it never cuts, so it must still come out whole
    p = make_permutator(harvested_domains={"web01.example.com"}, numbers_floor=100, numbers_ceiling=100)
    p.replace_numbers()
    assert p.generated_domains == {"web100.example.com"}


def test_replace_numbers_ceiling_is_inclusive():
    p = make_permutator(harvested_domains={"web1.example.com"}, numbers_floor=8, numbers_ceiling=9)
    p.replace_numbers()
    assert p.generated_domains == {"web8.example.com", "web9.example.com"}


def test_replace_numbers_in_the_middle_of_a_label():
    p = make_permutator(harvested_domains={"apiv2test.example.com"}, numbers_floor=0, numbers_ceiling=2)
    p.replace_numbers()
    assert p.generated_domains == {"apiv0test.example.com", "apiv1test.example.com"}


def test_replace_numbers_changes_every_label():
    # there is no deep setting for replace_numbers, it always goes through every label
    p = make_permutator(harvested_domains={"db1.node2.example.com"}, numbers_floor=0, numbers_ceiling=1)
    p.replace_numbers()
    assert p.generated_domains == {"db0.node2.example.com", "db1.node0.example.com", "db1.node1.example.com"}


def test_replace_numbers_never_touches_the_apex():
    # the 2 in example2 belongs to the apex, so only api1 may change
    p = make_permutator(harvested_domains={"api1.example2.com"}, numbers_floor=0, numbers_ceiling=1)
    p.replace_numbers()
    assert p.generated_domains == {"api0.example2.com"}


def test_replace_numbers_without_digits_generates_nothing():
    p = make_permutator(harvested_domains={"example.com", "api.example.com"})
    p.replace_numbers()
    assert p.generated_domains == set()


def test_replace_numbers_skips_known_domains():
    # web1 and web2 would each generate the other, but both were already harvested
    p = make_permutator(harvested_domains={"web1.example.com", "web2.example.com"}, numbers_floor=1, numbers_ceiling=2)
    p.replace_numbers()
    assert p.generated_domains == set()


# --- generate ---

# every number suffix the default settings give: 0-9, padded up to 2 digits, with and without a hyphen
DEFAULT_NUMBER_SUFFIXES = {f"{sep}{str(num).zfill(width)}" for num in range(10) for width in (1, 2) for sep in ("", "-")}

# what each strategy produces at full depth for word "dev" and domain "api1.main.example.com".
# api1 has a digit on purpose: without one, replace_numbers would expect an empty set and prove nothing
DESIGN_TABLE = {
    "prepend":   {"dev.api1.main.example.com"},
    "insert":    {"api1.dev.main.example.com", "api1.main.dev.example.com"},
    "hyphenate": {"dev-api1.main.example.com", "api1-dev.main.example.com",
                  "api1.dev-main.example.com", "api1.main-dev.example.com"},
    "concat":    {"devapi1.main.example.com", "api1dev.main.example.com",
                  "api1.devmain.example.com", "api1.maindev.example.com"},
    "replace":   {"api1.dev.example.com"},
    # the number strategies ignore the wordlist, so "dev" never shows up in them
    "add_numbers": {f"api1{s}.main.example.com" for s in DEFAULT_NUMBER_SUFFIXES}
                 | {f"api1.main{s}.example.com" for s in DEFAULT_NUMBER_SUFFIXES},
    # api1 itself is the harvested domain, so it is skipped
    "replace_numbers": {f"api{n}.main.example.com" for n in range(10)} - {"api1.main.example.com"},
}


@pytest.mark.parametrize("strategy", IMPLEMENTED_STRATEGIES)
def test_generate_runs_only_the_enabled_strategy(strategy):
    p = make_permutator(harvested_domains={"api1.main.example.com"}, strategies=(strategy,),
                        deep_hyphenate=True, deep_concat=True, deep_add_numbers=True)
    p.wordlist = {"dev"}
    p.generate()
    assert p.generated_domains == DESIGN_TABLE[strategy]


def test_generate_with_every_strategy_disabled_generates_nothing():
    p = make_permutator(harvested_domains={"api.main.example.com"}, strategies=())
    p.wordlist = {"dev"}
    p.generate()
    assert p.generated_domains == set()


def test_generate_combines_all_enabled_strategies():
    p = make_permutator(harvested_domains={"api1.main.example.com"}, strategies=("prepend", "replace"))
    p.wordlist = {"dev"}
    p.generate()
    assert p.generated_domains == DESIGN_TABLE["prepend"] | DESIGN_TABLE["replace"]


def test_generate_with_defaults_matches_design_table():
    # only config defaults: every strategy enabled and deep_all=True, so this is the whole design table
    config = ProteusConfig(known_path="unused")
    p = ProteusPermutator(config, harvested_domains={"api1.main.example.com"})
    p.wordlist = {"dev"}
    p.generate()
    assert p.generated_domains == set().union(*DESIGN_TABLE.values())


def test_generate_builds_wordlist_if_empty():
    p = make_permutator(common_words=["api"], harvested_domains={"example.com"}, strategies=("prepend",))
    p.generate()
    assert p.wordlist == {"api"}
    assert p.generated_domains == {"api.example.com"}


def test_generate_keeps_existing_wordlist():
    # a wordlist that was already built (or set by hand) must not be rebuilt or added to
    p = make_permutator(common_words=["www"], harvested_domains={"example.com"}, strategies=("prepend",))
    p.wordlist = {"api"}
    p.generate()
    assert p.wordlist == {"api"}
    assert p.generated_domains == {"api.example.com"}


def test_generate_with_no_words_only_runs_number_strategies():
    # every strategy on, so the word strategies really are empty because of the missing words.
    # the number strategies don't use words, so their output is all that's left
    p = make_permutator(harvested_domains={"api1.main.example.com"}, strategies=IMPLEMENTED_STRATEGIES,
                        deep_add_numbers=True)
    p.generate()
    assert p.generated_domains == DESIGN_TABLE["add_numbers"] | DESIGN_TABLE["replace_numbers"]
