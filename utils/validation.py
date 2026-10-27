"""Input validation helpers used by the interface and tests."""


def clean_user_message(value: str) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError("Write a message before sending it.")
    if len(clean) > 20_000:
        raise ValueError("Messages must be 20,000 characters or fewer.")
    return clean


def clean_title(value: str) -> str:
    clean = " ".join(value.split())
    if not clean:
        raise ValueError("Give the conversation a title.")
    return clean[:100]
