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

class IceCubeReconStrsBase(BaseModel):
    empl_id: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    check_date: Optional[date]
    empl_rcd: Optional[str]
    member_code: Optional[int]
    earnings_code: Optional[str]
    earnings_begin: Optional[date]
    earnings_end: Optional[date]
    ern_rate: Optional[float]
    earnings: Optional[float]
    contribution_rate: Optional[int]
    contribution_amt: Optional[float]
    assignment: Optional[int]
    contribution_code: Optional[int]
    pay_code: Optional[int]
    input_source: Optional[str]
    retirement_type: Optional[str]
    retirement_code: Optional[str]
    verified: Optional[bool]

class IceCubeReconStrsCreate(IceCubeReconStrsBase):
    pass

class IceCubeReconStrsRead(IceCubeReconStrsBase):
    id: int

    class Config:
        orm_mode = True