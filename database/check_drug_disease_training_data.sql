SET NOCOUNT ON;

PRINT '1. Total drugs';
SELECT COUNT(*) AS TotalDrugs
FROM dbo.Drugs
WHERE IsDeleted = 0;

PRINT '2. Total diseases';
SELECT COUNT(*) AS TotalDiseases
FROM dbo.Diseases
WHERE IsDeleted = 0;

PRINT '3. Total disease synonyms';
SELECT COUNT(*) AS TotalDiseaseSynonyms
FROM dbo.DiseaseSynonyms;

PRINT '3b. Vietnamese disease names and synonyms for UI/search';
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

PRINT '4. Total therapeutic links';
SELECT COUNT(*) AS TotalTherapeuticLinks
FROM dbo.DrugDiseaseLinks l
JOIN dbo.LinkTypes lt ON lt.LinkTypeId = l.LinkTypeId
WHERE l.IsDeleted = 0
  AND lt.LinkTypeCode IN ('INDICATION', 'THERAPEUTIC_INDICATION');

PRINT '5. Total contraindication links';
SELECT COUNT(*) AS TotalContraindicationLinks
FROM dbo.DrugDiseaseLinks l
JOIN dbo.LinkTypes lt ON lt.LinkTypeId = l.LinkTypeId
WHERE l.IsDeleted = 0
  AND lt.LinkTypeCode = 'CONTRAINDICATION';

PRINT '6. Total adverse effect links';
SELECT COUNT(*) AS TotalAdverseEffectLinks
FROM dbo.DrugDiseaseLinks l
JOIN dbo.LinkTypes lt ON lt.LinkTypeId = l.LinkTypeId
WHERE l.IsDeleted = 0
  AND lt.LinkTypeCode IN ('SIDE_EFFECT', 'ADVERSE_EFFECT', 'SAFETY_WARNING');

PRINT '7. Total links by link type';
SELECT
    lt.LinkTypeCode,
    lt.LinkTypeName,
    COUNT(*) AS LinkCount
FROM dbo.DrugDiseaseLinks l
JOIN dbo.LinkTypes lt ON lt.LinkTypeId = l.LinkTypeId
WHERE l.IsDeleted = 0
GROUP BY lt.LinkTypeCode, lt.LinkTypeName
ORDER BY LinkCount DESC, lt.LinkTypeCode;

PRINT '8. Total links by evidence status';
SELECT
    es.EvidenceStatusCode,
    es.EvidenceStatusName,
    COUNT(*) AS LinkCount
FROM dbo.DrugDiseaseLinks l
JOIN dbo.EvidenceStatuses es ON es.EvidenceStatusId = l.EvidenceStatusId
WHERE l.IsDeleted = 0
GROUP BY es.EvidenceStatusCode, es.EvidenceStatusName
ORDER BY LinkCount DESC, es.EvidenceStatusCode;

PRINT '9. Total training labels by value';
SELECT
    LabelValue,
    LabelSource,
    COUNT(*) AS LabelCount
FROM dbo.LinkTrainingLabels
GROUP BY LabelValue, LabelSource
ORDER BY LabelValue DESC, LabelSource;

PRINT '10. Top 100 generated links';
SELECT TOP (100)
    dr.DrugCode,
    dr.ActiveName,
    dr.TradeName,
    dis.DiseaseCode,
    dis.DiseaseName,
    lt.LinkTypeName,
    es.EvidenceStatusName,
    cl.LevelName AS ConfidenceLevelName,
    er.Description AS EvidenceSnippet
FROM dbo.DrugDiseaseLinks l
JOIN dbo.Drugs dr ON dr.DrugId = l.DrugId
JOIN dbo.Diseases dis ON dis.DiseaseId = l.DiseaseId
JOIN dbo.LinkTypes lt ON lt.LinkTypeId = l.LinkTypeId
JOIN dbo.EvidenceStatuses es ON es.EvidenceStatusId = l.EvidenceStatusId
LEFT JOIN dbo.ConfidenceLevels cl ON cl.ConfidenceLevelId = l.ConfidenceLevelId
OUTER APPLY (
    SELECT TOP (1) er.Description
    FROM dbo.LinkEvidenceReferences er
    LEFT JOIN dbo.DataSources src ON src.DataSourceId = er.DataSourceId
    WHERE er.LinkId = l.LinkId
      AND (src.SourceCode = 'EXISTING_DRUG_LABEL_TEXT' OR src.SourceCode IS NULL)
    ORDER BY er.LinkEvidenceReferenceId
) er
WHERE l.IsDeleted = 0
ORDER BY l.CreatedAt DESC, l.LinkId DESC;

PRINT '11. Diseases that have no linked drugs';
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

PRINT '12. Drugs that have no linked diseases';
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

PRINT '13. Top diseases by number of linked drugs';
SELECT TOP (50)
    dis.DiseaseCode,
    dis.DiseaseName,
    COUNT(DISTINCT l.DrugId) AS LinkedDrugCount
FROM dbo.Diseases dis
JOIN dbo.DrugDiseaseLinks l ON l.DiseaseId = dis.DiseaseId
WHERE dis.IsDeleted = 0
  AND l.IsDeleted = 0
GROUP BY dis.DiseaseCode, dis.DiseaseName
ORDER BY LinkedDrugCount DESC, dis.DiseaseCode;

PRINT '14. Top drugs by number of linked diseases';
SELECT TOP (50)
    dr.DrugCode,
    dr.ActiveName,
    dr.TradeName,
    COUNT(DISTINCT l.DiseaseId) AS LinkedDiseaseCount
FROM dbo.Drugs dr
JOIN dbo.DrugDiseaseLinks l ON l.DrugId = dr.DrugId
WHERE dr.IsDeleted = 0
  AND l.IsDeleted = 0
GROUP BY dr.DrugCode, dr.ActiveName, dr.TradeName
ORDER BY LinkedDiseaseCount DESC, dr.DrugCode;
