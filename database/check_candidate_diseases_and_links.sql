SET NOCOUNT ON;

PRINT '1. Total diseases';
SELECT COUNT(*) AS TotalDiseases
FROM dbo.Diseases
WHERE IsDeleted = 0;

PRINT '1b. Vietnamese disease names and synonyms for UI/search';
SELECT
    d.DiseaseCode,
    d.DiseaseName AS VietnameseDiseaseName,
    en.EnglishSynonyms,
    vi.VietnameseSynonyms,
    COUNT(DISTINCT l.DrugId) AS LinkedDrugCount
FROM dbo.Diseases d
LEFT JOIN dbo.DrugDiseaseLinks l
    ON l.DiseaseId = d.DiseaseId
   AND l.IsDeleted = 0
OUTER APPLY (
    SELECT STRING_AGG(ds.SynonymName, '; ') AS EnglishSynonyms
    FROM dbo.DiseaseSynonyms ds
    WHERE ds.DiseaseId = d.DiseaseId
      AND ISNULL(ds.LanguageCode, '') = 'en'
) en
OUTER APPLY (
    SELECT STRING_AGG(ds.SynonymName, '; ') AS VietnameseSynonyms
    FROM dbo.DiseaseSynonyms ds
    WHERE ds.DiseaseId = d.DiseaseId
      AND ISNULL(ds.LanguageCode, '') = 'vi'
) vi
WHERE d.IsDeleted = 0
GROUP BY d.DiseaseCode, d.DiseaseName, en.EnglishSynonyms, vi.VietnameseSynonyms
ORDER BY d.DiseaseCode;

PRINT '2. Total candidate diseases imported from local drug text mining';
SELECT COUNT(DISTINCT d.DiseaseId) AS TotalCandidateDiseasesImported
FROM dbo.Diseases d
JOIN dbo.DiseaseSources ds ON ds.DiseaseId = d.DiseaseId
JOIN dbo.DataSources src ON src.DataSourceId = ds.DataSourceId
WHERE d.IsDeleted = 0
  AND src.SourceCode = 'LOCAL_DRUG_TEXT_MINING';

PRINT '3. Total drug-disease links';
SELECT COUNT(*) AS TotalDrugDiseaseLinks
FROM dbo.DrugDiseaseLinks
WHERE IsDeleted = 0;

PRINT '4. Links by link type';
SELECT
    lt.LinkTypeCode,
    lt.LinkTypeName,
    COUNT(*) AS LinkCount
FROM dbo.DrugDiseaseLinks l
JOIN dbo.LinkTypes lt ON lt.LinkTypeId = l.LinkTypeId
WHERE l.IsDeleted = 0
GROUP BY lt.LinkTypeCode, lt.LinkTypeName
ORDER BY LinkCount DESC, lt.LinkTypeCode;

PRINT '5. Training labels by value';
SELECT
    LabelValue,
    LabelSource,
    COUNT(*) AS LabelCount
FROM dbo.LinkTrainingLabels
GROUP BY LabelValue, LabelSource
ORDER BY LabelValue DESC, LabelSource;

PRINT '6. Top 100 new diseases generated from drug text';
SELECT TOP (100)
    d.DiseaseCode,
    d.DiseaseName,
    dg.GroupCode,
    dg.GroupName,
    rs.StatusCode AS ReviewStatusCode,
    cl.LevelCode AS ConfidenceLevelCode,
    ds.SourceNote,
    d.CreatedAt,
    dfv.FeatureValue,
    dfv.FeatureVectorJson
FROM dbo.Diseases d
JOIN dbo.DiseaseSources ds ON ds.DiseaseId = d.DiseaseId
JOIN dbo.DataSources src ON src.DataSourceId = ds.DataSourceId
LEFT JOIN dbo.DiseaseGroups dg ON dg.DiseaseGroupId = d.DiseaseGroupId
LEFT JOIN dbo.ReviewStatuses rs ON rs.ReviewStatusId = d.ReviewStatusId
LEFT JOIN dbo.ConfidenceLevels cl ON cl.ConfidenceLevelId = d.ConfidenceLevelId
OUTER APPLY (
    SELECT TOP (1) dfv.FeatureValue, dfv.FeatureVectorJson
    FROM dbo.DiseaseFeatureValues dfv
    JOIN dbo.FeatureDefinitions fd ON fd.FeatureDefinitionId = dfv.FeatureDefinitionId
    WHERE dfv.DiseaseId = d.DiseaseId
      AND fd.EntityType = 'DISEASE'
      AND fd.FeatureCode = 'LOCAL_DRUG_TEXT_MINING_PROFILE'
    ORDER BY dfv.DiseaseFeatureValueId DESC
) dfv
WHERE d.IsDeleted = 0
  AND src.SourceCode = 'LOCAL_DRUG_TEXT_MINING'
ORDER BY d.CreatedAt DESC, d.DiseaseCode;

PRINT '7. Top 100 new links with evidence snippet';
SELECT TOP (100)
    dr.DrugCode,
    dr.ActiveName,
    dr.TradeName,
    dis.DiseaseCode,
    dis.DiseaseName,
    lt.LinkTypeCode,
    lt.LinkTypeName,
    es.EvidenceStatusCode,
    es.EvidenceStatusName,
    rs.StatusCode AS ReviewStatusCode,
    er.Description AS EvidenceSnippet,
    l.CreatedAt
FROM dbo.DrugDiseaseLinks l
JOIN dbo.Drugs dr ON dr.DrugId = l.DrugId
JOIN dbo.Diseases dis ON dis.DiseaseId = l.DiseaseId
JOIN dbo.LinkTypes lt ON lt.LinkTypeId = l.LinkTypeId
JOIN dbo.EvidenceStatuses es ON es.EvidenceStatusId = l.EvidenceStatusId
LEFT JOIN dbo.ReviewStatuses rs ON rs.ReviewStatusId = l.ReviewStatusId
JOIN dbo.DiseaseSources ds ON ds.DiseaseId = dis.DiseaseId
JOIN dbo.DataSources disease_src ON disease_src.DataSourceId = ds.DataSourceId
OUTER APPLY (
    SELECT TOP (1) er.Description
    FROM dbo.LinkEvidenceReferences er
    JOIN dbo.DataSources evidence_src ON evidence_src.DataSourceId = er.DataSourceId
    WHERE er.LinkId = l.LinkId
      AND evidence_src.SourceCode = 'EXISTING_DRUG_LABEL_TEXT'
    ORDER BY er.LinkEvidenceReferenceId
) er
WHERE l.IsDeleted = 0
  AND disease_src.SourceCode = 'LOCAL_DRUG_TEXT_MINING'
ORDER BY l.CreatedAt DESC, l.LinkId DESC;

PRINT '8. Diseases with no linked drugs';
SELECT
    dis.DiseaseCode,
    dis.DiseaseName
FROM dbo.Diseases dis
WHERE dis.IsDeleted = 0
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.DrugDiseaseLinks l
      WHERE l.DiseaseId = dis.DiseaseId
        AND l.IsDeleted = 0
  )
ORDER BY dis.DiseaseCode;

PRINT '9. Drugs with no linked diseases';
SELECT
    dr.DrugCode,
    dr.ActiveName,
    dr.TradeName
FROM dbo.Drugs dr
WHERE dr.IsDeleted = 0
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.DrugDiseaseLinks l
      WHERE l.DrugId = dr.DrugId
        AND l.IsDeleted = 0
  )
ORDER BY dr.DrugCode;
