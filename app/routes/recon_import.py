from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import io
from datetime import datetime, date
from app.db import get_db, get_engine
from dateutil.relativedelta import relativedelta
from app.models import IceCubeReconPers, IceCubeReconStrs
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import PASSPHRASE

"""
Routes and processing logic for uploading and importing Ice Cube data.
"""
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


# Define mapping
STRS_COLUMN_MAP = {
    "EMPLOYEE ID": "empl_id",
    "FIRST NAME": "first_name",
    "LAST NAME": "last_name",
    "CHECK DATE": "check_date",
    "EMPLOYEE RECORD": "empl_rcd",
    "MEMBER CODE": "member_code",
    "EARNINGS CODE": "earnings_code",
    "EARNINGS BEGIN": "earnings_begin",
    "EARNINGS END": "earnings_end",
    "EARNINGS RATE": "ern_rate",
    "EARNINGS": "earnings",
    "CONTRIBUTION RATE": "contribution_rate",
    "CONTRIBUTION AMOUNT": "contribution_amt",
    "ASSIGNMENT": "assignment",
    "CONTRIBUTION CODE": "contribution_code",
    "PAY CODE": "pay_code",
    "SOURCE": "input_source",
    "VERIFIED": "verified",
    "STRS": "retirement_type",
    "RECON PERIOD": "recon_period",
}

PERS_COLUMN_MAP = {
    "EMPLOYEE ID": "empl_id",
    "FIRST NAME": "first_name",
    "LAST NAME": "last_name",
    "SERVICE PERIOD": "service_period",
    "EMPLOYEE RECORD": "empl_rcd",
    "EARNINGS CODE": "earnings_code",
    "EARNINGS RATE": "ern_rate",
    "EARNINGS": "earnings",
    "CONTRIBUTION RATE": "contribution_rate",
    "CONTRIBUTION AMOUNT": "contribution_amt",
    "EARN CODE": "erncd",
    "CONTRIBUTION CODE": "contribution_code",
    "WORK SCHEDULE CODE": "work_schedule_code",
    "SOURCE": "user_source",
    "RECON PERIOD": "recon_period",
}

def detect_file_type(df: pd.DataFrame) -> str | None:
    """
    Look at df.columns (upper‐cased) and decide:
      - If it has STRS‐specific headers → return "STRS"
      - If it has PERS‐specific headers → return "PERS"
      - Otherwise → return None
    """

    # Normalize column names
    upcols = [col.strip().upper() for col in df.columns]

    # PERS files almost always include a "SERVICE PERIOD" (or "SERVICE P") column
    # and usually "EARN CODE" or "WORK SCHEDULE CODE", etc.
    pers_keywords = {"SERVICE PERIOD", "WORK SCHEDULE CODE", "EMPLOYEE RECORD"}  # tweak if your exports differ
    # STRS files almost always include a "CHECK DATE" column and a "MEMBER CODE" column
    strs_keywords = {"STRS", "ASSIGNMENT", "PAY CODE"}

    # Count how many keywords appear in the header list
    pers_count = sum(1 for h in upcols for kw in pers_keywords if kw in h)
    strs_count = sum(1 for h in upcols for kw in strs_keywords if kw in h)

    # If one clearly dominates, return it
    if pers_count > strs_count:
        return "PERS"
    if strs_count > pers_count:
        return "STRS"
    # If neither side is strong, return None
    return None

def clean_code(val, width=2):
    """
    Clean and format a code value by zero-padding.

    Args:
        val: The input value, possibly numeric or string.
        width: Minimum width for the output string, padded with zeros.

    Returns:
        A zero-padded string code, or None if input is null.
    """
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return str(int(val))  # 0.0 to "0"
    return str(val).strip().zfill(width)

def to_date(val):
    """
    Convert various input types to a date object.

    Args:
        val: A datetime/date/string value.

    Returns:
        A date object if conversion is successful, otherwise None.
    """
    if pd.isna(val):
        return None
    if isinstance(val, (datetime, date)):
        return val.date()
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None

