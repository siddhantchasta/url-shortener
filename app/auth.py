from fastapi import Header, HTTPException, status

from app.config import settings


async def require_api_key(x_api_key: str = Header(...)) -> None:
    """Gates write endpoints and debug routes. Reads and redirects stay public —
    that's the whole point of a link shortener. A single shared key is enough
    for a portfolio project; a real product would issue per-client keys."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
