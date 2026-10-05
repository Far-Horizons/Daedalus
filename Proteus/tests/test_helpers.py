import pytest
from ProteusHelpers import is_valid_domain


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
