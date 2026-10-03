import pdfplumber


def extract_pdf_text(file_path: str) -> list[dict]:
    pages = []

    with pdfplumber.open(file_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            pages.append({
                "page_number": page_number,
                "text": text,
            })

    return pages