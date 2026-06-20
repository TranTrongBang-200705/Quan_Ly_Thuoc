# Train RandomForest cho du doan lien ket thuoc - benh

Thu muc nay dung de train model AI rieng cho he thong, tach khoi frontend va backend.

## Nguon du lieu

Script doc du lieu tu SQL Server database `DataThuoc`.

Bang du lieu chinh:

- `dbo.Thuoc`: danh sach thuoc.
- `dbo.Benh`: danh sach benh/chi dinh.
- `dbo.LienKetThuocBenh`: lien ket thuoc - benh da biet.

Label:

- `LabelValue = 1`: cap thuoc - benh co trong `LienKetThuocBenh`.
- `LabelValue = 0`: cap thuoc - benh chua co lien ket, duoc tao tu cung thuoc voi mot benh khac chua lien ket.

Dataset duoc chia bang stratified split:

- `TRAIN`: train RandomForest.
- `VALIDATION`: danh gia trong qua trinh chon tham so.
- `TEST`: danh gia cuoi cung.

Stratified split dam bao train/validation/test deu co ca 2 lop `0` va `1`.

## Thuat toan RandomForest

RandomForest la tap hop nhieu cay quyet dinh. Moi cay duoc train tren mau bootstrap cua tap train va tai moi node chi xem mot tap con dac trung.

Cong thuc Gini impurity khi `criterion = "gini"`:

```text
Gini(t) = 1 - sum(p_k^2)
```

Trong do `p_k` la ty le mau thuoc lop `k` tai node `t`.

Do giam impurity cua mot split:

```text
Gain = Impurity(parent)
       - (N_left / N_parent) * Impurity(left)
       - (N_right / N_parent) * Impurity(right)
```

RandomForest classification tong hop ket qua bang voting/xac suat trung binh tu cac cay:

```text
P(class=1) = trung_binh(P_tree_i(class=1))
```

Trong code, model duoc tao bang `sklearn.ensemble.RandomForestClassifier`.
Pipeline train gom:

1. Tao feature dang dictionary tu tung cap thuoc - benh.
2. Ma hoa feature bang `DictVectorizer`.
3. Train `RandomForestClassifier`.
4. Tinh metric tren validation/test bang nhan that va nhan du doan.

## Tham so dang dung

Xem file `ai/config/random_forest.json`:

- `n_estimators`: so cay trong forest.
- `criterion`: cong thuc tinh impurity, dang dung `gini`.
- `max_depth`: do sau toi da cua cay.
- `min_samples_split`: so mau toi thieu de tach node.
- `min_samples_leaf`: so mau toi thieu o leaf.
- `max_features`: so dac trung duoc can nhac moi lan split.
- `bootstrap`: co lay mau bootstrap cho tung cay hay khong.
- `class_weight`: can bang trong so lop.
- `random_state`: seed de tai lap ket qua.
- `n_jobs`: so luong CPU job, dang de `-1` de dung toi da CPU kha dung.

## Chong data leakage

Script mac dinh bat `loai_bo_dac_trung_ro_ri_nhan = true`.

Khong dua vao model cac cot chi ton tai sau khi da biet link, vi chung lam metric dep gia:

- `SourceScore`
- `LinkTypeCode`
- `ConfidenceLevelCode`
- `label_source`
- `matched_keyword`
- `evidence_field`
- `source`

Nhung cot nay co the dung de audit/bao cao, nhung khong nen dung lam feature train cho bai toan du doan link moi.

## Cach chay

```powershell
python -m ai.src.train_random_forest --config ai/config/random_forest.json
```

Ket qua:

- Model: `ai/models/random_forest_thuoc_benh.joblib`
- Metrics: `ai/reports/bao_cao_random_forest.json`
- Feature importance: `ai/reports/do_quan_trong_dac_trung.csv`

## Tich hop backend sau nay

Backend moi chi can load file model `.joblib` va tao feature cung schema:

- `drug_id`
- `disease_id`
- `drug_code`
- `disease_code`
- `drug_group_id`
- `route_id`
- `disease_group_id`
- `do_dai_ten_thuoc`
- `do_dai_ten_benh`

Sau do goi:

```python
xac_suat = mo_hinh.predict_proba([dac_trung])[0][positive_index]
nhan_du_doan = mo_hinh.predict([dac_trung])[0]
```
