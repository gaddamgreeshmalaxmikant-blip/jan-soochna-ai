from pydantic import BaseModel
from typing import List, Optional, Union

class Rule(BaseModel):
    field: str
    operator: str
    value: Optional[Union[float, int, str, bool]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    values: Optional[List[str]] = None

class Scheme(BaseModel):
    scheme_id: str
    name: str
    description: str
    department: str
    source_url: str
    benefits: str
    documents_required: List[str]
    rules: List[Rule]

class UserProfile(BaseModel):
    age: int
    annual_income: float
    state: str
    land_owner: Optional[bool] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None