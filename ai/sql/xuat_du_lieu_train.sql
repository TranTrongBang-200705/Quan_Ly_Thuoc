SET NOCOUNT ON;
SELECT
    di.DatasetItemId,
    di.DrugId,
    di.DiseaseId,
    di.LabelValue,
    di.SplitName,
    REPLACE(REPLACE(COALESCE(di.FeatureVectorJson, N'{}'), CHAR(13), N' '), CHAR(10), N' ') AS FeatureVectorJson,
    COALESCE(dr.DrugCode, N'') AS DrugCode,
    COALESCE(dr.ActiveName, N'') AS ActiveName,
    COALESCE(dr.TradeName, N'') AS TradeName,
    COALESCE(CAST(dr.DrugGroupId AS nvarchar(30)), N'') AS DrugGroupId,
    COALESCE(CAST(dr.RouteId AS nvarchar(30)), N'') AS RouteId,
    COALESCE(CAST(dis.DiseaseGroupId AS nvarchar(30)), N'') AS DiseaseGroupId,
    COALESCE(dis.DiseaseCode, N'') AS DiseaseCode,
    COALESCE(dis.DiseaseName, N'') AS DiseaseName,
    COALESCE(lt.LinkTypeCode, N'UNKNOWN') AS LinkTypeCode,
    COALESCE(cl.LevelCode, N'UNKNOWN') AS ConfidenceLevelCode,
    COALESCE(CAST(src.SourceScore AS nvarchar(30)), N'') AS SourceScore
FROM dbo.DatasetItems di
JOIN dbo.Drugs dr ON dr.DrugId = di.DrugId
JOIN dbo.Diseases dis ON dis.DiseaseId = di.DiseaseId
LEFT JOIN dbo.DrugDiseaseLinks src ON src.LinkId = di.SourceLinkId
LEFT JOIN dbo.LinkTypes lt ON lt.LinkTypeId = src.LinkTypeId
LEFT JOIN dbo.ConfidenceLevels cl ON cl.ConfidenceLevelId = src.ConfidenceLevelId
ORDER BY di.DatasetItemId;
