from ProteusConfig import ProteusConfig
import ProteusHelpers
from collections import Counter
import dataclasses
import re

class ProteusPermutator:
    """Expects input from ProteusHarvester. It can work without, but may miss things if not prepped properly."""
    def __init__(self,
                 config:            ProteusConfig,
                 harvested_domains: set[str],
                 common_words:      list[str] | None = None,
                 harvested_words:   Counter | None = None):
        self.config             = config
        self.harvested_domains  = ProteusHelpers.parse_domain_set(harvested_domains)
        self.common_words       = common_words
        self.harvested_words    = harvested_words
        self.wordlist:          set[str] = set()
        self.generated_domains: set[str] = set()

    def _is_full(self) -> bool:
        return self.config.max_permutation_words is not None and len(self.wordlist) >= self.config.max_permutation_words

    def _fill_from(self, words: set[str] | list[str] | None) -> None:
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

    def _add_candidate(self, domain: ProteusHelpers.Domain) -> None:
        fqdn = domain.fqdn
        if domain not in self.harvested_domains and ProteusHelpers.is_valid_domain(fqdn):
            self.generated_domains.add(fqdn)

    def _attach_to_label(self, *, deep: bool, separator: str) -> None:
        for domain in self.harvested_domains:
            if not domain.labels:
                continue
            positions = range(len(domain.labels)) if deep else range(1)
            for i in positions:
                before, label, after = domain.labels[:i], domain.labels[i], domain.labels[i+1:]
                for word in self.wordlist:
                    for new_label in (f"{word}{separator}{label}", f"{label}{separator}{word}"):
                        self._add_candidate(dataclasses.replace(domain, labels=before+(new_label,)+after))

    def prepend(self) -> None:
        for domain in self.harvested_domains:
            for word in self.wordlist:
                self._add_candidate(dataclasses.replace(domain, labels=(word,)+domain.labels))
                
    def insert(self) -> None:
        for domain in self.harvested_domains:
            if not domain.labels:
                continue
            for i in range(1, len(domain.labels)+1):
                before, after = domain.labels[:i], domain.labels[i:]
                for word in self.wordlist:
                    new_labels = before+(word,)+after
                    self._add_candidate(dataclasses.replace(domain, labels=new_labels))

    def hyphenate(self) -> None:
        assert self.config.deep_hyphenate is not None
        self._attach_to_label(deep=self.config.deep_hyphenate, separator="-")

    def concat(self) -> None:
        assert self.config.deep_concat is not None
        self._attach_to_label(deep=self.config.deep_concat, separator="")

    def replace(self) -> None: # skip single label domains as these would only generate duplicates
        for domain in self.harvested_domains:
            for i in range(1, len(domain.labels)):
                before, after = domain.labels[:i], domain.labels[i+1:]
                for word in self.wordlist:
                    new_labels = before+(word,)+after
                    self._add_candidate(dataclasses.replace(domain, labels=new_labels))

    def add_numbers(self) -> None:
        assert self.config.deep_add_numbers is not None
        separators = ["", "-"]
        for domain in self.harvested_domains:
            if not domain.labels:
                continue
            positions = range(len(domain.labels)) if self.config.deep_add_numbers else range(1)
            for i in positions:
                before, label, after = domain.labels[:i], domain.labels[i], domain.labels[i+1:]
                if self.config.numbers_zero_padding:
                    target_depth = self.config.numbers_zero_padding_depth
                else:
                    target_depth = 1
                for num in range(self.config.numbers_floor, self.config.numbers_ceiling + 1):
                    for amt in range(1, target_depth + 1):
                        for sep in separators:
                            new_label = f"{label}{sep}{str(num).zfill(amt)}"
                            self._add_candidate(dataclasses.replace(domain, labels=before+(new_label,)+after))

    def replace_numbers(self) -> None:
        for domain in self.harvested_domains:
            if not domain.labels:
                continue
            for i in range(len(domain.labels)):
                before, label, after = domain.labels[:i], domain.labels[i], domain.labels[i+1:]
                for match in re.finditer(r"[0-9]+", label):
                    head, number, tail = label[:match.start()], match.group(), label[match.end():]
                    for num in range(self.config.numbers_floor, self.config.numbers_ceiling + 1):
                        new_label = f"{head}{str(num).zfill(len(number))}{tail}"
                        self._add_candidate(dataclasses.replace(domain, labels=before+(new_label,)+after))

    def generate(self) -> None:
        if not self.wordlist:
            self.build_wordlist()
        strategies = [
            (self.config.enable_prepend, self.prepend),
            (self.config.enable_insert, self.insert),
            (self.config.enable_hyphenate, self.hyphenate),
            (self.config.enable_concat, self.concat),
            (self.config.enable_replace, self.replace),
            (self.config.enable_add_numbers, self.add_numbers),
            (self.config.enable_replace_numbers, self.replace_numbers),
        ]
        for enabled, run in strategies:
            if enabled:
                run()