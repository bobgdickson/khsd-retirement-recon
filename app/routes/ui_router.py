"""
HTMX-based UI routes for rendering the upload form and handling uploads.
"""
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import io
from app.db import get_db
from app.routes.recon_import import process_ice_cube_upload  # ← assumes logic lives in recon_import.py
from app.config import PASSPHRASE

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def render_upload_form(request: Request):
    """
    Render the main upload form page.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTMLResponse: The upload form template.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/upload", response_class=HTMLResponse)
async def handle_upload(
    request: Request,
    file: UploadFile = File(...),
    month: str = Form(...),
    pension_plan: str = Form(...),
    passphrase: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Handle HTMX file upload from the UI and process Ice Cube data.

    Args:
        request (Request): FastAPI request object.
        file (UploadFile): Excel or CSV file upload.
        month (str): Reporting month in 'YYYY-MM' format.
        pension_plan (str): 'PERS' or 'STRS'.
        passphrase (str): Secret passphrase for authorization.
        db (Session): Database session dependency.

    Returns:
        HTMLResponse: Success or error message fragment.
    """
    if passphrase != PASSPHRASE:
        return HTMLResponse("<div class='error'>❌ Invalid passphrase.</div>", status_code=403)
    try:
        parsed_date = datetime.strptime(month, "%Y-%m")
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents)) if file.filename.endswith(".xlsx") else pd.read_csv(io.StringIO(contents.decode("utf-8")))
        result = process_ice_cube_upload(df, parsed_date, pension_plan, db)
        return HTMLResponse(f"<div class='success'>✅ {result['rows_inserted']} rows uploaded and staged.</div>")
    except Exception as e:
        return HTMLResponse(f"<div class='error'>❌ Upload failed: {str(e)}</div>", status_code=400)
