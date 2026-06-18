# Train RandomForest cho du doan lien ket thuoc - benh

Thu muc nay dung de train model AI rieng cho he thong, tach khoi frontend va backend.

## Nguon du lieu

Script doc du lieu tu SQL Server database `DrugDiseaseML_DB_check`, bang `dbo.DatasetItems`, join them `dbo.Drugs`, `dbo.Diseases`, va `dbo.DrugDiseaseLinks`.

Label:

- `LabelValue = 1`: co lien ket thuoc - benh.
- `LabelValue = 0`: mau am/unknown negative.

Split trong database hien tai:

- `TRAIN`: train RandomForest.
- `VALIDATION`: danh gia trong qua trinh chon tham so.
- `TEST`: danh gia cuoi cung.

Neu split trong database khong can bang label, script se dung stratified split moi theo `LabelValue` de dam bao train/validation/test deu co ca 2 lop.

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
