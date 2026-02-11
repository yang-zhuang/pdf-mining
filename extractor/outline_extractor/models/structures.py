from dataclasses import dataclass, field
from typing import List
from enum import Enum

class HeadingSignal(str, Enum):
    REGEX_OUTLINE = "regex_outline"
    HASH_PREFIX = "hash_prefix"
    LENGTH_RANGE = "length_range"


@dataclass
class LineInfo:
    original_line_number: int
    raw_text: str
    cleaned_text: str
    is_heading: bool = False
    heading_signals: List[HeadingSignal] = field(default_factory=list)


@dataclass
class HeadingDetectionConfig:
    enable_regex: bool = True
    enable_hash: bool = True
    enable_length: bool = True
    min_length: int = 2
    max_length: int = 40
