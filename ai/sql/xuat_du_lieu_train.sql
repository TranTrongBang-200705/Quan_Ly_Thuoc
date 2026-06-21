SET NOCOUNT ON;

DECLARE @MaxBenhId int = (
    SELECT MAX(BenhId)
    FROM dbo.Benh
);

WITH MauDuong AS
(
    SELECT
        lk.LienKetId AS DatasetItemId,
        lk.ThuocId AS DrugId,
        lk.BenhId AS DiseaseId,
        CAST(1 AS int) AS LabelValue,
        N'ALL' AS SplitName,
        N'{}' AS FeatureVectorJson,
        COALESCE(t.MaThuoc, N'') AS DrugCode,
        COALESCE(t.TenThuoc, N'') AS ActiveName,
        COALESCE(t.TenThuocGoc, N'') AS TradeName,
        COALESCE(CAST(t.NhomThuocId AS nvarchar(30)), N'') AS DrugGroupId,
        N'' AS RouteId,
        COALESCE(CAST(b.NhomBenhId AS nvarchar(30)), N'') AS DiseaseGroupId,
        COALESCE(b.MaBenh, N'') AS DiseaseCode,
        COALESCE(b.TenBenh, N'') AS DiseaseName,
        COALESCE(llt.MaLoaiLienKet, N'UNKNOWN') AS LinkTypeCode,
        COALESCE(mtc.MaMucTinCay, N'UNKNOWN') AS ConfidenceLevelCode,
        COALESCE(CAST(lk.DiemLienKet AS nvarchar(30)), N'') AS SourceScore
    FROM dbo.LienKetThuocBenh lk
    JOIN dbo.Thuoc t ON t.ThuocId = lk.ThuocId
    JOIN dbo.Benh b ON b.BenhId = lk.BenhId
    LEFT JOIN dbo.LoaiLienKet llt ON llt.LoaiLienKetId = lk.LoaiLienKetId
    LEFT JOIN dbo.MucTinCay mtc ON mtc.MucTinCayId = lk.MucTinCayId
),
MauAm AS
(
    SELECT
        lkNguon.LienKetId + 100000000 AS DatasetItemId,
        t.ThuocId AS DrugId,
        b.BenhId AS DiseaseId,
        CAST(0 AS int) AS LabelValue,
        N'ALL' AS SplitName,
        N'{}' AS FeatureVectorJson,
        COALESCE(t.MaThuoc, N'') AS DrugCode,
        COALESCE(t.TenThuoc, N'') AS ActiveName,
        COALESCE(t.TenThuocGoc, N'') AS TradeName,
        COALESCE(CAST(t.NhomThuocId AS nvarchar(30)), N'') AS DrugGroupId,
        N'' AS RouteId,
        COALESCE(CAST(b.NhomBenhId AS nvarchar(30)), N'') AS DiseaseGroupId,
        COALESCE(b.MaBenh, N'') AS DiseaseCode,
        COALESCE(b.TenBenh, N'') AS DiseaseName,
        N'UNKNOWN' AS LinkTypeCode,
        N'UNKNOWN' AS ConfidenceLevelCode,
        N'' AS SourceScore
    FROM dbo.LienKetThuocBenh lkNguon
    JOIN dbo.Thuoc t ON t.ThuocId = lkNguon.ThuocId
    JOIN dbo.Benh b
        ON b.BenhId =
            CASE
                WHEN lkNguon.BenhId < @MaxBenhId
                THEN lkNguon.BenhId + 1
                ELSE 1
            END
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.LienKetThuocBenh lk
        WHERE lk.ThuocId = lkNguon.ThuocId
          AND lk.BenhId = b.BenhId
    )
)
SELECT *
FROM MauDuong
UNION ALL
SELECT *
FROM MauAm
ORDER BY DatasetItemId;
