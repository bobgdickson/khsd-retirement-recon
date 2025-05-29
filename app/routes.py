from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import io
from datetime import datetime, date
from app.db import get_db
from app.models import IceCubeReconPers, IceCubeReconStrs

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
    "STRS": "retirement_type",  # Assuming STRS is a type, not a code
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
    "SOURCE": "user_source"
}

def clean_code(val, width=2):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return str(int(val)) # 0.0 to "0"
    return str(val).strip().zfill(width)

def to_date(val):
    if pd.isna(val):
        return None
    if isinstance(val, (datetime, date)):
        return val.date()
    try:
        return pd.to_datetime(val).date()
    except:
        return None

@router.post("/import-ice-cube/", response_model=dict)
async def import_ice_cube_data(
    file: UploadFile = File(...),
    month: str = Form(...),  # format: YYYY-MM
    pension_plan: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validate month
    try:
        parsed_date = datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Month format must be YYYY-MM")

    # Read file contents
    contents = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        elif file.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    # Add service_period if needed
    df["service_period"] = parsed_date
    print("Original columns:", df.columns.tolist())
    print(df.head())
    # Determine model and delete existing records for same month
    start_of_month = parsed_date.replace(day=1)
    if pension_plan == "PERS":
        db.query(IceCubeReconPers).filter(
            IceCubeReconPers.check_date >= start_of_month,
            IceCubeReconPers.check_date < (start_of_month.replace(month=start_of_month.month % 12 + 1, day=1)
                                           if start_of_month.month < 12
                                           else start_of_month.replace(year=start_of_month.year + 1, month=1, day=1))
        ).delete(synchronize_session=False)

        df.columns = [col.strip().upper() for col in df.columns]
        df.rename(columns=PERS_COLUMN_MAP, inplace=True)

        # Add check_date from parsed_date
        df["check_date"] = parsed_date

        allowed_fields = {column.name for column in IceCubeReconPers.__table__.columns}

        records = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            record_data = {
                "empl_id": str(row_dict.get("empl_id")).strip() if pd.notna(row_dict.get("empl_id")) else None,
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
            }

            records.append(IceCubeReconPers(**record_data))

    elif pension_plan == "STRS":
        db.query(IceCubeReconStrs).filter(
            IceCubeReconStrs.check_date >= start_of_month,
            IceCubeReconStrs.check_date < (start_of_month.replace(month=start_of_month.month % 12 + 1, day=1)
                                           if start_of_month.month < 12
                                           else start_of_month.replace(year=start_of_month.year + 1, month=1, day=1))
        ).delete(synchronize_session=False)
        
        # Clean and normalize column names
        df.columns = [col.strip().upper() for col in df.columns]


        # Apply column renaming
        df.rename(columns=STRS_COLUMN_MAP, inplace=True)

        # Log for debugging
        print("Renamed columns:", df.columns.tolist())
        print("Sample row:", df.iloc[0].to_dict())

        # Restrict to fields defined in the SQLAlchemy model
        allowed_fields = {column.name for column in IceCubeReconStrs.__table__.columns}

        # Drop any columns that don't match
        records = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()

            record_data = {
                "empl_id": str(row_dict.get("empl_id")).strip() if pd.notna(row_dict.get("empl_id")) else None,
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
            }

            try:
                records.append(IceCubeReconStrs(**record_data))
            except Exception as e:
                print("Row failed:", record_data)
                print("Error:", e)
    else:
        raise HTTPException(status_code=400, detail="Invalid pension_plan. Use 'PERS' or 'STRS'.")

    db.bulk_save_objects(records)
    db.commit()

    return {"message": "Upload successful", "rows_inserted": len(records)}
