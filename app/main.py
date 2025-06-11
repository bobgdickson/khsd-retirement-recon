from fastapi import FastAPI

from app.routes.recon_import import router
from app.routes.ui_router import router as ui_router

app = FastAPI(title="Ice Cube Data Import API", version="1.0.0")

app.include_router(router, prefix="/api", tags=["ice_cube"])
app.include_router(ui_router, tags=["ui"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)