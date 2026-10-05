from dataclasses import dataclass
import pathlib
import json

PROTEUS_CONFIG = pathlib.Path(__file__).parent / "proteus_config.json"

@dataclass # defaults are determined here
class ProteusConfig:
    known_path: str | pathlib.Path
    common_path: str | pathlib.Path = pathlib.Path(__file__).parent / "common_words/most_common.txt"
    common_max_count: int | None = None
    harvest_split_hyphens: bool = True

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