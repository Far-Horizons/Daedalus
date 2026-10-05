import pytest
from ProteusConfig import ProteusConfig
from ProteusIO import ProteusIO


def make_io(tmp_path, known_lines=None, common_lines=None, common_max_count=None):
    # tmp_path is a fresh, empty folder that pytest creates for each test
    known_file = tmp_path / "known.txt"
    common_file = tmp_path / "common.txt"
    known_file.write_text("\n".join(known_lines or []) + "\n")
    common_file.write_text("\n".join(common_lines or []) + "\n")

    config = ProteusConfig(
        known_path=known_file,
        common_path=common_file,
        common_max_count=common_max_count,
    )
    return ProteusIO(config)


# --- load_known ---

def test_known_strips_and_lowercases(tmp_path):
    io = make_io(tmp_path, known_lines=["  API.Example.com  ", "dev.example.com"])
    assert io.load_known() == {"api.example.com", "dev.example.com"}


def test_known_skips_blank_lines(tmp_path):
    io = make_io(tmp_path, known_lines=["api.example.com", "", "   ", "dev.example.com"])
    assert io.load_known() == {"api.example.com", "dev.example.com"}


def test_known_removes_duplicates(tmp_path):
    io = make_io(tmp_path, known_lines=["api.example.com", "API.example.com"])
    assert io.load_known() == {"api.example.com"}


def test_known_does_not_validate(tmp_path):
    # validation is the harvester's job; IO must not drop lines the harvester
    # would accept after normalising (like a trailing dot)
    io = make_io(tmp_path, known_lines=["example.com.", "foo_bar"])
    assert io.load_known() == {"example.com.", "foo_bar"}


# --- load_common ---

def test_common_filters_by_pattern(tmp_path):
    io = make_io(tmp_path, common_lines=["api", "dev-test", "foo_bar", "a.b", "-bad", "bad-"])
    assert io.load_common() == {"api", "dev-test"}


def test_common_skips_blank_lines(tmp_path):
    io = make_io(tmp_path, common_lines=["api", "", "   ", "dev"])
    assert io.load_common() == {"api", "dev"}


def test_common_no_limit_loads_everything(tmp_path):
    io = make_io(tmp_path, common_lines=["a", "b", "c", "d"], common_max_count=None)
    assert io.load_common() == {"a", "b", "c", "d"}


def test_common_limit(tmp_path):
    io = make_io(tmp_path, common_lines=["a", "b", "c", "d"], common_max_count=2)
    assert io.load_common() == {"a", "b"}


def test_common_limit_ignores_skipped_lines(tmp_path):
    # blank, invalid and duplicate lines must not use up the limit
    io = make_io(tmp_path, common_lines=["a", "", "foo_bar", "a", "b", "c"], common_max_count=2)
    assert io.load_common() == {"a", "b"}


# --- errors ---

def test_missing_file_raises(tmp_path):
    config = ProteusConfig(known_path=tmp_path / "does_not_exist.txt")
    with pytest.raises(FileNotFoundError):
        ProteusIO(config).load_known()
