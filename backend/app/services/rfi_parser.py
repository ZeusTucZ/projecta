import re


def extract_rfi_data(pages: list[dict]) -> dict:
    text = "\n".join(page["text"] for page in pages)

    labels = (
        r"Project|RFI Number|Date|Drawing Reference|"
        r"Subject|Question|Response|Potential Impact"
    )

    def extract_field(label: str) -> str | None:
        pattern = (
            rf"^[ \t]*{re.escape(label)}[ \t]*:[ \t]*"
            rf"(.*?)"
            rf"(?=^[ \t]*(?:{labels})[ \t]*:|\Z)"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )

        if match is None:
            return None

        value = match.group(1).strip()
        return value or None

    source_page = next(
        (
            page["page_number"]
            for page in pages
            if re.search(
                r"^[ \t]*RFI Number[ \t]*:",
                page["text"],
                flags=re.IGNORECASE | re.MULTILINE,
            )
        ),
        None,
    )

    return {
        "rfi_number": extract_field("RFI Number"),
        "date_issued": extract_field("Date"),
        "drawing_reference": extract_field("Drawing Reference"),
        "subject": extract_field("Subject"),
        "question": extract_field("Question"),
        "response": extract_field("Response"),
        "potential_impact": extract_field("Potential Impact"),
        "source_page": source_page,
    }