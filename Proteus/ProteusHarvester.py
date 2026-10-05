from ProteusConfig import ProteusConfig
from ProteusConstants import DOMAIN_RE
from collections import Counter
from collections.abc import Iterable
import tldextract
import re


class ProteusHarvester:

    _extract = tldextract.TLDExtract(suffix_list_urls=())

    def __init__(self, config: ProteusConfig):
        self.config = config
        self.seen_domains: set[str] = set()
        self.harvested_words: Counter = Counter()
        self.harvested_domains: set[str] = set()

    def harvest(self, known_domains: Iterable[str]) -> None:
        for domain in known_domains:
            domain = domain.strip().lower().rstrip(".")
            # reject malformed or seen domains
            if not re.fullmatch(DOMAIN_RE, domain) or domain in self.seen_domains:
                continue
            self.seen_domains.add(domain)
            ext = self._extract(domain)
            if not ext.suffix or not ext.domain: # skip empty suffixes and domains
                continue
            sub_words = []
            if ext.subdomain:
                sub_words = ext.subdomain.split(".")

            # Add the (sub)domain words to the counter
            for sw in sub_words:
                self.harvested_words[sw] += 1
                if self.config.harvest_split_hyphens and "-" in sw and not sw.startswith("xn--"): # harvest individual words in a word with hyphens
                    split_words = sw.split("-")
                    for split_word in split_words:
                        if split_word:
                            self.harvested_words[split_word] += 1
            self.harvested_words[ext.domain] += 1

            # Add the (sub)domains to the set
            self.harvested_domains.add(f"{ext.domain}.{ext.suffix}")
            for i in range(1, len(sub_words)+1):
                subdomain = ".".join(sub_words[-i:])
                self.harvested_domains.add(f"{subdomain}.{ext.domain}.{ext.suffix}")