def process_ice_cube_upload(df: pd.DataFrame, parsed_date: date, pension_plan: str, db: Session):
    """
    Process and import Ice Cube DataFrame into the reconciliation database.

    This will detect the file type (PERS or STRS), validate against the provided
    pension_plan, clean and transform the DataFrame, delete any existing records
    for the recon_period, and bulk-insert the new records.

    Args:
        df (pd.DataFrame): DataFrame loaded from the uploaded file.
        parsed_date (date): The reporting month parsed as a date.
        pension_plan (str): 'PERS' or 'STRS' indicating the target plan.
        db (Session): SQLAlchemy database session.

    Returns:
        dict: Summary with message and rows_inserted count.

    Raises:
        HTTPException: If file type detection or pension_plan is invalid.
    """
    detected_plan = detect_file_type(df)
    if detected_plan and pension_plan != detected_plan:
        raise HTTPException(
            status_code=400,
            detail=f"Detected file type '{detected_plan}' does not match provided pension_plan '{pension_plan}'."
        )
    
    start_of_month = parsed_date.replace(day=1)
    end_of_month = (start_of_month.replace(month=start_of_month.month % 12 + 1, day=1)
                    if start_of_month.month < 12
                    else start_of_month.replace(year=start_of_month.year + 1, month=1, day=1))

    if pension_plan == "PERS":
        db.query(IceCubeReconPers).filter(
            IceCubeReconPers.recon_period == parsed_date.strftime("%Y-%m"),
        ).delete(synchronize_session=False)

        df.columns = [col.strip().upper() for col in df.columns]
        df.rename(columns=PERS_COLUMN_MAP, inplace=True)
        df["check_date"] = parsed_date
        df["recon_period"] = parsed_date.strftime("%Y-%m")

        records = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            record_data = {
                "empl_id": str(row_dict.get("empl_id")).zfill(6) if pd.notna(row_dict.get("empl_id")) else None,
                "first_name": str(row_dict.get("first_name")).strip() if pd.notna(row_dict.get("first_name")) else None,
                "last_name": str(row_dict.get("last_name")).strip() if pd.notna(row_dict.get("last_name")) else None,
                "service_period": to_date(row_dict.get("service_period")),
                "empl_rcd": str(row_dict.get("empl_rcd")).zfill(2) if pd.notna(row_dict.get("empl_rcd")) else None,
                "earnings_code": str(row_dict.get("earnings_code")) if pd.notna(row_dict.get("earnings_code")) else None,
                "ern_rate": float(row_dict.get("ern_rate")) if pd.notna(row_dict.get("ern_rate")) else None,
                "earnings": float(row_dict.get("earnings")) if pd.notna(row_dict.get("earnings")) else None,
                "contribution_rate": float(row_dict.get("contribution_rate")) if pd.notna(row_dict.get("contribution_rate")) else None,
                "contribution_amt": float(row_dict.get("contribution_amt")) if pd.notna(row_dict.get("contribution_amt")) else None,
                "erncd": str(row_dict.get("erncd")) if pd.notna(row_dict.get("erncd")) else None,
                "contribution_code": int(row_dict.get("contribution_code")) if pd.notna(row_dict.get("contribution_code")) else None,
                "work_schedule_code": clean_code(row_dict.get("work_schedule_code")),
                "user_source": str(row_dict.get("user_source")) if pd.notna(row_dict.get("user_source")) else None,
                "retirement_code": str(row_dict.get("retirement_code")) if pd.notna(row_dict.get("retirement_code")) else None,
                "check_date": to_date(row_dict.get("check_date")),
                "recon_period": row_dict.get("recon_period", parsed_date.strftime("%Y-%m")),
            }
            records.append(IceCubeReconPers(**record_data))

    elif pension_plan == "STRS":
        db.query(IceCubeReconStrs).filter(
            IceCubeReconStrs.recon_period == parsed_date.strftime("%Y-%m"),
        ).delete(synchronize_session=False)

        df.columns = [col.strip().upper() for col in df.columns]
        df.rename(columns=STRS_COLUMN_MAP, inplace=True)

        df["recon_period"] = parsed_date.strftime("%Y-%m")

        records = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            record_data = {
                "empl_id": str(row_dict.get("empl_id")).zfill(6) if pd.notna(row_dict.get("empl_id")) else None,
                "first_name": str(row_dict.get("first_name")).strip() if pd.notna(row_dict.get("first_name")) else None,
                "last_name": str(row_dict.get("last_name")).strip() if pd.notna(row_dict.get("last_name")) else None,
                "check_date": to_date(row_dict.get("check_date")),
                "empl_rcd": str(row_dict.get("empl_rcd")).zfill(2) if pd.notna(row_dict.get("empl_rcd")) else None,
                "member_code": int(row_dict.get("member_code")) if pd.notna(row_dict.get("member_code")) else None,
                "earnings_code": str(row_dict.get("earnings_code")) if pd.notna(row_dict.get("earnings_code")) else None,
                "earnings_begin": to_date(row_dict.get("earnings_begin")),
                "earnings_end": to_date(row_dict.get("earnings_end")),
                "ern_rate": float(row_dict.get("ern_rate")) if pd.notna(row_dict.get("ern_rate")) else None,
                "earnings": float(row_dict.get("earnings")) if pd.notna(row_dict.get("earnings")) else None,
                "contribution_rate": float(row_dict.get("contribution_rate")) if pd.notna(row_dict.get("contribution_rate")) else None,
                "contribution_amt": float(row_dict.get("contribution_amt")) if pd.notna(row_dict.get("contribution_amt")) else None,
                "assignment": int(row_dict.get("assignment")) if pd.notna(row_dict.get("assignment")) else None,
                "contribution_code": int(row_dict.get("contribution_code")) if pd.notna(row_dict.get("contribution_code")) else None,
                "pay_code": int(row_dict.get("pay_code")) if pd.notna(row_dict.get("pay_code")) else None,
                "input_source": str(row_dict.get("input_source")) if pd.notna(row_dict.get("input_source")) else None,
                "retirement_type": str(row_dict.get("retirement_type")) if pd.notna(row_dict.get("retirement_type")) else None,
                "verified": bool(int(row_dict.get("verified"))) if pd.notna(row_dict.get("verified")) else None,
                "recon_period": row_dict.get("recon_period", parsed_date.strftime("%Y-%m")),
            }
            records.append(IceCubeReconStrs(**record_data))
    else:
        raise HTTPException(status_code=400, detail="Invalid pension_plan. Use 'PERS' or 'STRS'.")

    db.bulk_save_objects(records)
    db.commit()

    # Stage Payroll Data
    rows_staged = load_staging_data(parsed_date.strftime("%Y-%m"))

    return {"message": "Upload successful", "rows_inserted": len(records)}

