from extractor.outline_extractor.models.structures import HeadingSignal
from extractor.outline_extractor.detection.detectors import *

def detect_heading_signals(line, config):
    line.heading_signals.clear()

    if config.HEADING_DETECTION.enable_regex and detect_by_outline_regex(line.cleaned_text):
        line.heading_signals.append(HeadingSignal.REGEX_OUTLINE)

    if config.HEADING_DETECTION.enable_hash and detect_by_hash_prefix(line.raw_text):
        line.heading_signals.append(HeadingSignal.HASH_PREFIX)

    if config.HEADING_DETECTION.enable_length and detect_by_length(
        line.cleaned_text,
        config.HEADING_DETECTION.min_length,
        config.HEADING_DETECTION.max_length
    ):
        line.heading_signals.append(HeadingSignal.LENGTH_RANGE)

    line.is_heading = len(line.heading_signals) > 0
