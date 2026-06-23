# Deploy free hosting

Kien truc khuyen nghi:

- Frontend React: Vercel hoac Render Static Site.
- Backend FastAPI: Render Web Service, Dockerfile `Dockerfile.backend`.
- AI FastAPI: Render Web Service, Dockerfile `Dockerfile.ai`.
- Database: PostgreSQL free (Neon/Supabase) for no-card deployment, or Azure SQL if you have a payment card.

## 1. Dua source len GitHub

Render/Vercel deploy de nhat tu GitHub. Tren branch `deploy-free-hosting`, noi dung cua `Quan_Ly_Thuoc_RunTest` da nam ngay tai root repo.

## 2. Tao PostgreSQL database free

Neu khong co the Visa/Mastercard, dung Neon hoac Supabase PostgreSQL la huong an toan nhat. Cach nay khong dung database SQL Server local cua ban, chi import ban sao du lieu.

Backend da ho tro `DATABASE_URL` PostgreSQL. Local SQL Server van chay nhu cu neu khong set `DATABASE_URL`.

### Tao schema va import data

Sau khi co PostgreSQL connection string, chay tren may local:

```powershell
cd Quan_Ly_Thuoc_RunTest
$env:DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require"
python scripts/create_tables.py
python scripts/create_postgres_seed.py
python scripts/load_postgres_seed.py
```

Script tren se tao bang, tao `database/postgres_seed.sql`, roi nap seed vao PostgreSQL.

## 3. Deploy AI service len Render

Create Web Service:

- Environment: Docker
- Root Directory: de trong
- Dockerfile Path: `Dockerfile.ai`
- Health check path: `/health`

Environment variables:

```env
AI_MODEL_PATH=/app/ai/models/random_forest_thuoc_benh.joblib
AI_MODEL_CONFIG_PATH=/app/ai/config/random_forest.json
AI_MODEL_VERSION=random-forest-datathuoc-1.0.0
AI_MODEL_N_JOBS=1
```

Sau khi deploy, copy URL dang `https://...onrender.com`.

## 4. Deploy backend len Render

Create Web Service:

- Environment: Docker
- Root Directory: de trong
- Dockerfile Path: `Dockerfile.backend`
- Health check path: `/api/health`

Environment variables:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
JWT_SECRET_KEY=replace_with_a_long_random_secret
AI_SERVICE_URL=https://your-ai-service.onrender.com
CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://your-frontend-domain.onrender.com
```

## 5. Deploy frontend

### Vercel

- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment variable:

```env
VITE_API_BASE_URL=https://your-backend-service.onrender.com/api
```

### Render Static Site

- Root Directory: `frontend`
- Build Command: `npm ci && npm run build`
- Publish Directory: `dist`
- Environment variable:

```env
VITE_API_BASE_URL=https://your-backend-service.onrender.com/api
```

## Free-tier luu y

- Render Free Web Service sleep sau mot thoi gian khong co request, nen request dau tien co the cham.
- AI service co model `.joblib`; neu Render free bi crash do RAM, can giam model hoac gop AI vao backend de bot mot service.
- Khong commit `.env` that hoac password len GitHub.
