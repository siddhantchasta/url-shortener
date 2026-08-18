from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class URLCreateRequest(BaseModel):
    url: HttpUrl
    custom_alias: str | None = Field(default=None, min_length=3, max_length=32)
    expires_in_hours: int | None = Field(default=None, ge=1, le=8760)

    @field_validator("custom_alias")
    @classmethod
    def alias_must_be_alnum(cls, v: str | None) -> str | None:
        if v is not None and not v.isalnum():
            raise ValueError("custom_alias must be alphanumeric")
        return v


class URLUpdateRequest(BaseModel):
    url: HttpUrl | None = None
    expires_in_hours: int | None = Field(default=None, ge=1, le=8760)


class URLResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None
    click_count: int

    model_config = {"from_attributes": True}
