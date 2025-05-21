from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import IceCubeReconPers, Base
from schemas import IceCubeReconPersRead
from typing import List
from datetime import datetime
import pandas as pd
import io

app = FastAPI(title="KHSD Retirement Recon API", version="1.0")

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/import-ice-cube/", response_model=dict)
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

    # Add metadata columns (can be updated in future with data cleanup step)
    df["service_period"] = parsed_date

    # Convert to list of model instances
    records = []
    if pension_plan == "PERS":
        for _, row in df.iterrows():
            record = IceCubeReconPers(
                empl_id=row.get("EMPL_ID"),
                first_name=row.get("FIRST_NAME"),
                last_name=row.get("LAST_NAME"),
                service_period=row.get("service_period"),
                empl_rcd=row.get("EMPL_RCD"),
                earnings_code=row.get("EARNINGS_CODE"),
                ern_rate=row.get("ERN_RATE"),
                earnings=row.get("EARNINGS"),
                contribution_rate=row.get("CONTRIBUTION_RATE"),
                contribution_amt=row.get("CONTRIBUTION_AMT"),
                erncd=row.get("ERNCD"),
                contribution_code=row.get("CONTRIBUTION_CODE"),
                work_schedule_code=row.get("WORK_SCHEDULE_CODE"),
                user_source=row.get("user_source"),
                retirement_code=row.get("RETIREMENT_CODE"),
                check_date=row.get("CHECK_DATE")
            )
            records.append(record)

        # Insert into DB
        db.bulk_save_objects(records)
        db.commit()

    return {"message": "Upload successful", "rows_inserted": len(records)}
