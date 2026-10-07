from ProteusConfig import ProteusConfig
from ProteusHelpers import is_valid_domain
from collections import Counter

class ProteusPermutator:
    def __init__(self,
                 config:            ProteusConfig,
                 harvested_domains: set[str],
                 common_words:      list[str] | None = None,
                 harvested_words:   Counter | None = None):
        self.config             = config
        self.harvested_domains  = harvested_domains
        self.common_words       = common_words
        self.harvested_words    = harvested_words
        self.wordlist:          set[str] = set()
        self.generated_domains: set[str] = set()

    def _is_full(self) -> bool:
        return self.config.max_permutation_words is not None and len(self.wordlist) >= self.config.max_permutation_words

    def _fill_from(self, words: set[str] | list[str] | Counter | None) -> None:
        if words is None:
            return
        for word in words:
            if self._is_full():
                break
            self.wordlist.add(word)

    def build_wordlist(self) -> None:
        # if common words are set as priority, fill with common words
        if self.config.common_word_priority:
            self._fill_from(self.common_words)

        # fill with harvested words, up to the max wordlist length, and enforcing minimum count if it exists.
        if self.harvested_words is not None:
            eligible_words = [word for word, count in self.harvested_words.most_common() if self.config.min_word_occurrence is None or count >= self.config.min_word_occurrence]
            self._fill_from(eligible_words)

        # if common words are not set as priority, fill with common words if there is remaining space.
        if not self.config.common_word_priority:
            self._fill_from(self.common_words)

    def _add_candidate(self, domain: str) -> None:
        if domain not in self.harvested_domains and is_valid_domain(domain):
            self.generated_domains.add(domain)

    def prepend(self) -> None:
        for domain in self.harvested_domains:
            for word in self.wordlist:
                self._add_candidate(f"{word}.{domain}")
                
    def insert(self) -> None:
        pass

    def hyphenate(self) -> None:
        pass

    def concat(self) -> None:
        pass

    def replace(self) -> None:
        pass

    def add_numbers(self) -> None:
        pass

    def replace_numbers(self) -> None:
        pass

    def generate(self) -> None:
        if not self.wordlist:
            self.build_wordlist()
        if self.config.enable_prepend:
            self.prepend()