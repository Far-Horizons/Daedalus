from dataclasses import dataclass
import pathlib
import json

PROTEUS_CONFIG = pathlib.Path(__file__).parent / "proteus_config.json"

@dataclass # defaults are determined here
class ProteusConfig:
    # IO settings
    known_path: str | pathlib.Path
    common_path: str | pathlib.Path = pathlib.Path(__file__).parent / "common_words/most_common.txt"
    max_common_words: int | None  = None  # Maximum amount of common words used in the word list for the permutator. None means no limit.

    # Harvester settings
    harvest_split_hyphens: bool = True

    # Permutator word list settings
    max_permutation_words:  int | None  = 500   # Maximum amount of words used by the permutator
    common_word_priority:   bool        = True  # Should the common word list have priority over harvested words?
    min_word_occurrence:    int | None  = None  # Minimum amount of times a word needs to be harvested before being used in the permutator

    # Permutation Strategy toggles
    enable_prepend          : bool = True
    enable_insert           : bool = True
    enable_hyphenate        : bool = True
    enable_concat           : bool = True
    enable_replace          : bool = True
    enable_add_numbers      : bool = True
    enable_replace_numbers  : bool = True

    # Permutation Strategy depth toggles
    # If deep_all is set to True, the other depth toggles default to True. They can be individually set to False.
    # If deep_all is set to False, the other depth toggles default to False. They can be individually set to True.
    deep_all            : bool        = True
    deep_hyphenate      : bool | None = None
    deep_concat         : bool | None = None
    deep_add_numbers    : bool | None = None

    def __post_init__(self):
        self.enforce_consistency()

    @classmethod # any setting in the JSON will override the default
    def from_json(cls, known_path: str| pathlib.Path, cfg_path: str | pathlib.Path | None = None) -> "ProteusConfig":
        use_default = cfg_path is None
        if use_default:
            cfg_path = PROTEUS_CONFIG

        try:
            with open(cfg_path, "r") as f:
                cfg = json.load(f)
        except FileNotFoundError:
            if not use_default:
                raise
            cfg = {}

        return cls(known_path=known_path, **cfg)

    def enforce_consistency(self):
        # max common words can't be more than the max permutation words
        if self.max_common_words is not None and self.max_permutation_words is not None and self.max_common_words > self.max_permutation_words:
            raise ValueError(f"max_common_words ({self.max_common_words}) can't be more than max_permutation_words ({self.max_permutation_words})")
        # if a max permutation words is set, but no max common words, cap max common words at max permutation words
        if self.max_common_words is None and self.max_permutation_words is not None:
            self.max_common_words = self.max_permutation_words