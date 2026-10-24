from typing import Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator

Category = Literal[
    "Email",
    "Financial",
    "Social Media",
    "Cloud Storage",
    "Shopping",
    "Work",
    "School",
    "Gaming",
    "Password Manager",
    "Communication",
    "Other",
]
RelationType = Literal[
    "PASSWORD_RESET",
    "RECOVERY_EMAIL",
    "SIGN_IN_WITH_GOOGLE",
    "SIGN_IN_WITH_APPLE",
    "SIGN_IN_WITH_FACEBOOK",
    "SHARED_PASSWORD",
    "OAUTH_READ_ACCESS",
    "OAUTH_WRITE_ACCESS",
    "PHONE_RECOVERY",
    "PASSWORD_MANAGER_STORES_CREDENTIAL",
    "OTHER",
]
WEIGHTS = dict(
    PASSWORD_RESET=10,
    RECOVERY_EMAIL=9,
    SIGN_IN_WITH_GOOGLE=9,
    SIGN_IN_WITH_APPLE=9,
    SIGN_IN_WITH_FACEBOOK=8,
    SHARED_PASSWORD=10,
    OAUTH_WRITE_ACCESS=9,
    OAUTH_READ_ACCESS=6,
    PHONE_RECOVERY=5,
    PASSWORD_MANAGER_STORES_CREDENTIAL=10,
    OTHER=5,
)


class AccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    service_name: str = Field(min_length=1, max_length=100)
    category: Category = "Other"
    email_or_username: str = Field(default="", max_length=254)
    importance: Literal["Low", "Medium", "High", "Critical"] = "Medium"
    has_mfa: bool = False
    mfa_type: Literal[
        "None", "Authenticator", "SMS", "Security key", "Email", "Other"
    ] = "None"
    has_passkey: bool = False
    recovery_phone: str = Field(default="", max_length=40)
    recovery_email: str = Field(default="", max_length=254)
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def normalize_mfa(self):
        if not self.has_mfa:
            self.mfa_type = "None"
        return self


class AccountOutput(AccountInput):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class RelationshipInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_account_id: str = Field(min_length=1, max_length=36)
    target_account_id: str = Field(min_length=1, max_length=36)
    relationship_type: RelationType
    risk_weight: int | None = Field(default=None, ge=1, le=10)
    notes: str = Field(default="", max_length=2000)


class RelationshipOutput(RelationshipInput):
    model_config = ConfigDict(from_attributes=True)
    id: str
