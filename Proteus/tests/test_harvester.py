import pytest
from ProteusConfig import ProteusConfig
from ProteusHarvester import ProteusHarvester


def make_harvester(split_hyphens=True):
    # known_path is required by the config, but the harvester never reads it
    config = ProteusConfig(known_path="unused", harvest_split_hyphens=split_hyphens)
    return ProteusHarvester(config)


# --- Basic behaviour ---

def test_counts_subdomain_and_domain_words():
    h = make_harvester()
    h.harvest(["api.staging.example.com"])
    assert h.harvested_words == {"api": 1, "staging": 1, "example": 1}


def test_collects_all_parent_domains():
    h = make_harvester()
    h.harvest(["a.b.c.example.com"])
    assert h.harvested_domains == {
        "example.com",
        "c.example.com",
        "b.c.example.com",
        "a.b.c.example.com",
    }


def test_domain_without_subdomain():
    h = make_harvester()
    h.harvest(["example.com"])
    assert h.harvested_words == {"example": 1}
    assert h.harvested_domains == {"example.com"}


def test_multi_part_suffix():
    # tldextract should know co.uk is one suffix, so "example" is the domain word
    h = make_harvester()
    h.harvest(["api.example.co.uk"])
    assert h.harvested_words == {"api": 1, "example": 1}
    assert h.harvested_domains == {"example.co.uk", "api.example.co.uk"}


def test_word_counts_add_up_across_domains():
    h = make_harvester()
    h.harvest(["api.example.com", "api.other.com", "dev.example.com"])
    assert h.harvested_words["api"] == 2
    assert h.harvested_words["example"] == 2
    assert h.harvested_words["dev"] == 1


def test_accepts_any_iterable():
    # harvest is typed as Iterable[str], so lists, sets and generators should all work
    for known in (["api.example.com"], {"api.example.com"}, (d for d in ["api.example.com"])):
        h = make_harvester()
        h.harvest(known)
        assert h.harvested_words == {"api": 1, "example": 1}


# --- Normalisation ---

@pytest.mark.parametrize("raw", [
    "API.Example.COM",
    "  api.example.com  ",
    "api.example.com.",      # trailing dot = valid FQDN notation
    "api.example.com\n",
])
def test_normalises_input(raw):
    h = make_harvester()
    h.harvest([raw])
    assert h.harvested_domains == {"example.com", "api.example.com"}


# --- Rejection of bad input ---

@pytest.mark.parametrize("bad", [
    "",
    "a..b.example.com",      # empty label
    ".example.com",          # leading dot
    "-api.example.com",      # label starts with hyphen
    "api-.example.com",      # label ends with hyphen
    "under_score.example.com",
    "münchen.example.com",   # unicode form is not supported (only xn-- form)
    "10.0.0.1",              # no public suffix
    "localhost",             # no public suffix
    "co.uk",                 # suffix only, no domain
])
def test_rejects_bad_input(bad):
    h = make_harvester()
    h.harvest([bad])
    assert h.harvested_words == {}
    assert h.harvested_domains == set()


def test_bad_input_does_not_stop_the_rest():
    h = make_harvester()
    h.harvest(["a..b.example.com", "api.example.com"])
    assert h.harvested_domains == {"example.com", "api.example.com"}


# --- Deduplication (counts are occurrences across distinct input domains) ---

def test_duplicate_in_one_call_counted_once():
    h = make_harvester()
    h.harvest(["api.example.com", "api.example.com"])
    assert h.harvested_words["api"] == 1


def test_duplicate_after_normalisation_counted_once():
    h = make_harvester()
    h.harvest(["API.example.com", "api.example.com."])
    assert h.harvested_words["api"] == 1


def test_duplicate_across_calls_counted_once():
    h = make_harvester()
    h.harvest(["api.example.com"])
    h.harvest(["api.example.com"])
    assert h.harvested_words["api"] == 1


def test_parent_domain_in_input_is_still_counted():
    # b.example.com ends up in harvested_domains as a parent of a.b.example.com,
    # but that must not stop it from being harvested when it appears as input itself
    h = make_harvester()
    h.harvest(["a.b.example.com", "b.example.com"])
    assert h.harvested_words["b"] == 2


# --- Hyphen splitting ---

def test_splits_hyphens_and_keeps_full_word():
    h = make_harvester(split_hyphens=True)
    h.harvest(["dev-api-staging.example.com"])
    assert h.harvested_words == {
        "dev-api-staging": 1,
        "dev": 1,
        "api": 1,
        "staging": 1,
        "example": 1,
    }


def test_does_not_split_when_disabled():
    h = make_harvester(split_hyphens=False)
    h.harvest(["dev-api.example.com"])
    assert h.harvested_words == {"dev-api": 1, "example": 1}


def test_word_without_hyphen_not_double_counted():
    h = make_harvester(split_hyphens=True)
    h.harvest(["dev.example.com"])
    assert h.harvested_words["dev"] == 1


def test_double_hyphen_gives_no_empty_word():
    h = make_harvester(split_hyphens=True)
    h.harvest(["a--b.example.com"])
    assert "" not in h.harvested_words
    assert h.harvested_words == {"a--b": 1, "a": 1, "b": 1, "example": 1}


def test_punycode_label_not_split():
    h = make_harvester(split_hyphens=True)
    h.harvest(["xn--mnchen-3ya.example.com"])
    assert h.harvested_words == {"xn--mnchen-3ya": 1, "example": 1}


def test_hyphen_split_does_not_invent_domains():
    # splitting only affects word counts; dev.example.com was never observed
    h = make_harvester(split_hyphens=True)
    h.harvest(["dev-api.example.com"])
    assert h.harvested_domains == {"example.com", "dev-api.example.com"}


def test_registered_domain_word_not_split():
    # current design: only subdomain labels are split, not the domain itself
    h = make_harvester(split_hyphens=True)
    h.harvest(["my-company.com"])
    assert h.harvested_words == {"my-company": 1}
