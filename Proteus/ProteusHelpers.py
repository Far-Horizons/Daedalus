from ProteusConstants import DOMAIN_RE, LABEL_CHAR_LIMIT, DOMAIN_CHAR_LIMIT
from dataclasses import dataclass
import tldextract

def is_valid_domain(domain: str) -> bool:
    if len(domain) > DOMAIN_CHAR_LIMIT:
        return False
    for label in domain.split("."):
        if len(label) > LABEL_CHAR_LIMIT:
            return False
    return DOMAIN_RE.fullmatch(domain) is not None

@dataclass(frozen=True)
class Domain:
    labels: tuple[str, ...] 
    domain: str
    suffix: str

    @property
    def fqdn(self) -> str:
        return ".".join(self.labels + (self.domain, self.suffix))

    @property
    def apex(self) -> str:
        return ".".join((self.domain, self.suffix))

_extract = tldextract.TLDExtract(suffix_list_urls=())

def parse_domain(domain: str) -> Domain | None:
    ext = _extract(domain)
    if not ext.suffix or not ext.domain:
        return None
    if ext.subdomain:
        labels = tuple(ext.subdomain.split("."))
    else:
        labels = tuple()
    return Domain(labels=labels, domain=ext.domain, suffix=ext.suffix)

def parse_domain_set(domains: set[str]) -> set[Domain]:
    parsed_domains = set()
    for domain in domains:
        pd = parse_domain(domain)
        if pd is not None:
            parsed_domains.add(pd)
    return parsed_domains