from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class NoticeExtractionResult(BaseModel):
    """
    Strict Pydantic model for government notice field extraction.
    Only the 7 required business fields are allowed.
    """
    account: Optional[str] = None
    country: str = "United States of America"
    agency: Optional[str] = None
    agency_type: Optional[Literal["Department", "City", "Local"]] = None
    department: Optional[str] = None
    classification: Optional[str] = None
    notice_type: Optional[str] = None

    @model_validator(mode="after")
    def enforce_business_rules(self) -> "NoticeExtractionResult":
        # Rule 1: Always enforce fixed country
        self.country = "United States of America"

        # Rule 2: Clean string fields (empty strings to None)
        for field_name in ["account", "agency", "department", "classification"]:
            val = getattr(self, field_name)
            if isinstance(val, str):
                trimmed = val.strip()
                setattr(self, field_name, trimmed if trimmed else None)

        # Rule 3: Enforce notice_type always equals classification
        self.notice_type = self.classification

        # Rule 4: Validate agency_type
        if self.agency_type not in ("Department", "City", "Local"):
            self.agency_type = None

        return self

    def to_strict_dict(self) -> dict:
        """
        Returns exactly the 7 required fields as a clean dictionary with no extra properties.
        """
        return {
            "account": self.account,
            "country": "United States of America",
            "agency": self.agency,
            "agency_type": self.agency_type,
            "department": self.department,
            "classification": self.classification,
            "notice_type": self.notice_type,
        }
