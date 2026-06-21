# DrugDisease.FastApi

FastAPI backend for the DataThuoc schema. The app runs with three parts:

```text
frontend/ React
  -> http://localhost:8000/api
backend/DrugDisease.FastApi/ FastAPI business API
  -> SQL Server DataThuoc
  -> http://localhost:8001 AI service
ai/ FastAPI AI service + RandomForest model
```

## Environment

Create `backend/DrugDisease.FastApi/.env` from `.env.example` and set:

```env
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=LALISAMANOBAN\SQLEXPRESS02
DB_SERVER_FALLBACKS=.\SQLEXPRESS02,(local)\SQLEXPRESS02,localhost\SQLEXPRESS02
DB_NAME=DataThuoc
DB_TRUSTED_CONNECTION=yes
DB_ENCRYPT=no
DB_TRUST_SERVER_CERTIFICATE=yes
DB_CONNECTION_TIMEOUT=5
JWT_SECRET_KEY=CHANGE_THIS_SECRET_FOR_DEVELOPMENT_ONLY
AI_SERVICE_URL=http://localhost:8001
```

The backend builds the SQLAlchemy URL with `odbc_connect`, so SQL Server instance names are passed through the ODBC connection string instead of a raw URL.

`AI_SERVICE_BASE_URL` is still accepted for compatibility, but `AI_SERVICE_URL` is preferred.

## Install AI

From the repository root:

```bash
cd ai
pip install -r requirements.txt
```

Train/retrain when needed from the repository root:

```bash
python -m ai.src.train_random_forest --config ai/config/random_forest.json
```

Run AI service from the repository root:

```bash
uvicorn ai.src.api:app --host 0.0.0.0 --port 8001 --reload
```

AI checks:

```bash
curl http://localhost:8001/health
curl -X POST http://localhost:8001/predict/batch ^
  -H "Content-Type: application/json" ^
  -d "{\"items\":[{\"thuocId\":1,\"benhId\":1,\"maThuoc\":\"\",\"maBenh\":\"\",\"tenThuoc\":\"Test\",\"tenBenh\":\"Test\"}]}"
```

If the model file is missing or cannot load, `/health` returns `modelLoaded: false` instead of crashing.

## Install Backend

```bash
cd backend/DrugDisease.FastApi
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger:

```text
http://localhost:8000/docs
```

Database connection check:

```bash
python scripts/test_db_connection.py
```

## Main API Routes

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
GET  /api/admin/access-check

GET  /api/thuoc
GET  /api/thuoc/{id}
GET  /api/benh
GET  /api/benh/{id}
GET  /api/lien-ket-thuoc-benh
GET  /api/lien-ket-thuoc-benh/theo-thuoc/{thuocId}
GET  /api/lien-ket-thuoc-benh/theo-benh/{benhId}
GET  /api/lookups

POST /api/du-doan
GET  /api/du-doan/lich-su
GET  /api/du-doan/{id}
POST /api/phan-hoi-ket-qua

GET    /api/admin/dashboard
GET    /api/admin/links
POST   /api/admin/links
PUT    /api/admin/links/{link_id}
DELETE /api/admin/links/{link_id}
GET    /api/du-doan/admin/lich-su
GET    /api/model/info
```

Prediction flow now sends candidate pairs to `POST /predict/batch` on the AI service first. If AI is unavailable, the backend falls back to `LienKetThuocBenh.DiemLienKet` and returns `nguonDiem = DATABASE_FALLBACK` plus a warning.

## Frontend

Create `frontend/.env` when you do not use the Vite proxy:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Run:

```bash
cd frontend
npm install
npm run dev
```

## Quick Test

1. `GET http://localhost:8001/health`
2. `POST http://localhost:8001/predict/batch`
3. `GET http://localhost:8000/api/health`
4. `POST http://localhost:8000/api/auth/login` with admin / 123456 if that account is seeded
5. `GET http://localhost:8000/api/thuoc?page=1&pageSize=12`
6. `GET http://localhost:8000/api/benh?page=1&pageSize=12`
7. `GET http://localhost:8000/api/lien-ket-thuoc-benh/theo-thuoc/1`
8. `POST http://localhost:8000/api/du-doan`
9. Open the frontend drug list, verify drug images/placeholders, submit prediction, and verify `AI_MODEL` or `DATABASE_FALLBACK` is shown.
