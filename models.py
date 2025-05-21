from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class IceCubeReconPers(Base):
    __tablename__ = 'ICE_CUBE_RECON_PERS'

    id = Column(Integer, primary_key=True, autoincrement=True)
    empl_id = Column(String(10))
    first_name = Column(String)  # VARCHAR(MAX)
    last_name = Column(String)   # VARCHAR(MAX)
    service_period = Column(Date)
    empl_rcd = Column(String(2))
    earnings_code = Column(String(10))
    ern_rate = Column(Float)
    earnings = Column(Float)
    contribution_rate = Column(Integer)
    contribution_amt = Column(Float)
    erncd = Column(String(10))
    contribution_code = Column(Integer)
    work_schedule_code = Column(String(2))
    user_source = Column(String)  # VARCHAR(MAX)
    retirement_code = Column(String(10))
    check_date = Column(Date)