@router.post("/import-ice-cube/")
async def import_ice_cube_file(
    file: UploadFile = File(...),
    month: str = Form(...),
    pension_plan: str = Form(...),
    passphrase: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    API endpoint to upload an Ice Cube file and import its contents.

    Validates the passphrase, reads the spreadsheet or CSV into a DataFrame,
    and delegates to process_ice_cube_upload.

    Args:
        file (UploadFile): Excel (.xlsx) or CSV file upload.
        month (str): Reporting month in 'YYYY-MM' format.
        pension_plan (str): 'PERS' or 'STRS'.
        passphrase (str): Secret passphrase to authorize import.
        db (Session): Database session dependency.

    Returns:
        dict: Result from process_ice_cube_upload.

    Raises:
        HTTPException: If passphrase is invalid.
    """
    if passphrase != PASSPHRASE:
        raise HTTPException(status_code=403, detail="Invalid passphrase.")
    parsed_date = datetime.strptime(month, "%Y-%m")
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents)) if file.filename.endswith(".xlsx") else pd.read_csv(io.StringIO(contents.decode("utf-8")))
    return process_ice_cube_upload(df, parsed_date, pension_plan, db)

def load_staging_data(month):
    """
    Load and stage payroll data for a given recon_period month.

    Queries existing staging table and PeopleSoft database, replaces the
    local staging table if counts mismatch.

    Args:
        month (str): Recon period in 'YYYY-MM' format.

    Returns:
        int: Number of rows pulled from PeopleSoft.
    """
    parsed = datetime.strptime(month, "%Y-%m")
    start_window = (parsed - relativedelta(months=1)).replace(day=1)
    end_window = (parsed + relativedelta(months=1)).replace(day=1)
    # Convert to strings for SQL parameters
    start_window = start_window.strftime("%Y-%m-%d")
    end_window = end_window.strftime("%Y-%m-%d")

    cube_engine = get_engine(name="local")

    stage_sql = """
    SELECT COUNT(*) FROM ICE_CUBE_PAY_DATA_STAGING
    WHERE PAY_END_DT >= ? AND PAY_END_DT < ?
    """
    existing_count = pd.read_sql(
        stage_sql,
        cube_engine,
        params=(start_window, end_window)
    ).iloc[0, 0]

    # Connect to PeopleSoft DB
    ps_engine = get_engine(name="ps")

    ps_query = """
    SELECT
        C.EMPLID,
        C.PAY_END_DT,
        C.PAGE_NUM,
        C.LINE_NUM,
        C.PAYGROUP,
        C.OFF_CYCLE,
        C.SEPCHK,
        D.DEDCD,
        D.DED_CLASS,
        D.DED_CUR
    FROM PS_PAY_CHECK C
    LEFT JOIN PS_PAY_DEDUCTION D
        ON D.PAGE_NUM = C.PAGE_NUM
        AND D.LINE_NUM = C.LINE_NUM
        AND D.PAY_END_DT = C.PAY_END_DT
        AND D.PAYGROUP = C.PAYGROUP
        AND D.OFF_CYCLE = C.OFF_CYCLE
        AND D.SEPCHK = C.SEPCHK
        AND D.DEDCD IN ('PERPB2' ,'PERPBD' ,'PERPBD' ,'PERS' ,'PERSAJ' ,'PERSAJ' ,'PERSP' ,'PERSPB','STRPB2','STRPBY','STRS','STRSAJ','STRSPB')
    WHERE
        C.PAY_END_DT >= ? AND C.PAY_END_DT < ?
    """

    # Pull from PeopleSoft
    df = pd.read_sql(
        ps_query,
        ps_engine,
        params=(start_window, end_window)
    )

    # Compare count of existing staged data
    if existing_count != len(df):
        print(f"Staging data count mismatch: existing {existing_count}, new {len(df)}")
        # Save to local staging table
        df.to_sql("ICE_CUBE_PAY_DATA_STAGING", cube_engine, if_exists="replace", index=False)

    return len(df)

@router.post("/import-payroll-staging/")
async def import_payroll_staging(month: str, db: Session = Depends(get_db)):
    """
    API endpoint to trigger staging of payroll data for a given month.

    Args:
        month (str): Recon period in 'YYYY-MM' format.
        db (Session): Database session dependency (unused here).

    Returns:
        dict: Message and count of rows copied into staging.
    """
    rows_inserted = load_staging_data(month)
    return {"message": "Payroll data copied", "rows_inserted": rows_inserted}

