import secrets
import string

ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int = 6) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def build_short_url(domain: str, short_code: str) -> str:
    scheme = "http" if domain.startswith("localhost") else "https"
    return f"{scheme}://{domain}/{short_code}"
