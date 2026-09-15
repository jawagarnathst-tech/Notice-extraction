from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class NoticeExtractionResult(BaseModel):
    """
    Strict Pydantic model for government notice field extraction.
    Only the 16 required business fields are allowed.
    """
    account: Optional[str] = None
    country: str = "United States of America"
    agency: Optional[str] = None
    agency_type: Optional[Literal["Department", "City", "Local"]] = None
    department: Optional[str] = None
    classification: Optional[str] = None
    notice_type: Optional[str] = None
    tax_period: Optional[str] = None
    tax_year: Optional[str] = None
    agency_id_to_use: Optional[str] = None
    amount_type: Optional[str] = None
    issue_date: Optional[str] = None
    credit_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    penalty_amount: Optional[float] = None
    interest_amount: Optional[float] = None

    @model_validator(mode="after")
    def enforce_business_rules(self) -> "NoticeExtractionResult":
        # Rule 1: Always enforce fixed country
        self.country = "United States of America"

        # Rule 2: Clean string fields (empty strings to None)
        for field_name in ["account", "agency", "department", "classification", "tax_period", "tax_year", "agency_id_to_use", "amount_type", "issue_date"]:
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
        Returns exactly the 16 required fields as a clean dictionary with no extra properties.
        """
        return {
            "account": self.account,
            "country": "United States of America",
            "agency": self.agency,
            "agency_type": self.agency_type,
            "department": self.department,
            "classification": self.classification,
            "notice_type": self.notice_type,
            "tax_period": self.tax_period,
            "tax_year": self.tax_year,
            "agency_id_to_use": self.agency_id_to_use,
            "amount_type": self.amount_type,
            "issue_date": self.issue_date,
            "credit_amount": self.credit_amount,
            "tax_amount": self.tax_amount,
            "penalty_amount": self.penalty_amount,
            "interest_amount": self.interest_amount,
        }
