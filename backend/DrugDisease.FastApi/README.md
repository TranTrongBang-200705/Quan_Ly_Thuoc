# DrugDisease.FastApi

Backend nghiệp vụ FastAPI thay cho `backend/DrugDisease.Api` ASP.NET Core.

Thư mục này **chỉ là BE mới**. Không chứa frontend và không sửa module AI.

## Kiến trúc chạy

```text
frontend/ React
  -> http://localhost:8000/api
backend/DrugDisease.FastApi/ FastAPI nghiệp vụ
  -> SQL Server
  -> http://localhost:8001 AI service
ai/ FastAPI AI service + Random Forest model
```

## Không đụng module AI

AI vẫn chạy từ thư mục repo gốc:

```bash
uvicorn ai.src.api:app --host 0.0.0.0 --port 8001
```

Backend mới gọi AI qua biến:

```env
AI_SERVICE_BASE_URL=http://localhost:8001
```

## Cách đặt folder vào repo

Trong repo `Quan_Ly_Thuoc`, đặt folder này vào:

```text
backend/DrugDisease.FastApi/
```

Cấu trúc cuối:

```text
Quan_Ly_Thuoc/
  frontend/
  ai/
  backend/
    DrugDisease.Api/        # ASP.NET cũ, có thể giữ để đối chiếu
    DrugDisease.FastApi/    # BE mới
```

## Cài đặt

```bash
cd backend/DrugDisease.FastApi
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Sửa `.env` cho đúng SQL Server của máy.

## Chạy AI service

Tại thư mục gốc repo:

```bash
pip install -r ai/requirements.txt
uvicorn ai.src.api:app --host 0.0.0.0 --port 8001
```

Test:

```bash
curl http://localhost:8001/health
```

## Chạy backend FastAPI

```bash
cd backend/DrugDisease.FastApi
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger:

```text
http://localhost:8000/docs
```

Health:

```bash
curl http://localhost:8000/api/health
```

## Cho frontend gọi BE mới

Cách ít sửa nhất: tạo file `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Hoặc sửa `frontend/vite.config.js` proxy `/api` từ `http://localhost:5218` sang `http://localhost:8000`.

## Endpoint tương thích frontend hiện tại

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
GET  /api/admin/access-check

GET  /api/drugs
GET  /api/diseases
GET  /api/links
GET  /api/lookups

POST /api/predictions
GET  /api/predictions/{request_id}
GET  /api/predictions/history
GET  /api/predictions/admin/history

POST /api/feedbacks

GET    /api/admin/dashboard
GET    /api/admin/links
POST   /api/admin/links
PUT    /api/admin/links/{link_id}
DELETE /api/admin/links/{link_id}

GET /api/model/info
```

## Ghi chú quan trọng

- BE mới giữ prefix `/api` để frontend ít sửa.
- BE mới không load model `.joblib` trực tiếp.
- BE mới gọi AI service qua HTTP.
- Bảng có trigger đã đặt `implicit_returning=False` để giảm lỗi kiểu SQL Server trigger + OUTPUT clause.
- Nếu token cũ từ ASP.NET không dùng được, hãy đăng xuất rồi đăng nhập lại bằng BE mới.
- Nếu đăng nhập bằng tài khoản cũ lỗi, kiểm tra `JWT_SECRET_KEY` và hash mật khẩu. Mật khẩu BCrypt cũ của ASP.NET thường tương thích với `passlib[bcrypt]`.

## Test nhanh

1. `GET http://localhost:8001/health`
2. `GET http://localhost:8000/api/health`
3. `POST http://localhost:8000/api/auth/login`
4. `GET http://localhost:8000/api/drugs`
5. `GET http://localhost:8000/api/diseases`
6. `GET http://localhost:8000/api/lookups`
7. `POST http://localhost:8000/api/predictions`

## Những phần giữ nguyên so với ASP.NET cũ

- Auth JWT, USER/ADMIN.
- Tra cứu thuốc, bệnh.
- Tra cứu liên kết đã biết.
- Admin thêm/sửa/xóa mềm liên kết thuốc - bệnh.
- Dự đoán 3 kiểu: `DRUG_TO_DISEASE`, `DISEASE_TO_DRUG`, `PAIR_PREDICTION`.
- Lịch sử user và lịch sử admin.
- Feedback.
- Gọi AI service `/predict/batch`.
