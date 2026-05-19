# Khai thác thêm bệnh từ dữ liệu thuốc đã có

Pipeline này không gọi API bên ngoài và không truy cập internet. Nguồn dữ liệu duy nhất là text thuốc đã có sẵn trong SQL Server `DrugDiseaseML_DB`, đặc biệt các field của `dbo.Drugs` như `KnownIndications`, `ContraindicationsInteractions`, `SideEffectsWarnings`, và `MechanismOfAction`.

## Luồng xử lý

1. Script extract đọc dữ liệu thuốc trong SQL Server và tìm cụm từ có vẻ là bệnh hoặc tình trạng y khoa.
2. Kết quả được ghi ra CSV `data/seed/candidate_diseases_from_drugs.csv`.
3. Người dùng review CSV thủ công.
4. Chỉ những dòng có `Action = APPROVED` hoặc `Action = IMPORT` mới được import vào database.
5. Script tạo link chỉ tạo `DrugDiseaseLinks` khi text thuốc hiện có chứa keyword bệnh.
6. Link tự động được đánh dấu `AUTO_EXTRACTED` và `NEED_REVIEW`.

## Nguyên tắc an toàn

- Không bịa claim y khoa.
- Không tạo liên kết thuốc - bệnh nếu không có evidence text trong database.
- Candidate disease phải qua CSV review trước khi import.
- Link từ `KnownIndications` có thể tạo nhãn dương tính demo cho ML.
- Link từ chống chỉ định hoặc tác dụng phụ không phải nhãn điều trị dương tính.
- Mẫu âm hoặc unknown chỉ là dữ liệu demo, không phải bằng chứng y khoa thuốc không điều trị bệnh.
- Pipeline dùng cho học tập và nghiên cứu, không phải lời khuyên y tế.

## Bước 1: Extract candidate diseases

```powershell
python etl/extract_candidate_diseases_from_drug_text.py --min-evidence 2
```

Script sẽ tạo:

```text
data/seed/candidate_diseases_from_drugs.csv
```

Các dòng mặc định có `Action = NEED_REVIEW` nên chưa được import.

Script dùng thêm từ điển cục bộ:

```text
data/seed/disease_vietnamese_dictionary.csv
```

Nếu candidate tiếng Anh có mapping trong file này, script sẽ tự điền `CandidateDiseaseNameVi` và `SuggestedGroupCode`. Không có API dịch hoặc internet nào được gọi.

## Bước 2: Review thủ công

Mở file:

```text
data/seed/candidate_diseases_from_drugs.csv
```

Kiểm tra các cột disease name evidence count sample drug evidence snippet. Với dòng muốn import, đổi:

```text
Action
```

từ:

```text
NEED_REVIEW
```

thành:

```text
APPROVED
```

hoặc:

```text
IMPORT
```

## Bước 3: Import candidate diseases đã duyệt

```powershell
python etl/import_candidate_diseases_local.py
```

Script sẽ import vào `dbo.Diseases`, thêm synonyms, source `LOCAL_DRUG_TEXT_MINING`, và metadata feature nếu schema hỗ trợ. Script idempotent và không xóa dữ liệu cũ.

Vì schema hiện tại chỉ có `dbo.Diseases.DiseaseName`, importer ưu tiên lưu tên tiếng Việt làm tên hiển thị chính cho UI/search. Tên tiếng Anh được lưu làm synonym `LanguageCode = 'en'`; tên và keyword tiếng Việt từ dictionary được lưu làm synonym `LanguageCode = 'vi'`.

## Bước 4: Tạo links và labels

```powershell
python etl/generate_drug_disease_links_local.py
python etl/create_training_labels_from_links.py
```

`generate_drug_disease_links_local.py` match tất cả bệnh active trong `dbo.Diseases`, bao gồm bệnh mới import từ mining. Link chỉ được tạo khi có keyword xuất hiện trong text thuốc đang lưu trong SQL Server.

## Kiểm tra

```powershell
sqlcmd -S localhost\SQLEXPRESS -d DrugDiseaseML_DB -E -i database\check_candidate_diseases_and_links.sql
```

Report sẽ hiển thị tổng số bệnh, tổng candidate disease đã import, tổng link, link theo loại, training label theo giá trị, top bệnh mới từ drug text, top link mới có evidence snippet, bệnh chưa có thuốc liên kết và thuốc chưa có bệnh liên kết.

Backend có thể hỗ trợ tìm kiếm tiếng Việt bằng cách query cả `dbo.Diseases.DiseaseName` và `dbo.DiseaseSynonyms.SynonymName`. Matching với drug label text vẫn dựa nhiều vào keyword tiếng Anh vì dữ liệu nhãn thuốc đã import thường là tiếng Anh.
