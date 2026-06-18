Thanh vien nhom: Bang, My, Khoa, Hieu

Frontend DrugDiseaseML

Source React/Vite nam trong thu muc src va bam theo cac API backend hien co:

- GET /api/drugs
- GET /api/diseases
- GET /api/links
- GET /api/lookups
- POST /api/predictions
- GET /api/predictions/history
- POST /api/feedbacks

User workspace:

- Tra cuu thuoc
- Tra cuu benh
- Xem lien ket thuoc - benh da biet
- Gui yeu cau du doan
- Xem lich su du doan
- Gui feedback

Admin workspace theo backend hien co:

- Dashboard giam sat du lieu
- Catalog monitor cho Drugs va Diseases
- Known link monitor
- Prediction request monitor
- System lookup monitor

Luu y: backend hien chua co API add/update/delete, approve, deploy model, audit log.
Vi vay cac man hinh admin hien tai la read-only/monitoring.

Chay frontend:

1. Mac dinh frontend goi backend tai https://localhost:7001/api

2. Neu backend dung cong khac, tao file .env.local:

   VITE_API_BASE_URL=https://localhost:7001/api

3. Chay app:

   npm run dev

Build production:

   npm run build
