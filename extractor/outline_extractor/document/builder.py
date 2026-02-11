from typing import List
from models.structures import LineInfo
from preprocessing.ocr_loader import extract_page_text
from preprocessing.cleaning import remove_prefixes
from detection.dispatcher import detect_heading_signals
from models.structures import HeadingDetectionConfig


def build_lines_from_page(
    page_text: str,
    skip_empty: bool,
    prefixes_to_remove: List[str]
) -> List[LineInfo]:

    lines = []

    for idx, raw in enumerate(page_text.splitlines()):
        if skip_empty and not raw.strip():
            continue

        cleaned = remove_prefixes(raw.strip(), prefixes_to_remove)

        lines.append(
            LineInfo(
                original_line_number=idx,
                raw_text=raw,
                cleaned_text=cleaned
            )
        )

    return lines


def build_document_lines(
    ocr_pages: List[List[dict]],
    skip_empty: bool,
    prefixes_to_remove: List[str]
) -> List[List[LineInfo]]:

    pages = []

    for ocr_page in ocr_pages:
        page_text = extract_page_text(ocr_page)
        lines = build_lines_from_page(
            page_text,
            skip_empty,
            prefixes_to_remove
        )
        pages.append(lines)

    return pages


def mark_page_headings(
    pages: List[List[LineInfo]],
    config: HeadingDetectionConfig
):

    for page in pages:
        for line in page:
            detect_heading_signals(line, config)


def extract_page_headings(
    pages: List[List[LineInfo]]
) -> List[List[LineInfo]]:

    result = []

    for page in pages:
        headings = [l for l in page if l.is_heading]

        if len(headings) > 0:
            result.append(headings)

    return result
