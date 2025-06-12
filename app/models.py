"""
SQLAlchemy ORM models defining Ice Cube reconciliation and staging tables.
"""
from sqlalchemy import Column, Integer, String, Float, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class IceCubeReconPers(Base):
    __tablename__ = 'ICE_CUBE_RECON_PERS'
    extend_existing = True  # Allow extending existing table

    """
    ORM model for PERS reconciliation table ICE_CUBE_RECON_PERS.
    """

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
    recon_period = Column(String(7)) 

class IceCubeReconStrs(Base):
    __tablename__ = "ICE_CUBE_RECON_STRS"
    extend_existing = True

    """
    ORM model for STRS reconciliation table ICE_CUBE_RECON_STRS.
    """

    id = Column("ID", Integer, primary_key=True, index=True)
    empl_id = Column("EMPL_ID", String(10), nullable=True)
    first_name = Column("FIRST_NAME", String, nullable=True)
    last_name = Column("LAST_NAME", String, nullable=True)
    check_date = Column("CHECK_DATE", Date, nullable=True)
    empl_rcd = Column("EMPL_RCD", String(2), nullable=True)
    member_code = Column("MEMBER_CODE", Integer, nullable=True)
    earnings_code = Column("EARNINGS_CODE", String(10), nullable=True)
    earnings_begin = Column("EARNINGS_BEGIN", Date, nullable=True)
    earnings_end = Column("EARNINGS_END", Date, nullable=True)
    ern_rate = Column("ERN_RATE", Float, nullable=True)
    earnings = Column("EARNINGS", Float, nullable=True)
    contribution_rate = Column("CONTRIBUTION_RATE", Integer, nullable=True)
    contribution_amt = Column("CONTRIBUTION_AMT", Float, nullable=True)
    assignment = Column("ASSIGNMENT", Integer, nullable=True)
    contribution_code = Column("CONTRIBUTION_CODE", Integer, nullable=True)
    pay_code = Column("PAY_CODE", Integer, nullable=True)
    input_source = Column("INPUT_SOURCE", String, nullable=True)
    retirement_type = Column("RETIREMENT_TYPE", String(10), nullable=True)
    retirement_code = Column("RETIREMENT_CODE", String(10), nullable=True)
    verified = Column("VERIFIED", Boolean, nullable=True)
    recon_period = Column("RECON_PERIOD", String(7), nullable=True)

class IceCubePayDataStaging(Base):
    __tablename__ = "ICE_CUBE_PAY_DATA_STAGING"
    extend_existing = True

    """
    ORM model for staging payroll data table ICE_CUBE_PAY_DATA_STAGING.
    """

    id = Column(Integer, primary_key=True, autoincrement=True)
    emplid = Column(String(10), nullable=True)
    pay_end_dt = Column(Date, nullable=True)
    page_num = Column(Integer, nullable=True)
    line_num = Column(Integer, nullable=True)
    paygroup = Column(String(10), nullable=True)
    off_cycle = Column(String(10), nullable=True)
    sepchk = Column(Integer, nullable=True)
    dedcd = Column(String(10), nullable=True)
    ded_class = Column(String(10), nullable=True)
    ded_cur = Column(Float, nullable=True)
