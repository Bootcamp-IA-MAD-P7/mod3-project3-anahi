import re
from io import BytesIO

import fitz
import requests


def download_pdf(pdf_url: str) -> fitz.Document:
    response = requests.get(pdf_url, timeout=30)
    response.raise_for_status()
    return fitz.open(stream=BytesIO(response.content), filetype="pdf")


def extract_text(doc: fitz.Document) -> str:
    pages = []
    for page in doc:
        pages.append(page.get_text(sort=True))
    return "\n".join(pages)


def cut_references(text: str) -> str:
    pattern = re.compile(r"\n(References|Bibliography|Works Cited)\s*\n", re.IGNORECASE)
    match = pattern.search(text)
    if match:
        return text[: match.start()]
    return text


def parse_pdf(pdf_url: str) -> str:
    doc = download_pdf(pdf_url)
    text = extract_text(doc)
    text = cut_references(text)
    doc.close()
    return text
