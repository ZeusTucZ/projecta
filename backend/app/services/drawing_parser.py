import re


def extract_drawing_data(pages: list[dict]) -> list[dict]:
    drawings = []

    for page in pages:
        text = page["text"]

        number_match = re.search(
            r"\bDRAWING:\s*([^\s]+)",
            text,
            flags=re.IGNORECASE,
        )

        revision_match = re.search(
            r"\bREVISION:\s*([^\s]+)",
            text,
            flags=re.IGNORECASE,
        )

        title_match = re.search(
            r"^[ \t]*\S+[ \t]+(.+?)[ \t]+-[ \t]+REV[ \t]+\S+[ \t]*$",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        discipline_match = re.search(
            r"\bDISCIPLINE:[ \t]*([^\r\n]+)",
            text,
            flags=re.IGNORECASE,
        )

        drawings.append({
            "drawing_number": (
                number_match.group(1) if number_match else None
            ),
            "revision": (
                revision_match.group(1) if revision_match else None
            ),
            "title": (
                title_match.group(1).strip() if title_match else None
            ),
            "discipline": (
                discipline_match.group(1).strip()
                if discipline_match
                else None
            ),
            "source_page": page["page_number"],
        })

    return drawings