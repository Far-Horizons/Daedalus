from ProteusConstants import DOMAIN_RE, LABEL_CHAR_LIMIT, DOMAIN_CHAR_LIMIT

def is_valid_domain(domain: str) -> bool:
    if len(domain) > DOMAIN_CHAR_LIMIT:
        return False
    for label in domain.split("."):
        if len(label) > LABEL_CHAR_LIMIT:
            return False
    return DOMAIN_RE.fullmatch(domain) is not None