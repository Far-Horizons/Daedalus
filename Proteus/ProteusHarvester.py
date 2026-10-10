from ProteusConfig import ProteusConfig
from ProteusConstants import PUNYCODE_PREFIX
import ProteusHelpers
from collections import Counter
from collections.abc import Iterable

class ProteusHarvester:
    def __init__(self, config: ProteusConfig):
        self.config = config
        self.seen_domains: set[str] = set()
        self.harvested_words: Counter = Counter()
        self.harvested_domains: set[str] = set()

    def harvest(self, known_domains: Iterable[str]) -> None:
        for domain in known_domains:
            domain = domain.strip().lower().rstrip(".")
            # reject malformed or seen domains
            if not ProteusHelpers.is_valid_domain(domain) or domain in self.seen_domains:
                continue
            self.seen_domains.add(domain)
            parsed = ProteusHelpers.parse_domain(domain)
            if parsed is None:
                continue
            
            # Add the (sub)domain words to the counter
            for sw in parsed.labels:
                self.harvested_words[sw] += 1
                if self.config.harvest_split_hyphens and "-" in sw and not sw.startswith(PUNYCODE_PREFIX): # harvest individual words in a word with hyphens
                    split_words = sw.split("-")
                    for split_word in split_words:
                        if split_word:
                            self.harvested_words[split_word] += 1
            self.harvested_words[parsed.domain] += 1

            # Add the (sub)domains to the set
            self.harvested_domains.add(parsed.apex)
            for i in range(1, len(parsed.labels)+1):
                subdomain = ".".join(parsed.labels[-i:])
                self.harvested_domains.add(f"{subdomain}.{parsed.apex}")