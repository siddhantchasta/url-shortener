import secrets
import string

ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int = 6) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def build_short_url(domain: str, short_code: str) -> str:
    cleaned_domain = domain.removeprefix("https://").removeprefix("http://").rstrip("/")
    scheme = "http" if cleaned_domain.startswith("localhost") else "https"
    return f"{scheme}://{cleaned_domain}/{short_code}"

