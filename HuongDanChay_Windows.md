# Huong dan chay project tren Windows PowerShell

Project nay nen chay bang Python 3.11 hoac Python 3.12 tren Windows.
Khong dung Python 3.14 cho project nay, vi mot so package native co the chua co wheel phu hop voi version dependency dang dung va se bi fallback sang build tu source.

## Kiem tra Python dang co

Chay:

```powershell
py -0p
```

Neu co ca Python 3.11 va 3.12, uu tien Python 3.11 cho backend va AI. Neu muon dung Python 3.12, thay `py -3.11` bang `py -3.12` trong cac lenh ben duoi.

## Backend

Thu muc backend:

```powershell
cd D:\DrugDisease.FastApi.BE-only\Quan_Ly_Thuoc_FAST\backend\DrugDisease.FastApi
```

Tao virtual environment:

```powershell
py -3.11 -m venv .venv-be
```

Kich hoat virtual environment:

```powershell
.\.venv-be\Scripts\Activate.ps1
```

Trong PowerShell khong chay `Scripts\activate`. Lenh do danh cho cmd.exe. Hay dung dung file `Activate.ps1` nhu tren.

Neu PowerShell chan script, chay mot lan:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Cap nhat pip va cai dependency:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Neu chua co file `.env`, tao tu file mau:

```powershell
copy .env.example .env
```

Kiem tra lai `DATABASE_URL`, `AI_SERVICE_URL`, `JWT_SECRET_KEY` trong `.env`.

Kiem tra SQL Server instance dang chay:

```powershell
Get-Service | Where-Object { $_.Name -like '*SQL*' -or $_.DisplayName -like '*SQL*' } | Select-Object Name,DisplayName,Status
```

Tren may hien tai instance dang chay la `SQLEXPRESS02`, nen `.env` dang dung:

```env
DATABASE_URL=mssql+pyodbc://@localhost\SQLEXPRESS02/DataThuoc?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&Encrypt=no&TrustServerCertificate=yes
```

Chay backend:

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger:

```text
http://localhost:8000/docs
```

## AI service

Vao root project:

```powershell
cd D:\DrugDisease.FastApi.BE-only\Quan_Ly_Thuoc_FAST
```

Tao virtual environment rieng cho AI:

```powershell
py -3.11 -m venv .venv-ai
```

Kich hoat:

```powershell
.\.venv-ai\Scripts\Activate.ps1
```

Cai dependency:

```powershell
python -m pip install --upgrade pip
python -m pip install -r ai\requirements.txt
```

Chay AI API:

```powershell
python -m uvicorn ai.src.api:app --host 0.0.0.0 --port 8001 --reload
```

Kiem tra health:

```powershell
curl http://localhost:8001/health
```

Train lai model neu can:

```powershell
python -m ai.src.train_random_forest --config ai/config/random_forest.json
```

## Frontend

Vao thu muc frontend:

```powershell
cd D:\DrugDisease.FastApi.BE-only\Quan_Ly_Thuoc_FAST\frontend
```

Tao file `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Cai package va chay dev server:

```powershell
npm install
npm run dev
```

Neu PowerShell bao `npm.ps1 cannot be loaded because running scripts is disabled`, chay mot lan:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Sau do dong mo lai PowerShell, hoac chay tam bang file `.cmd`:

```powershell
npm.cmd install
npm.cmd run dev
```

## Ghi chu loi thuong gap

Neu gap `No module named uvicorn`, thuong la do chua kich hoat dung virtual environment hoac chua cai `requirements.txt` trong virtual environment do. Hay chay backend bang `python -m uvicorn ...` sau khi da activate `.venv-be`.

Neu pip bao `Microsoft Visual C++ 14.0 or greater is required` hoac `link.exe not found`, pip dang phai build package native tu source. Cach on dinh hon tren Windows la dung Python 3.11/3.12 va dependency trong file `requirements.txt` da cap nhat de pip lay binary wheel thay vi build.

Neu SQL Server bao `No credentials are available in the security package` hoac `Encryption not supported on the client`, hay mo SQL Server Configuration Manager va kiem tra:

- Instance dang dung co phai `SQLEXPRESS02` khong.
- SQL Server Network Configuration cua instance da bat protocol can dung.
- SQL Server co dang ep encryption/certificate khong.
- Tai khoan Windows hien tai co quyen connect vao database `DataThuoc` khong.
