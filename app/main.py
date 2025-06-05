from fastapi import FastAPI
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import io
from datetime import datetime, date
from app.db import get_db
from app.models import IceCubeReconPers, IceCubeReconStrs
from app.routes.recon_import import router
from app.routes.ui_router import router as ui_router

app = FastAPI(title="Ice Cube Data Import API", version="1.0.0")

app.include_router(router, prefix="/api", tags=["ice_cube"])
app.include_router(ui_router, tags=["ui"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)