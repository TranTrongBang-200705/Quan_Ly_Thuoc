# Train RandomForest cho du doan lien ket thuoc - benh

Thu muc nay dung de train model AI rieng cho he thong, tach khoi frontend va backend.

## Nguon du lieu

Script doc du lieu tu SQL Server database `DataThuoc`.

Bang du lieu chinh:

- `dbo.Thuoc`: danh sach thuoc.
- `dbo.Benh`: danh sach benh/chi dinh.
- `dbo.LienKetThuocBenh`: lien ket thuoc - benh da biet.

Kiem tra database hien tai:

- `LienKetThuocBenh` co 11,825 dong.
- Moi thuoc hien co dung 1 lien ket trong `LienKetThuocBenh`.
- 11,825/11,825 lien ket co `Thuoc.CongDung` trung voi `Benh.TenBenh`.
- `Benh.TrieuChung` hien dang rong toan bo, nen feature trieu chung chi duoc giu san cho khi database co du lieu.

Vi `Benh.TenBenh` duoc suy ra tu `Thuoc.CongDung`, model hien tai nen duoc hieu la model so khop chi dinh/cong dung trong database, khong phai model y khoa tong quat.

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
2. Tao feature text tu cac cot co san trong database: `HoatChat`, `CongDung`, `TacDungPhu`, `TenBenh`, `MoTa`, `TrieuChung`, `ThuocDieuTriDaBiet`.
3. Tinh cac chi so so khop text nhu so tu chung va ti le tu chung giua `CongDung` va `TenBenh`.
4. Ma hoa feature bang `DictVectorizer`.
5. Train `RandomForestClassifier`.
6. Tinh metric tren validation/test bang nhan that va nhan du doan.

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

Luu y: `CongDung` va `TenBenh` khong phai cot ro ri nhan theo nghia database sau-du-doan, vi backend co the co san cong dung thuoc va ten benh ung vien. Tuy nhien trong dataset hien tai `TenBenh` duoc sinh truc tiep tu `CongDung`, nen metric se rat cao va can duoc giai thich ro trong bao cao.

## Ket qua hien tai

Ket qua sau khi train lai bang cac cot co san trong database:

- Tong mau: 23,650.
- Mau duong: 11,825.
- Mau am: 11,825.
- Validation F1: 0.9980.
- Test F1: 0.9972.
- Test ROC-AUC: 1.0000.

Ket qua cao bat thuong vi `Benh.TenBenh` cua lien ket duong trung voi `Thuoc.CongDung`. Neu sau nay database co benh doc lap, trieu chung that, mo ta benh chi tiet hon, metric se phan anh thuc te hon.

## Cach chay

```powershell
python -m ai.src.train_random_forest --config ai/config/random_forest.json
```

Ket qua:

- Model: `ai/models/random_forest_thuoc_benh.joblib`
- Metrics: `ai/reports/bao_cao_random_forest.json`
- Feature importance: `ai/reports/do_quan_trong_dac_trung.csv`

## Test case du doan

Dung script sau de tao cac case test xem xac suat du doan co khop voi nhan trong dataset khong:

```powershell
python -m ai.src.test_random_forest_cases --config ai/config/random_forest.json --so-case-moi-nhom 8
```

Script se tao cac nhom:

- `duong_ngau_nhien_da_biet_lien_ket`: cap co lien ket that trong database.
- `am_ngau_nhien_chua_co_lien_ket`: cap chua co lien ket.
- `duong_diem_cao_nhat`: cac mau duong model tu tin nhat.
- `am_diem_thap_nhat`: cac mau am model tu tin nhat.
- `duong_de_nham_nhat_diem_thap`: mau duong kho, model cho diem thap.
- `am_de_nham_nhat_diem_cao`: mau am kho, model cho diem cao.

Ket qua duoc ghi vao:

- `ai/reports/test_cases_random_forest.csv`
- `ai/reports/test_cases_random_forest.json`

Hai nhom `*_de_nham_nhat_*` la test bien co chu dich lay cac case kho nhat, nen co the sai nhieu hon cac nhom ngau nhien.

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
- `HoatChat`
- `CongDung`
- `TacDungPhu`
- `MoTaBenh`
- `TrieuChung`
- `ThuocDieuTriDaBiet`

Sau do goi:

```python
xac_suat = mo_hinh.predict_proba([dac_trung])[0][positive_index]
nhan_du_doan = mo_hinh.predict([dac_trung])[0]
```
