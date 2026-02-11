import re

def remove_prefixes(text, prefixes):
    if not prefixes:
        return text

    escaped = [re.escape(p) for p in prefixes]
    pattern = r"^(?:" + "|".join(escaped) + r")+"
    return re.sub(pattern, "", text).lstrip()
