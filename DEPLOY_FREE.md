# Deploy free hosting

Kien truc khuyen nghi:

- Frontend React: Vercel hoac Render Static Site.
- Backend FastAPI: Render Web Service, Dockerfile `Dockerfile.backend`.
- AI FastAPI: Render Web Service, Dockerfile `Dockerfile.ai`.
- SQL Server database: Azure SQL Database free offer.

## 1. Dua source len GitHub

Render/Vercel deploy de nhat tu GitHub. Thu muc goc nen la `Quan_Ly_Thuoc_RunTest`.

## 2. Tao Azure SQL Database free

Tao database free tren Azure SQL, sau do import du lieu DataThuoc.

Neu ban dang co file `.bak`, Azure SQL Database khong import truc tiep `.bak`. Nen dung mot trong hai cach:

- Export database local thanh `.bacpac`, roi Import vao Azure SQL.
- Chay script `.sql` trong `database/` neu script da day du schema + data.

Khi tao xong, mo firewall cua Azure SQL cho Render outbound IP hoac tam thoi Allow Azure services/your IP de test.

## 3. Deploy AI service len Render

Create Web Service:

- Environment: Docker
- Root Directory: `Quan_Ly_Thuoc_RunTest`
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
- Root Directory: `Quan_Ly_Thuoc_RunTest`
- Dockerfile Path: `Dockerfile.backend`
- Health check path: `/api/health`

Environment variables:

```env
ENVIRONMENT=production
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_SERVER=your-sql-server.database.windows.net
DB_NAME=DataThuoc
DB_USERNAME=your_sql_admin_user
DB_PASSWORD=your_sql_admin_password
DB_ENCRYPT=yes
DB_TRUST_SERVER_CERTIFICATE=no
DB_CONNECTION_TIMEOUT=30
JWT_SECRET_KEY=replace_with_a_long_random_secret
AI_SERVICE_URL=https://your-ai-service.onrender.com
CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://your-frontend-domain.onrender.com
```

## 5. Deploy frontend

### Vercel

- Root Directory: `Quan_Ly_Thuoc_RunTest/frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment variable:

```env
VITE_API_BASE_URL=https://your-backend-service.onrender.com/api
```

### Render Static Site

- Root Directory: `Quan_Ly_Thuoc_RunTest/frontend`
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
