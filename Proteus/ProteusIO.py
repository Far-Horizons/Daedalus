from ProteusConfig import ProteusConfig
from ProteusConstants import LABEL_RE
import re

class ProteusIO:
    def __init__(self, config: ProteusConfig):
        self.config = config

    @staticmethod
    def _load_lines(path, pattern: re.Pattern[str] | str | None = None, line_limit=None) -> list[str]:
        lines = []
        seen = set()
        with open(path, "r") as f:
            for line in f:
                if line_limit is not None and len(lines) >= line_limit:
                    break
                line = line.strip().lower()
                if not line:
                    continue
                if pattern is None or re.fullmatch(pattern, line):
                    if line not in seen:
                        seen.add(line)
                        lines.append(line)
        return lines

    def load_known(self) -> list[str]:
        return self._load_lines(self.config.known_path) # regex validation handled by harvester

    def load_common(self) -> list[str]:
        return self._load_lines(self.config.common_path, LABEL_RE, line_limit=self.config.max_common_words)