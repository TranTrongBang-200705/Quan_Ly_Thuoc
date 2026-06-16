Thanh vien nhom: Bang, My, Khoa, Hieu

Du doan lien ket thuoc - benh bang RandomForest

1. Cai dat thu vien

   pip install -r requirements.txt

2. Train model

   python -m src.train_random_forest --config config/random_forest.yaml

3. Du doan lien ket moi

   python -m src.predict_link --drug-class Antidiabetic --disease-group Endocrine --mechanism-overlap 0.9 --clinical-evidence 0.88

Ket qua train se luu model vao thu muc models va metric vao thu muc reports.
