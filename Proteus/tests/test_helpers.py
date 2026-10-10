import pytest
from dataclasses import FrozenInstanceError
from ProteusHelpers import is_valid_domain, Domain, parse_domain, parse_domain_set


def make_domain(length):
    # builds a domain of exactly `length` characters out of 63-char labels,
    # so only the total length limit can be the reason it gets rejected
    labels = []
    remaining = length
    while remaining > 0:
        label_len = min(63, remaining)
        labels.append("a" * label_len)
        remaining -= label_len + 1  # +1 for the dot that joins it to the next label
    domain = ".".join(labels)
    assert len(domain) == length
    return domain


# --- Basic behaviour ---

@pytest.mark.parametrize("good", [
    "example.com",
    "api.staging.example.com",
    "dev-api.example.com",
    "a.b",                       # shortest possible labels
    "123.example.com",           # labels may be all digits
    "xn--mnchen-3ya.example.com",
])
def test_accepts_valid_domains(good):
    assert is_valid_domain(good)


@pytest.mark.parametrize("bad", [
    "",
    "a..b.example.com",          # empty label
    ".example.com",              # leading dot
    "example.com.",              # trailing dot (the harvester strips it before calling)
    "-api.example.com",          # label starts with hyphen
    "api-.example.com",          # label ends with hyphen
    "under_score.example.com",
    "API.example.com",           # uppercase (the harvester lowercases before calling)
    "münchen.example.com",
    "api example.com",
])
def test_rejects_malformed_domains(bad):
    assert not is_valid_domain(bad)


# --- Label length limit (63) ---

def test_label_at_limit_is_valid():
    assert is_valid_domain("a" * 63 + ".example.com")


def test_label_over_limit_is_rejected():
    assert not is_valid_domain("a" * 64 + ".example.com")


def test_long_label_in_the_middle_is_rejected():
    # every label is checked, not just the first one
    assert not is_valid_domain("api." + "a" * 64 + ".example.com")


# --- Total length limit (253) ---

def test_domain_at_limit_is_valid():
    assert is_valid_domain(make_domain(253))


def test_domain_over_limit_is_rejected():
    assert not is_valid_domain(make_domain(254))


# --- Domain ---

def test_fqdn_joins_labels_domain_and_suffix():
    d = Domain(labels=("api", "main"), domain="example", suffix="com")
    assert d.fqdn == "api.main.example.com"


def test_fqdn_without_labels_is_the_apex():
    d = Domain(labels=(), domain="example", suffix="com")
    assert d.fqdn == "example.com"


def test_fqdn_with_multi_part_suffix():
    d = Domain(labels=("api",), domain="example", suffix="co.uk")
    assert d.fqdn == "api.example.co.uk"


def test_apex_ignores_labels():
    d = Domain(labels=("api", "main"), domain="example", suffix="co.uk")
    assert d.apex == "example.co.uk"


def test_domain_is_frozen():
    d = Domain(labels=("api",), domain="example", suffix="com")
    with pytest.raises(FrozenInstanceError):
        d.labels = ("dev",)


# --- parse_domain ---

def test_parse_splits_subdomain_into_labels_in_order():
    assert parse_domain("api.main.example.com") == Domain(labels=("api", "main"), domain="example", suffix="com")


def test_parse_apex_domain_has_no_labels():
    # "".split(".") gives [""], so an apex domain must not end up with one empty label
    assert parse_domain("example.com") == Domain(labels=(), domain="example", suffix="com")


def test_parse_multi_part_suffix():
    # co.uk is one suffix, so "example" is the domain and not a label
    assert parse_domain("api.example.co.uk") == Domain(labels=("api",), domain="example", suffix="co.uk")


@pytest.mark.parametrize("domain", [
    "example.com",
    "api.example.com",
    "api.main.example.co.uk",
])
def test_parse_then_fqdn_gives_back_the_input(domain):
    assert parse_domain(domain).fqdn == domain


@pytest.mark.parametrize("bad", [
    "",
    "localhost",         # no suffix at all
    "foo.invalidtld",    # unknown suffix
    "co.uk",             # a bare suffix with no domain in front of it
])
def test_parse_returns_none_without_domain_or_suffix(bad):
    assert parse_domain(bad) is None


def test_parse_does_not_repair_malformed_input():
    # validation is the caller's job (is_valid_domain); parse_domain must not hide broken input
    assert parse_domain("a..b.example.com").labels == ("a", "", "b")


# --- parse_domain_set ---

def test_parse_set_parses_every_domain():
    assert parse_domain_set({"api.example.com", "example.co.uk"}) == {
        Domain(labels=("api",), domain="example", suffix="com"),
        Domain(labels=(), domain="example", suffix="co.uk"),
    }


def test_parse_set_drops_unparseable_domains():
    # a mix: only the domains parse_domain can handle survive, the rest are skipped without an error
    assert parse_domain_set({"api.example.com", "localhost", "foo.invalidtld", ""}) == {
        Domain(labels=("api",), domain="example", suffix="com"),
    }


def test_parse_set_of_nothing_is_empty():
    assert parse_domain_set(set()) == set()
