import re

LABEL = r'[a-z0-9]([a-z0-9-]*[a-z0-9])?'

LABEL_RE = re.compile(LABEL)
DOMAIN_RE = re.compile(rf'{LABEL}(\.{LABEL})*')