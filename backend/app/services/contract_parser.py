import re


def extract_contract_data(pages: list[dict]) -> dict:
    text = "\n".join(page["text"] for page in pages)

    def extract_line(label: str) -> str | None:
        match = re.search(
            rf"^[ \t]*{re.escape(label)}[ \t]*:[ \t]*([^\r\n]*)",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        if match is None:
            return None

        return match.group(1).strip() or None

    sections = []

    section_pattern = (
        r"^[ \t]*Section[ \t]+"
        r"(?P<number>\d+(?:\.\d+)*)"
        r"[ \t]*[-–—][ \t]*"
        r"(?P<title>[^\r\n]+)\r?\n"
        r"(?P<content>.*?)"
        r"(?=^[ \t]*Section[ \t]+\d+(?:\.\d+)*[ \t]*[-–—]|\Z)"
    )

    for match in re.finditer(
        section_pattern,
        text,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    ):
        # Locate the page where this section starts.
        offset = 0
        source_page = None

        for page in pages:
            if offset <= match.start() < offset + len(page["text"]):
                source_page = page["page_number"]
                break

            offset += len(page["text"]) + 1

        sections.append({
            "section_number": match.group("number"),
            "title": match.group("title").strip(),
            "text": match.group("content").strip(),
            "source_page": source_page,
        })

    return {
        "contract_number": extract_line("Contract No."),
        "trade": extract_line("Trade"),
        "sections": sections,
    }