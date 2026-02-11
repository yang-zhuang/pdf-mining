import re

def is_valid_outline_line(line):
    return bool(re.match(r"^\d+(\.\d+)*", line.strip()))

def extract_outline_lines(response):
    result = []
    for line in response.splitlines():
        if not line.strip():
            result.append("")
        elif is_valid_outline_line(line):
            result.append(line)
    return result
