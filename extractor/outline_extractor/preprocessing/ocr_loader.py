def extract_page_text(ocr_page):
    contents = [
        e["page_content"]
        for e in ocr_page
        if "page_content" in e
    ]
    if len(contents) != 1:
        raise ValueError("Each OCR page must contain one page_content")
    return contents[0]
