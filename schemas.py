from pydantic import BaseModel
from typing import Optional
from datetime import date

class IceCubeReconPersBase(BaseModel):
    empl_id: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    service_period: Optional[date]
    empl_rcd: Optional[str]
    earnings_code: Optional[str]
    ern_rate: Optional[float]
    earnings: Optional[float]
    contribution_rate: Optional[int]
    contribution_amt: Optional[float]
    erncd: Optional[str]
    contribution_code: Optional[int]
    work_schedule_code: Optional[str]
    user_source: Optional[str]
    retirement_code: Optional[str]
    check_date: Optional[date]

class IceCubeReconPersCreate(IceCubeReconPersBase):
    pass

class IceCubeReconPersRead(IceCubeReconPersBase):
    id: int

    class Config:
        orm_mode = True
