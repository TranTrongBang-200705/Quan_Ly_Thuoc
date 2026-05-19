# Tạo bệnh phổ biến và liên kết thuốc - bệnh cục bộ

Pipeline này không gọi API bên ngoài và không truy cập internet. Dữ liệu đầu vào chỉ gồm dữ liệu thuốc đã restore/import sẵn trong SQL Server và file seed cục bộ `data/seed/common_vietnam_diseases.csv`.

## Mục tiêu

- Seed danh sách bệnh phổ biến hoặc liên quan tại Việt Nam vào `dbo.Diseases`.
- Thêm synonym tiếng Việt và tiếng Anh vào `dbo.DiseaseSynonyms`.
- Thêm mã ICD-10 vào `dbo.DiseaseExternalCodes` khi có trong seed.
- Tạo liên kết thuốc - bệnh chỉ khi keyword của bệnh xuất hiện trong text đã có sẵn trong database.
- Lưu bằng chứng vào `dbo.LinkEvidenceReferences` để biết match đến từ field nào và keyword nào.
- Đánh dấu liên kết tự động là cần xem lại hoặc chờ kiểm duyệt.
- Tạo nhãn huấn luyện demo cho module ML.

## Quy tắc an toàn dữ liệu y khoa

Script không tự bịa claim y khoa. Một liên kết thuốc - bệnh chỉ được tạo khi keyword bệnh xuất hiện trong text hiện có của thuốc như:

- `Drugs.KnownIndications`
- `Drugs.ContraindicationsInteractions`
- `Drugs.SideEffectsWarnings`
- `Drugs.MechanismOfAction`

Liên kết từ `KnownIndications` được dùng làm nhãn dương tính demo cho bài toán điều trị. Liên kết từ chống chỉ định hoặc tác dụng phụ không được xem là nhãn điều trị dương tính.

Các mẫu âm hoặc unknown chỉ phục vụ demo ML. Chúng không phải là bằng chứng y khoa rằng thuốc không liên quan hoặc không điều trị bệnh đó.

Toàn bộ pipeline dùng cho học tập và nghiên cứu. Không dùng kết quả này làm lời khuyên y tế hoặc thay thế bác sĩ dược sĩ.

## Chạy pipeline

Từ thư mục project:

```powershell
python etl/import_common_diseases_local.py
python etl/generate_drug_disease_links_local.py
python etl/create_training_labels_from_links.py
```

`generate_drug_disease_links_local.py` cũng gọi phần tạo nhãn sau khi tạo link. Lệnh `create_training_labels_from_links.py` vẫn có thể chạy riêng và idempotent nên không tạo trùng dữ liệu.

## Kiểm tra dữ liệu

```powershell
sqlcmd -S localhost\SQLEXPRESS -d DrugDiseaseML_DB -E -i database\check_drug_disease_training_data.sql
```

Report sẽ hiển thị tổng số thuốc bệnh synonym liên kết theo loại bằng chứng nhãn huấn luyện top link được tạo bệnh chưa có thuốc liên kết và thuốc chưa có bệnh liên kết.

## Ghi chú vận hành

- Nếu số thuốc active nhỏ hơn 10 script tạo link sẽ dừng với thông báo cần restore/import dữ liệu thuốc trước.
- Nếu số bệnh active nhỏ hơn 10 hãy chạy `python etl/import_common_diseases_local.py` trước.
- Script không xóa dữ liệu hiện có.
- Script không ghi đè dữ liệu chuyên gia đã review.
- Các dòng tạo tự động dùng source `EXISTING_DRUG_LABEL_TEXT` và user hệ thống `system@drug-disease-ml.local`.

## Hỗ trợ tên bệnh tiếng Việt

Schema hiện tại chỉ có `dbo.Diseases.DiseaseName`, không có cột riêng cho tiếng Việt và tiếng Anh. Vì vậy pipeline lưu tên bệnh tiếng Việt làm tên hiển thị chính để phục vụ UI và tìm kiếm tiếng Việt.

Tên tiếng Anh và keyword tiếng Anh vẫn được lưu trong `dbo.DiseaseSynonyms` với `LanguageCode = 'en'` để match với drug label text đã import, vì phần lớn label text là tiếng Anh. Tên tiếng Việt và keyword tiếng Việt được lưu với `LanguageCode = 'vi'`.

Backend có thể hỗ trợ tìm kiếm tiếng Việt bằng cách search trên `dbo.Diseases.DiseaseName` và `dbo.DiseaseSynonyms.SynonymName`.
