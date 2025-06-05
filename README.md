## 🧊 KHSD Ice Cube Retirement Reconciliation API

This service ingests `.xlsx` or `.csv` files from the Ice Cube export system, applies light transformation and metadata tagging, and writes the cleaned records into a SQL-backed reconciliation table. It is designed to support anomaly detection and iterative reconciliation against production PeopleSoft HCM data, powering a Power BI worklist dashboard for HR and payroll teams.

---

### 📌 Purpose

- **Input**: Ice Cube retirement export files (e.g., STRS/PERS earnings and contributions)
- **Transformation**: Adds metadata (`recon_period`, `service_period`), with optional future validation/cleanup steps
- **Storage**: Writes to pre-defined SQL tables (`ICE_CUBE_RECON_PERS`, `ICE_CUBE_RECON_STRS`)
- **Workflow**: Power BI surfaces discrepancies between Ice Cube and PeopleSoft HCM → users iteratively correct issues in Ice Cube and re-upload until resolution

---

### ⚙️ Tech Stack

- **FastAPI** backend for file ingestion
- **SQLAlchemy** ORM with SQL Server backend
- **Pandas** for Excel/CSV parsing and transformation
- **Docker** for containerized deployment
- **HTMX** UI for drag-and-drop upload with live progress
- **GitHub Actions** for image build on push to `main`

---

### 🚀 Deployment

1. **Clone the repo**

2. Create a `.env` file with your database connection string:

   ```env
   DATABASE_URL=mssql+pyodbc://user:pass@host/dbname?driver=ODBC+Driver+17+for+SQL+Server
   PS_DB_URL=mssql+pyodbc://user:pass@host/dbname?driver=ODBC+Driver+17+for+SQL+Server
````

3. **Run locally via Docker Compose**:

   ```bash
   docker-compose up --build
   ```

4. Or pull the latest built image:

   ```bash
   docker pull ghcr.io/bobgdickson/khsd-retirement-recon:latest
   docker run --env-file .env -p 8000:8000 ghcr.io/bobgdickson/khsd-retirement-recon:latest
   ```

---

### 📤 API File Upload Endpoint

**URL**: `POST /api/import-ice-cube/`
**Content-Type**: `multipart/form-data`

**Parameters**:

* `file`: `.xlsx` or `.csv` file from Ice Cube
* `month`: Service month in `YYYY-MM` format (e.g., `"2024-04"`)
* `pension_plan`: `"STRS"` or `"PERS"`

**Example cURL**:

```bash
curl -X POST http://localhost:8000/api/import-ice-cube/ \
  -F "file=@export_apr.xlsx" \
  -F "month=2024-04" \
  -F "pension_plan=STRS"
```

---

### 💻 Web UI (HTMX)

**URL**: `GET /`

This interface provides a user-friendly upload form with:

* `month`, `pension_plan`, and file fields
* **Live progress bar** using `XMLHttpRequest.upload.onprogress`
* Automatic status messages for:

  * "Uploading…"
  * "Processing…"
  * ✅ Success or ❌ Error

No frontend framework or JavaScript build tooling is required. The form is rendered via Jinja templates and works natively in modern browsers.

---

### 📈 Usage in Power BI

The `ICE_CUBE_RECON_PERS` and `ICE_CUBE_RECON_STRS` tables feed into a Power BI report, highlighting:

* Missing or misaligned contribution amounts
* Unexpected earning codes
* Unusual rates or check dates
* Unmatched employee IDs

This enables payroll staff to:

* Focus on anomalies only
* Correct issues in Ice Cube
* Re-export and re-ingest files as needed

---

### 🔒 Security & Secrets

* Database credentials are stored in `.env` and **not committed**
* Docker image builds exclude sensitive config
* Uploads are in-memory; no files are written to disk

---

### ✅ Project Features & TODOs

* [x] Auto-refresh payroll on initial load
* [x] Skip payroll staging load if data already exists for that period
* [x] Add `recon_period` (month-year) column to support overwrite logic
* [x] Replace Appsmith with friendly in-browser HTMX UI
* [x] Add real-time progress bar and status messaging
* [ ] Optional: background processing or queuing for heavy files
* [ ] Optional: anomaly scoring via ML heuristics

---
