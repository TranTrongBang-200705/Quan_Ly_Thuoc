/* ==========================================================
   DATABASE: DrugDiseaseML_DB
   Đề tài: Hệ thống web dự đoán liên kết thuốc – bệnh bằng Machine Learning
   Hệ quản trị: SQL Server / T-SQL
   Ghi chú: Kết quả dự đoán chỉ dùng để tham khảo, không thay thế tư vấn bác sĩ/dược sĩ.
   ========================================================== */

IF DB_ID(N'DrugDiseaseML_DB') IS NULL
BEGIN
    CREATE DATABASE DrugDiseaseML_DB;
END
GO

USE DrugDiseaseML_DB;
GO

/* ==========================================================
   1. NHÓM NGƯỜI DÙNG, PHÂN QUYỀN, AUDIT
   ========================================================== */
CREATE TABLE dbo.Roles (
    RoleId INT IDENTITY(1,1) PRIMARY KEY,
    RoleCode NVARCHAR(50) NOT NULL UNIQUE,
    RoleName NVARCHAR(100) NOT NULL,
    Description NVARCHAR(500) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE dbo.Users (
    UserId INT IDENTITY(1,1) PRIMARY KEY,
    UserCode NVARCHAR(50) NULL UNIQUE,
    FullName NVARCHAR(200) NOT NULL,
    Email NVARCHAR(255) NOT NULL UNIQUE,
    Phone NVARCHAR(30) NULL,
    PasswordHash NVARCHAR(500) NULL,
    Organization NVARCHAR(255) NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2(0) NULL,
    IsDeleted BIT NOT NULL DEFAULT 0
);
GO

CREATE TABLE dbo.UserRoles (
    UserId INT NOT NULL,
    RoleId INT NOT NULL,
    AssignedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    PRIMARY KEY (UserId, RoleId),
    CONSTRAINT FK_UserRoles_Users FOREIGN KEY (UserId) REFERENCES dbo.Users(UserId),
    CONSTRAINT FK_UserRoles_Roles FOREIGN KEY (RoleId) REFERENCES dbo.Roles(RoleId)
);
GO

CREATE TABLE dbo.UserSessions (
    SessionId UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
    UserId INT NOT NULL,
    RefreshTokenHash NVARCHAR(500) NOT NULL,
    IpAddress NVARCHAR(50) NULL,
    UserAgent NVARCHAR(500) NULL,
    ExpiresAt DATETIME2(0) NOT NULL,
    RevokedAt DATETIME2(0) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_UserSessions_Users FOREIGN KEY (UserId) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.AuditLogs (
    AuditId BIGINT IDENTITY(1,1) PRIMARY KEY,
    TableName NVARCHAR(128) NOT NULL,
    RecordId NVARCHAR(100) NOT NULL,
    ActionType NVARCHAR(20) NOT NULL CHECK (ActionType IN ('INSERT','UPDATE','DELETE')),
    ChangedBy INT NULL,
    ChangedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    OldValues NVARCHAR(MAX) NULL CHECK (OldValues IS NULL OR ISJSON(OldValues)=1),
    NewValues NVARCHAR(MAX) NULL CHECK (NewValues IS NULL OR ISJSON(NewValues)=1),
    CONSTRAINT FK_AuditLogs_Users FOREIGN KEY (ChangedBy) REFERENCES dbo.Users(UserId)
);
GO

/* ==========================================================
   2. LOOKUP / DANH MỤC DÙNG CHUNG
   ========================================================== */
CREATE TABLE dbo.DataSources (
    DataSourceId INT IDENTITY(1,1) PRIMARY KEY,
    SourceCode NVARCHAR(50) NOT NULL UNIQUE,
    SourceName NVARCHAR(200) NOT NULL,
    SourceUrl NVARCHAR(500) NULL,
    Description NVARCHAR(1000) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE dbo.ApprovalStatuses (
    ApprovalStatusId INT IDENTITY(1,1) PRIMARY KEY,
    StatusCode NVARCHAR(50) NOT NULL UNIQUE,
    StatusName NVARCHAR(100) NOT NULL
);
GO

CREATE TABLE dbo.ReviewStatuses (
    ReviewStatusId INT IDENTITY(1,1) PRIMARY KEY,
    StatusCode NVARCHAR(50) NOT NULL UNIQUE,
    StatusName NVARCHAR(100) NOT NULL
);
GO

CREATE TABLE dbo.ConfidenceLevels (
    ConfidenceLevelId INT IDENTITY(1,1) PRIMARY KEY,
    LevelCode NVARCHAR(50) NOT NULL UNIQUE,
    LevelName NVARCHAR(100) NOT NULL,
    MinScore DECIMAL(5,4) NULL,
    MaxScore DECIMAL(5,4) NULL,
    CONSTRAINT CK_ConfidenceLevels_Range CHECK (MinScore IS NULL OR MaxScore IS NULL OR MinScore <= MaxScore)
);
GO

CREATE TABLE dbo.DrugGroups (
    DrugGroupId INT IDENTITY(1,1) PRIMARY KEY,
    GroupCode NVARCHAR(50) NOT NULL UNIQUE,
    GroupName NVARCHAR(150) NOT NULL
);
GO

CREATE TABLE dbo.DiseaseGroups (
    DiseaseGroupId INT IDENTITY(1,1) PRIMARY KEY,
    GroupCode NVARCHAR(50) NOT NULL UNIQUE,
    GroupName NVARCHAR(150) NOT NULL
);
GO

CREATE TABLE dbo.AdministrationRoutes (
    RouteId INT IDENTITY(1,1) PRIMARY KEY,
    RouteCode NVARCHAR(50) NOT NULL UNIQUE,
    RouteName NVARCHAR(100) NOT NULL
);
GO

CREATE TABLE dbo.LinkTypes (
    LinkTypeId INT IDENTITY(1,1) PRIMARY KEY,
    LinkTypeCode NVARCHAR(50) NOT NULL UNIQUE,
    LinkTypeName NVARCHAR(150) NOT NULL,
    Description NVARCHAR(500) NULL
);
GO

CREATE TABLE dbo.EvidenceStatuses (
    EvidenceStatusId INT IDENTITY(1,1) PRIMARY KEY,
    EvidenceStatusCode NVARCHAR(50) NOT NULL UNIQUE,
    EvidenceStatusName NVARCHAR(150) NOT NULL
);
GO

CREATE TABLE dbo.PredictionTypes (
    PredictionTypeId INT IDENTITY(1,1) PRIMARY KEY,
    PredictionTypeCode NVARCHAR(50) NOT NULL UNIQUE,
    PredictionTypeName NVARCHAR(150) NOT NULL
);
GO

CREATE TABLE dbo.ResultDeliveryChannels (
    ChannelId INT IDENTITY(1,1) PRIMARY KEY,
    ChannelCode NVARCHAR(50) NOT NULL UNIQUE,
    ChannelName NVARCHAR(150) NOT NULL
);
GO

CREATE TABLE dbo.ModelAlgorithms (
    AlgorithmId INT IDENTITY(1,1) PRIMARY KEY,
    AlgorithmCode NVARCHAR(50) NOT NULL UNIQUE,
    AlgorithmName NVARCHAR(150) NOT NULL,
    Description NVARCHAR(1000) NULL
);
GO

CREATE TABLE dbo.FeedbackStatuses (
    FeedbackStatusId INT IDENTITY(1,1) PRIMARY KEY,
    StatusCode NVARCHAR(50) NOT NULL UNIQUE,
    StatusName NVARCHAR(150) NOT NULL
);
GO

CREATE TABLE dbo.FeatureDefinitions (
    FeatureDefinitionId INT IDENTITY(1,1) PRIMARY KEY,
    EntityType NVARCHAR(30) NOT NULL CHECK (EntityType IN ('DRUG','DISEASE','LINK','PAIR')),
    FeatureCode NVARCHAR(100) NOT NULL,
    FeatureName NVARCHAR(200) NOT NULL,
    DataType NVARCHAR(50) NOT NULL DEFAULT 'NVARCHAR',
    EncodingMethod NVARCHAR(100) NULL,
    Description NVARCHAR(1000) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT UQ_FeatureDefinitions UNIQUE (EntityType, FeatureCode)
);
GO

/* ==========================================================
   3. NHÓM QUẢN LÝ DỮ LIỆU THUỐC - BM-01
   ========================================================== */
CREATE TABLE dbo.Drugs (
    DrugId INT IDENTITY(1,1) PRIMARY KEY,
    DrugCode NVARCHAR(50) NOT NULL UNIQUE, -- DRUG-
    ActiveName NVARCHAR(255) NOT NULL,
    TradeName NVARCHAR(255) NULL,
    DrugGroupId INT NULL,
    DosageFormStrength NVARCHAR(255) NULL,
    RouteId INT NULL,
    ApprovalStatusId INT NULL,
    MechanismOfAction NVARCHAR(MAX) NULL,
    KnownIndications NVARCHAR(MAX) NULL,
    SideEffectsWarnings NVARCHAR(MAX) NULL,
    ContraindicationsInteractions NVARCHAR(MAX) NULL,
    ConfidenceLevelId INT NULL,
    ReviewStatusId INT NOT NULL DEFAULT 1,
    ReviewedBy INT NULL,
    ReviewedAt DATETIME2(0) NULL,
    CreatedBy INT NULL,
    UpdatedBy INT NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2(0) NULL,
    IsDeleted BIT NOT NULL DEFAULT 0,
    CONSTRAINT FK_Drugs_DrugGroups FOREIGN KEY (DrugGroupId) REFERENCES dbo.DrugGroups(DrugGroupId),
    CONSTRAINT FK_Drugs_Routes FOREIGN KEY (RouteId) REFERENCES dbo.AdministrationRoutes(RouteId),
    CONSTRAINT FK_Drugs_ApprovalStatuses FOREIGN KEY (ApprovalStatusId) REFERENCES dbo.ApprovalStatuses(ApprovalStatusId),
    CONSTRAINT FK_Drugs_ConfidenceLevels FOREIGN KEY (ConfidenceLevelId) REFERENCES dbo.ConfidenceLevels(ConfidenceLevelId),
    CONSTRAINT FK_Drugs_ReviewStatuses FOREIGN KEY (ReviewStatusId) REFERENCES dbo.ReviewStatuses(ReviewStatusId),
    CONSTRAINT FK_Drugs_ReviewedBy FOREIGN KEY (ReviewedBy) REFERENCES dbo.Users(UserId),
    CONSTRAINT FK_Drugs_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES dbo.Users(UserId),
    CONSTRAINT FK_Drugs_UpdatedBy FOREIGN KEY (UpdatedBy) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.DrugSynonyms (
    DrugSynonymId INT IDENTITY(1,1) PRIMARY KEY,
    DrugId INT NOT NULL,
    SynonymName NVARCHAR(255) NOT NULL,
    LanguageCode NVARCHAR(10) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_DrugSynonyms_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT UQ_DrugSynonyms UNIQUE (DrugId, SynonymName)
);
GO

CREATE TABLE dbo.DrugExternalCodes (
    DrugExternalCodeId INT IDENTITY(1,1) PRIMARY KEY,
    DrugId INT NOT NULL,
    DataSourceId INT NOT NULL,
    ExternalCode NVARCHAR(100) NOT NULL,
    ExternalUrl NVARCHAR(500) NULL,
    CONSTRAINT FK_DrugExternalCodes_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT FK_DrugExternalCodes_DataSources FOREIGN KEY (DataSourceId) REFERENCES dbo.DataSources(DataSourceId),
    CONSTRAINT UQ_DrugExternalCodes UNIQUE (DataSourceId, ExternalCode)
);
GO

CREATE TABLE dbo.DrugTargets (
    DrugTargetId INT IDENTITY(1,1) PRIMARY KEY,
    DrugId INT NOT NULL,
    TargetName NVARCHAR(255) NOT NULL,
    TargetType NVARCHAR(50) NULL CHECK (TargetType IS NULL OR TargetType IN ('GENE','PROTEIN','PATHWAY','TARGET','OTHER')),
    Description NVARCHAR(1000) NULL,
    CONSTRAINT FK_DrugTargets_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId)
);
GO

CREATE TABLE dbo.DrugSources (
    DrugSourceId INT IDENTITY(1,1) PRIMARY KEY,
    DrugId INT NOT NULL,
    DataSourceId INT NOT NULL,
    SourceNote NVARCHAR(1000) NULL,
    CONSTRAINT FK_DrugSources_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT FK_DrugSources_DataSources FOREIGN KEY (DataSourceId) REFERENCES dbo.DataSources(DataSourceId),
    CONSTRAINT UQ_DrugSources UNIQUE (DrugId, DataSourceId)
);
GO

CREATE TABLE dbo.DrugFeatureValues (
    DrugFeatureValueId INT IDENTITY(1,1) PRIMARY KEY,
    DrugId INT NOT NULL,
    FeatureDefinitionId INT NOT NULL,
    FeatureValue NVARCHAR(MAX) NULL,
    FeatureVectorJson NVARCHAR(MAX) NULL CHECK (FeatureVectorJson IS NULL OR ISJSON(FeatureVectorJson)=1),
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_DrugFeatureValues_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT FK_DrugFeatureValues_FeatureDefinitions FOREIGN KEY (FeatureDefinitionId) REFERENCES dbo.FeatureDefinitions(FeatureDefinitionId),
    CONSTRAINT UQ_DrugFeatureValues UNIQUE (DrugId, FeatureDefinitionId)
);
GO

CREATE TABLE dbo.DrugReviewLogs (
    DrugReviewLogId INT IDENTITY(1,1) PRIMARY KEY,
    DrugId INT NOT NULL,
    ReviewStatusId INT NOT NULL,
    ReviewerId INT NULL,
    ReviewNote NVARCHAR(1000) NULL,
    ReviewedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_DrugReviewLogs_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT FK_DrugReviewLogs_Status FOREIGN KEY (ReviewStatusId) REFERENCES dbo.ReviewStatuses(ReviewStatusId),
    CONSTRAINT FK_DrugReviewLogs_Reviewer FOREIGN KEY (ReviewerId) REFERENCES dbo.Users(UserId)
);
GO

/* ==========================================================
   4. NHÓM QUẢN LÝ DỮ LIỆU BỆNH - BM-02
   ========================================================== */
CREATE TABLE dbo.Diseases (
    DiseaseId INT IDENTITY(1,1) PRIMARY KEY,
    DiseaseCode NVARCHAR(50) NOT NULL UNIQUE, -- DIS-
    DiseaseName NVARCHAR(255) NOT NULL,
    DiseaseGroupId INT NULL,
    PrevalenceLevel NVARCHAR(50) NULL CHECK (PrevalenceLevel IS NULL OR PrevalenceLevel IN (N'Phổ biến',N'Ít gặp',N'Hiếm gặp',N'Chưa xác định')),
    Description NVARCHAR(MAX) NULL,
    Symptoms NVARCHAR(MAX) NULL,
    KnownTreatments NVARCHAR(MAX) NULL,
    ConfidenceLevelId INT NULL,
    ReviewStatusId INT NOT NULL DEFAULT 1,
    ReviewedBy INT NULL,
    ReviewedAt DATETIME2(0) NULL,
    CreatedBy INT NULL,
    UpdatedBy INT NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2(0) NULL,
    IsDeleted BIT NOT NULL DEFAULT 0,
    CONSTRAINT FK_Diseases_DiseaseGroups FOREIGN KEY (DiseaseGroupId) REFERENCES dbo.DiseaseGroups(DiseaseGroupId),
    CONSTRAINT FK_Diseases_ConfidenceLevels FOREIGN KEY (ConfidenceLevelId) REFERENCES dbo.ConfidenceLevels(ConfidenceLevelId),
    CONSTRAINT FK_Diseases_ReviewStatuses FOREIGN KEY (ReviewStatusId) REFERENCES dbo.ReviewStatuses(ReviewStatusId),
    CONSTRAINT FK_Diseases_ReviewedBy FOREIGN KEY (ReviewedBy) REFERENCES dbo.Users(UserId),
    CONSTRAINT FK_Diseases_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES dbo.Users(UserId),
    CONSTRAINT FK_Diseases_UpdatedBy FOREIGN KEY (UpdatedBy) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.DiseaseSynonyms (
    DiseaseSynonymId INT IDENTITY(1,1) PRIMARY KEY,
    DiseaseId INT NOT NULL,
    SynonymName NVARCHAR(255) NOT NULL,
    LanguageCode NVARCHAR(10) NULL,
    CONSTRAINT FK_DiseaseSynonyms_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId),
    CONSTRAINT UQ_DiseaseSynonyms UNIQUE (DiseaseId, SynonymName)
);
GO

CREATE TABLE dbo.DiseaseExternalCodes (
    DiseaseExternalCodeId INT IDENTITY(1,1) PRIMARY KEY,
    DiseaseId INT NOT NULL,
    DataSourceId INT NOT NULL,
    ExternalCode NVARCHAR(100) NOT NULL,
    ExternalUrl NVARCHAR(500) NULL,
    CONSTRAINT FK_DiseaseExternalCodes_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId),
    CONSTRAINT FK_DiseaseExternalCodes_DataSources FOREIGN KEY (DataSourceId) REFERENCES dbo.DataSources(DataSourceId),
    CONSTRAINT UQ_DiseaseExternalCodes UNIQUE (DataSourceId, ExternalCode)
);
GO

CREATE TABLE dbo.DiseaseGenes (
    DiseaseGeneId INT IDENTITY(1,1) PRIMARY KEY,
    DiseaseId INT NOT NULL,
    GeneSymbol NVARCHAR(100) NOT NULL,
    GeneName NVARCHAR(255) NULL,
    Description NVARCHAR(1000) NULL,
    CONSTRAINT FK_DiseaseGenes_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId)
);
GO

CREATE TABLE dbo.DiseasePathways (
    DiseasePathwayId INT IDENTITY(1,1) PRIMARY KEY,
    DiseaseId INT NOT NULL,
    PathwayName NVARCHAR(255) NOT NULL,
    Description NVARCHAR(1000) NULL,
    CONSTRAINT FK_DiseasePathways_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId)
);
GO

CREATE TABLE dbo.DiseaseSources (
    DiseaseSourceId INT IDENTITY(1,1) PRIMARY KEY,
    DiseaseId INT NOT NULL,
    DataSourceId INT NOT NULL,
    SourceNote NVARCHAR(1000) NULL,
    CONSTRAINT FK_DiseaseSources_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId),
    CONSTRAINT FK_DiseaseSources_DataSources FOREIGN KEY (DataSourceId) REFERENCES dbo.DataSources(DataSourceId),
    CONSTRAINT UQ_DiseaseSources UNIQUE (DiseaseId, DataSourceId)
);
GO

CREATE TABLE dbo.DiseaseFeatureValues (
    DiseaseFeatureValueId INT IDENTITY(1,1) PRIMARY KEY,
    DiseaseId INT NOT NULL,
    FeatureDefinitionId INT NOT NULL,
    FeatureValue NVARCHAR(MAX) NULL,
    FeatureVectorJson NVARCHAR(MAX) NULL CHECK (FeatureVectorJson IS NULL OR ISJSON(FeatureVectorJson)=1),
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_DiseaseFeatureValues_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId),
    CONSTRAINT FK_DiseaseFeatureValues_FeatureDefinitions FOREIGN KEY (FeatureDefinitionId) REFERENCES dbo.FeatureDefinitions(FeatureDefinitionId),
    CONSTRAINT UQ_DiseaseFeatureValues UNIQUE (DiseaseId, FeatureDefinitionId)
);
GO

CREATE TABLE dbo.DiseaseReviewLogs (
    DiseaseReviewLogId INT IDENTITY(1,1) PRIMARY KEY,
    DiseaseId INT NOT NULL,
    ReviewStatusId INT NOT NULL,
    ReviewerId INT NULL,
    ReviewNote NVARCHAR(1000) NULL,
    ReviewedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_DiseaseReviewLogs_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId),
    CONSTRAINT FK_DiseaseReviewLogs_Status FOREIGN KEY (ReviewStatusId) REFERENCES dbo.ReviewStatuses(ReviewStatusId),
    CONSTRAINT FK_DiseaseReviewLogs_Reviewer FOREIGN KEY (ReviewerId) REFERENCES dbo.Users(UserId)
);
GO

/* ==========================================================
   5. NHÓM LIÊN KẾT THUỐC - BỆNH ĐÃ BIẾT - BM-03
   ========================================================== */
CREATE TABLE dbo.DrugDiseaseLinks (
    LinkId INT IDENTITY(1,1) PRIMARY KEY,
    LinkCode NVARCHAR(50) NOT NULL UNIQUE, -- LINK-
    DrugId INT NOT NULL,
    DiseaseId INT NOT NULL,
    LinkTypeId INT NOT NULL,
    EvidenceStatusId INT NOT NULL,
    ConfidenceLevelId INT NULL,
    SourceScore DECIMAL(7,4) NULL CHECK (SourceScore IS NULL OR SourceScore BETWEEN 0 AND 1),
    FormationBasis NVARCHAR(500) NULL,
    EvidenceDescription NVARCHAR(MAX) NULL,
    ProcessingNote NVARCHAR(1000) NULL,
    ReviewStatusId INT NOT NULL DEFAULT 1,
    VerifiedBy INT NULL,
    VerifiedRole NVARCHAR(100) NULL,
    VerifiedAt DATETIME2(0) NULL,
    CreatedBy INT NULL,
    UpdatedBy INT NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2(0) NULL,
    IsDeleted BIT NOT NULL DEFAULT 0,
    CONSTRAINT FK_Links_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT FK_Links_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId),
    CONSTRAINT FK_Links_LinkTypes FOREIGN KEY (LinkTypeId) REFERENCES dbo.LinkTypes(LinkTypeId),
    CONSTRAINT FK_Links_EvidenceStatuses FOREIGN KEY (EvidenceStatusId) REFERENCES dbo.EvidenceStatuses(EvidenceStatusId),
    CONSTRAINT FK_Links_ConfidenceLevels FOREIGN KEY (ConfidenceLevelId) REFERENCES dbo.ConfidenceLevels(ConfidenceLevelId),
    CONSTRAINT FK_Links_ReviewStatuses FOREIGN KEY (ReviewStatusId) REFERENCES dbo.ReviewStatuses(ReviewStatusId),
    CONSTRAINT FK_Links_VerifiedBy FOREIGN KEY (VerifiedBy) REFERENCES dbo.Users(UserId),
    CONSTRAINT UQ_DrugDiseaseLinks UNIQUE (DrugId, DiseaseId, LinkTypeId)
);
GO

CREATE TABLE dbo.LinkEvidenceReferences (
    LinkEvidenceReferenceId INT IDENTITY(1,1) PRIMARY KEY,
    LinkId INT NOT NULL,
    DataSourceId INT NULL,
    ReferenceType NVARCHAR(50) NULL CHECK (ReferenceType IS NULL OR ReferenceType IN ('PMID','NCT','UMLS','DOI','URL','INTERNAL','OTHER')),
    ReferenceCode NVARCHAR(200) NULL,
    ReferenceUrl NVARCHAR(500) NULL,
    Description NVARCHAR(1000) NULL,
    CONSTRAINT FK_LinkEvidenceReferences_Links FOREIGN KEY (LinkId) REFERENCES dbo.DrugDiseaseLinks(LinkId),
    CONSTRAINT FK_LinkEvidenceReferences_DataSources FOREIGN KEY (DataSourceId) REFERENCES dbo.DataSources(DataSourceId)
);
GO

CREATE TABLE dbo.LinkConfidenceReviews (
    LinkConfidenceReviewId INT IDENTITY(1,1) PRIMARY KEY,
    LinkId INT NOT NULL,
    ConfidenceLevelId INT NOT NULL,
    ReviewerId INT NULL,
    ReviewNote NVARCHAR(1000) NULL,
    ReviewedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_LinkConfidenceReviews_Links FOREIGN KEY (LinkId) REFERENCES dbo.DrugDiseaseLinks(LinkId),
    CONSTRAINT FK_LinkConfidenceReviews_Confidence FOREIGN KEY (ConfidenceLevelId) REFERENCES dbo.ConfidenceLevels(ConfidenceLevelId),
    CONSTRAINT FK_LinkConfidenceReviews_Reviewer FOREIGN KEY (ReviewerId) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.LinkTrainingLabels (
    LinkTrainingLabelId INT IDENTITY(1,1) PRIMARY KEY,
    LinkId INT NULL,
    DrugId INT NOT NULL,
    DiseaseId INT NOT NULL,
    LabelValue TINYINT NOT NULL CHECK (LabelValue IN (0,1)),
    LabelSource NVARCHAR(100) NOT NULL DEFAULT 'KNOWN_LINK',
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_LinkTrainingLabels_Links FOREIGN KEY (LinkId) REFERENCES dbo.DrugDiseaseLinks(LinkId),
    CONSTRAINT FK_LinkTrainingLabels_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT FK_LinkTrainingLabels_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId)
);
GO

/* ==========================================================
   6. NHÓM QUẢN LÝ DATASET, HUẤN LUYỆN, MODEL - BM-07
   ========================================================== */
CREATE TABLE dbo.TrainingDatasets (
    TrainingDatasetId INT IDENTITY(1,1) PRIMARY KEY,
    DatasetCode NVARCHAR(50) NOT NULL UNIQUE, -- VER-/DATA-
    DatasetName NVARCHAR(255) NOT NULL,
    Description NVARCHAR(1000) NULL,
    CreatedBy INT NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2(0) NULL,
    IsDeleted BIT NOT NULL DEFAULT 0,
    CONSTRAINT FK_TrainingDatasets_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.DatasetSources (
    DatasetSourceId INT IDENTITY(1,1) PRIMARY KEY,
    TrainingDatasetId INT NOT NULL,
    DataSourceId INT NOT NULL,
    CONSTRAINT FK_DatasetSources_Datasets FOREIGN KEY (TrainingDatasetId) REFERENCES dbo.TrainingDatasets(TrainingDatasetId),
    CONSTRAINT FK_DatasetSources_DataSources FOREIGN KEY (DataSourceId) REFERENCES dbo.DataSources(DataSourceId),
    CONSTRAINT UQ_DatasetSources UNIQUE (TrainingDatasetId, DataSourceId)
);
GO

CREATE TABLE dbo.DatasetVersions (
    DatasetVersionId INT IDENTITY(1,1) PRIMARY KEY,
    TrainingDatasetId INT NOT NULL,
    VersionCode NVARCHAR(50) NOT NULL UNIQUE, -- VER-
    DrugCount INT NOT NULL DEFAULT 0 CHECK (DrugCount >= 0),
    DiseaseCount INT NOT NULL DEFAULT 0 CHECK (DiseaseCount >= 0),
    PositiveLinkCount INT NOT NULL DEFAULT 0 CHECK (PositiveLinkCount >= 0),
    NegativeUnknownLinkCount INT NOT NULL DEFAULT 0 CHECK (NegativeUnknownLinkCount >= 0),
    DataFilePath NVARCHAR(500) NULL,
    MetadataJson NVARCHAR(MAX) NULL CHECK (MetadataJson IS NULL OR ISJSON(MetadataJson)=1),
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_DatasetVersions_Datasets FOREIGN KEY (TrainingDatasetId) REFERENCES dbo.TrainingDatasets(TrainingDatasetId)
);
GO

CREATE TABLE dbo.DatasetItems (
    DatasetItemId BIGINT IDENTITY(1,1) PRIMARY KEY,
    DatasetVersionId INT NOT NULL,
    DrugId INT NOT NULL,
    DiseaseId INT NOT NULL,
    LabelValue TINYINT NULL CHECK (LabelValue IS NULL OR LabelValue IN (0,1)),
    FeatureVectorJson NVARCHAR(MAX) NULL CHECK (FeatureVectorJson IS NULL OR ISJSON(FeatureVectorJson)=1),
    SplitName NVARCHAR(20) NULL CHECK (SplitName IS NULL OR SplitName IN ('TRAIN','VALIDATION','TEST')),
    SourceLinkId INT NULL,
    CONSTRAINT FK_DatasetItems_DatasetVersions FOREIGN KEY (DatasetVersionId) REFERENCES dbo.DatasetVersions(DatasetVersionId),
    CONSTRAINT FK_DatasetItems_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT FK_DatasetItems_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId),
    CONSTRAINT FK_DatasetItems_Links FOREIGN KEY (SourceLinkId) REFERENCES dbo.DrugDiseaseLinks(LinkId)
);
GO

CREATE TABLE dbo.PreprocessingRuns (
    PreprocessingRunId INT IDENTITY(1,1) PRIMARY KEY,
    DatasetVersionId INT NOT NULL,
    NormalizeDrugName BIT NOT NULL DEFAULT 0,
    NormalizeDiseaseName BIT NOT NULL DEFAULT 0,
    RemoveDuplicates BIT NOT NULL DEFAULT 0,
    AssignStandardCodes BIT NOT NULL DEFAULT 0,
    CreateFeatures BIT NOT NULL DEFAULT 0,
    SplitTrainTest BIT NOT NULL DEFAULT 0,
    ParametersJson NVARCHAR(MAX) NULL CHECK (ParametersJson IS NULL OR ISJSON(ParametersJson)=1),
    RunBy INT NULL,
    RunAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_PreprocessingRuns_DatasetVersions FOREIGN KEY (DatasetVersionId) REFERENCES dbo.DatasetVersions(DatasetVersionId),
    CONSTRAINT FK_PreprocessingRuns_Users FOREIGN KEY (RunBy) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.ModelVersions (
    ModelVersionId INT IDENTITY(1,1) PRIMARY KEY,
    ModelCode NVARCHAR(50) NOT NULL UNIQUE,
    ModelName NVARCHAR(255) NOT NULL,
    AlgorithmId INT NOT NULL,
    VersionLabel NVARCHAR(50) NOT NULL,
    HyperParametersJson NVARCHAR(MAX) NULL CHECK (HyperParametersJson IS NULL OR ISJSON(HyperParametersJson)=1),
    IsCurrent BIT NOT NULL DEFAULT 0,
    CreatedBy INT NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_ModelVersions_Algorithms FOREIGN KEY (AlgorithmId) REFERENCES dbo.ModelAlgorithms(AlgorithmId),
    CONSTRAINT FK_ModelVersions_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.ModelTrainingRuns (
    TrainingRunId INT IDENTITY(1,1) PRIMARY KEY,
    ModelVersionId INT NOT NULL,
    DatasetVersionId INT NOT NULL,
    TrainTestSplit NVARCHAR(50) NULL,
    StartedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    FinishedAt DATETIME2(0) NULL,
    RunStatus NVARCHAR(50) NOT NULL DEFAULT 'RUNNING' CHECK (RunStatus IN ('RUNNING','SUCCESS','FAILED','CANCELLED')),
    Note NVARCHAR(1000) NULL,
    TrainedBy INT NULL,
    CONSTRAINT FK_ModelTrainingRuns_ModelVersions FOREIGN KEY (ModelVersionId) REFERENCES dbo.ModelVersions(ModelVersionId),
    CONSTRAINT FK_ModelTrainingRuns_DatasetVersions FOREIGN KEY (DatasetVersionId) REFERENCES dbo.DatasetVersions(DatasetVersionId),
    CONSTRAINT FK_ModelTrainingRuns_Users FOREIGN KEY (TrainedBy) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.ModelMetrics (
    ModelMetricId INT IDENTITY(1,1) PRIMARY KEY,
    TrainingRunId INT NOT NULL,
    Accuracy DECIMAL(7,4) NULL CHECK (Accuracy IS NULL OR Accuracy BETWEEN 0 AND 1),
    PrecisionScore DECIMAL(7,4) NULL CHECK (PrecisionScore IS NULL OR PrecisionScore BETWEEN 0 AND 1),
    RecallScore DECIMAL(7,4) NULL CHECK (RecallScore IS NULL OR RecallScore BETWEEN 0 AND 1),
    F1Score DECIMAL(7,4) NULL CHECK (F1Score IS NULL OR F1Score BETWEEN 0 AND 1),
    AUC DECIMAL(7,4) NULL CHECK (AUC IS NULL OR AUC BETWEEN 0 AND 1),
    MetricJson NVARCHAR(MAX) NULL CHECK (MetricJson IS NULL OR ISJSON(MetricJson)=1),
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_ModelMetrics_TrainingRuns FOREIGN KEY (TrainingRunId) REFERENCES dbo.ModelTrainingRuns(TrainingRunId)
);
GO

CREATE TABLE dbo.ModelFiles (
    ModelFileId INT IDENTITY(1,1) PRIMARY KEY,
    ModelVersionId INT NOT NULL,
    FileType NVARCHAR(50) NOT NULL CHECK (FileType IN ('MODEL','ENCODER','SCALER','FEATURE_CONFIG','REPORT','OTHER')),
    FilePath NVARCHAR(500) NOT NULL,
    Checksum NVARCHAR(128) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_ModelFiles_ModelVersions FOREIGN KEY (ModelVersionId) REFERENCES dbo.ModelVersions(ModelVersionId)
);
GO

CREATE TABLE dbo.ModelDeploymentDecisions (
    DecisionId INT IDENTITY(1,1) PRIMARY KEY,
    DecisionCode NVARCHAR(50) NOT NULL UNIQUE,
    DecisionName NVARCHAR(150) NOT NULL
);
GO

CREATE TABLE dbo.ModelDeployments (
    ModelDeploymentId INT IDENTITY(1,1) PRIMARY KEY,
    ModelVersionId INT NOT NULL,
    DecisionId INT NOT NULL,
    EnvironmentName NVARCHAR(50) NOT NULL DEFAULT 'DEMO',
    DeploymentStatus NVARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (DeploymentStatus IN ('PENDING','DEPLOYED','REJECTED','ROLLED_BACK')),
    DecisionNote NVARCHAR(1000) NULL,
    DeployedBy INT NULL,
    DeployedAt DATETIME2(0) NULL,
    CONSTRAINT FK_ModelDeployments_ModelVersions FOREIGN KEY (ModelVersionId) REFERENCES dbo.ModelVersions(ModelVersionId),
    CONSTRAINT FK_ModelDeployments_Decisions FOREIGN KEY (DecisionId) REFERENCES dbo.ModelDeploymentDecisions(DecisionId),
    CONSTRAINT FK_ModelDeployments_Users FOREIGN KEY (DeployedBy) REFERENCES dbo.Users(UserId)
);
GO

/* ==========================================================
   7. NHÓM YÊU CẦU DỰ ĐOÁN - BM-04
   ========================================================== */
CREATE TABLE dbo.PredictionRequests (
    PredictionRequestId INT IDENTITY(1,1) PRIMARY KEY,
    RequestCode NVARCHAR(50) NOT NULL UNIQUE, -- REQ-
    RequesterId INT NULL,
    RequesterRoleText NVARCHAR(100) NULL,
    ContactEmail NVARCHAR(255) NULL,
    ContactPhone NVARCHAR(30) NULL,
    PredictionTypeId INT NOT NULL,
    InputDrugId INT NULL,
    InputDiseaseId INT NULL,
    TopK INT NOT NULL DEFAULT 10 CHECK (TopK IN (5,10,20) OR TopK > 0),
    ScoreThreshold DECIMAL(7,4) NULL CHECK (ScoreThreshold IS NULL OR ScoreThreshold BETWEEN 0 AND 1),
    DataPriority NVARCHAR(100) NULL,
    ChannelId INT NULL,
    RequestContent NVARCHAR(MAX) NULL,
    Purpose NVARCHAR(200) NULL,
    MedicalWarningAccepted BIT NOT NULL DEFAULT 0,
    RequestStatus NVARCHAR(50) NOT NULL DEFAULT 'SUBMITTED' CHECK (RequestStatus IN ('SUBMITTED','PROCESSING','COMPLETED','FAILED','CANCELLED')),
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2(0) NULL,
    IsDeleted BIT NOT NULL DEFAULT 0,
    CONSTRAINT FK_PredictionRequests_Users FOREIGN KEY (RequesterId) REFERENCES dbo.Users(UserId),
    CONSTRAINT FK_PredictionRequests_Types FOREIGN KEY (PredictionTypeId) REFERENCES dbo.PredictionTypes(PredictionTypeId),
    CONSTRAINT FK_PredictionRequests_Drugs FOREIGN KEY (InputDrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT FK_PredictionRequests_Diseases FOREIGN KEY (InputDiseaseId) REFERENCES dbo.Diseases(DiseaseId),
    CONSTRAINT FK_PredictionRequests_Channels FOREIGN KEY (ChannelId) REFERENCES dbo.ResultDeliveryChannels(ChannelId),
    CONSTRAINT CK_PredictionRequests_Input CHECK (
        (PredictionTypeId = 1 AND InputDrugId IS NOT NULL) OR
        (PredictionTypeId = 2 AND InputDiseaseId IS NOT NULL) OR
        (PredictionTypeId = 3 AND InputDrugId IS NOT NULL AND InputDiseaseId IS NOT NULL)
    )
);
GO

CREATE TABLE dbo.PredictionRequestParameters (
    PredictionRequestParameterId INT IDENTITY(1,1) PRIMARY KEY,
    PredictionRequestId INT NOT NULL,
    ParamName NVARCHAR(100) NOT NULL,
    ParamValue NVARCHAR(MAX) NULL,
    CONSTRAINT FK_PredictionRequestParameters_Requests FOREIGN KEY (PredictionRequestId) REFERENCES dbo.PredictionRequests(PredictionRequestId),
    CONSTRAINT UQ_PredictionRequestParameters UNIQUE (PredictionRequestId, ParamName)
);
GO

CREATE TABLE dbo.PredictionRequestStatusHistory (
    PredictionRequestStatusHistoryId INT IDENTITY(1,1) PRIMARY KEY,
    PredictionRequestId INT NOT NULL,
    OldStatus NVARCHAR(50) NULL,
    NewStatus NVARCHAR(50) NOT NULL,
    ChangedBy INT NULL,
    ChangedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    Note NVARCHAR(1000) NULL,
    CONSTRAINT FK_RequestStatusHistory_Requests FOREIGN KEY (PredictionRequestId) REFERENCES dbo.PredictionRequests(PredictionRequestId),
    CONSTRAINT FK_RequestStatusHistory_Users FOREIGN KEY (ChangedBy) REFERENCES dbo.Users(UserId)
);
GO

/* ==========================================================
   8. NHÓM KẾT QUẢ DỰ ĐOÁN - BM-05
   ========================================================== */
CREATE TABLE dbo.PredictionRuns (
    PredictionRunId INT IDENTITY(1,1) PRIMARY KEY,
    PredictionRunCode NVARCHAR(50) NOT NULL UNIQUE, -- PRED-
    PredictionRequestId INT NOT NULL,
    ModelVersionId INT NULL,
    ModuleName NVARCHAR(150) NOT NULL DEFAULT 'ML_PREDICTION_MODULE',
    InputSummary NVARCHAR(MAX) NULL,
    ScoreThreshold DECIMAL(7,4) NULL CHECK (ScoreThreshold IS NULL OR ScoreThreshold BETWEEN 0 AND 1),
    SystemComment NVARCHAR(MAX) NULL,
    ProcessingConclusion NVARCHAR(200) NULL,
    MandatoryMedicalWarning NVARCHAR(1000) NOT NULL DEFAULT N'Kết quả dự đoán chỉ phục vụ mục đích hỗ trợ nghiên cứu và tham khảo. Không sử dụng kết quả này như chỉ định điều trị hoặc thay thế ý kiến của bác sĩ/dược sĩ.',
    RunStatus NVARCHAR(50) NOT NULL DEFAULT 'RUNNING' CHECK (RunStatus IN ('RUNNING','SUCCESS','FAILED')),
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_PredictionRuns_Requests FOREIGN KEY (PredictionRequestId) REFERENCES dbo.PredictionRequests(PredictionRequestId),
    CONSTRAINT FK_PredictionRuns_ModelVersions FOREIGN KEY (ModelVersionId) REFERENCES dbo.ModelVersions(ModelVersionId)
);
GO

CREATE TABLE dbo.PredictionResults (
    PredictionResultId INT IDENTITY(1,1) PRIMARY KEY,
    PredictionRunId INT NOT NULL,
    RankNo INT NOT NULL CHECK (RankNo > 0),
    DrugId INT NOT NULL,
    DiseaseId INT NOT NULL,
    PredictionScore DECIMAL(9,6) NOT NULL CHECK (PredictionScore BETWEEN 0 AND 1),
    ConfidenceLevelId INT NULL,
    LinkTypeId INT NULL,
    ShortExplanation NVARCHAR(1000) NULL,
    KnownLinkId INT NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_PredictionResults_Runs FOREIGN KEY (PredictionRunId) REFERENCES dbo.PredictionRuns(PredictionRunId),
    CONSTRAINT FK_PredictionResults_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT FK_PredictionResults_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId),
    CONSTRAINT FK_PredictionResults_Confidence FOREIGN KEY (ConfidenceLevelId) REFERENCES dbo.ConfidenceLevels(ConfidenceLevelId),
    CONSTRAINT FK_PredictionResults_LinkTypes FOREIGN KEY (LinkTypeId) REFERENCES dbo.LinkTypes(LinkTypeId),
    CONSTRAINT FK_PredictionResults_KnownLinks FOREIGN KEY (KnownLinkId) REFERENCES dbo.DrugDiseaseLinks(LinkId),
    CONSTRAINT UQ_PredictionResults UNIQUE (PredictionRunId, RankNo)
);
GO

CREATE TABLE dbo.PredictionResultEvidence (
    PredictionResultEvidenceId INT IDENTITY(1,1) PRIMARY KEY,
    PredictionResultId INT NOT NULL,
    DataSourceId INT NULL,
    EvidenceText NVARCHAR(1000) NULL,
    ReferenceUrl NVARCHAR(500) NULL,
    CONSTRAINT FK_ResultEvidence_Results FOREIGN KEY (PredictionResultId) REFERENCES dbo.PredictionResults(PredictionResultId),
    CONSTRAINT FK_ResultEvidence_DataSources FOREIGN KEY (DataSourceId) REFERENCES dbo.DataSources(DataSourceId)
);
GO

CREATE TABLE dbo.PredictionExplanations (
    PredictionExplanationId INT IDENTITY(1,1) PRIMARY KEY,
    PredictionResultId INT NOT NULL,
    ExplanationType NVARCHAR(100) NULL,
    ExplanationText NVARCHAR(MAX) NOT NULL,
    FeatureContributionJson NVARCHAR(MAX) NULL CHECK (FeatureContributionJson IS NULL OR ISJSON(FeatureContributionJson)=1),
    CONSTRAINT FK_PredictionExplanations_Results FOREIGN KEY (PredictionResultId) REFERENCES dbo.PredictionResults(PredictionResultId)
);
GO

CREATE TABLE dbo.PredictionWarnings (
    PredictionWarningId INT IDENTITY(1,1) PRIMARY KEY,
    PredictionRunId INT NOT NULL,
    WarningType NVARCHAR(100) NOT NULL,
    WarningText NVARCHAR(1000) NOT NULL,
    IsMandatory BIT NOT NULL DEFAULT 1,
    CONSTRAINT FK_PredictionWarnings_Runs FOREIGN KEY (PredictionRunId) REFERENCES dbo.PredictionRuns(PredictionRunId)
);
GO

CREATE TABLE dbo.PredictionHistory (
    PredictionHistoryId BIGINT IDENTITY(1,1) PRIMARY KEY,
    UserId INT NULL,
    PredictionRequestId INT NOT NULL,
    PredictionRunId INT NULL,
    ActionName NVARCHAR(100) NOT NULL,
    ActionAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    Note NVARCHAR(1000) NULL,
    CONSTRAINT FK_PredictionHistory_Users FOREIGN KEY (UserId) REFERENCES dbo.Users(UserId),
    CONSTRAINT FK_PredictionHistory_Requests FOREIGN KEY (PredictionRequestId) REFERENCES dbo.PredictionRequests(PredictionRequestId),
    CONSTRAINT FK_PredictionHistory_Runs FOREIGN KEY (PredictionRunId) REFERENCES dbo.PredictionRuns(PredictionRunId)
);
GO

/* ==========================================================
   9. NHÓM PHẢN HỒI KẾT QUẢ - BM-06
   ========================================================== */
CREATE TABLE dbo.PredictionFeedbacks (
    FeedbackId INT IDENTITY(1,1) PRIMARY KEY,
    FeedbackCode NVARCHAR(50) NOT NULL UNIQUE, -- FB-
    PredictionRunId INT NOT NULL,
    PredictionResultId INT NULL,
    FeedbackUserId INT NULL,
    FeedbackRoleText NVARCHAR(100) NULL,
    DrugId INT NULL,
    DiseaseId INT NULL,
    GeneralAssessment NVARCHAR(100) NOT NULL CHECK (GeneralAssessment IN (N'Hợp lý',N'Chưa hợp lý',N'Cần kiểm chứng thêm',N'Không đủ thông tin để đánh giá')),
    UsefulScore TINYINT NULL CHECK (UsefulScore IS NULL OR UsefulScore BETWEEN 1 AND 5),
    SuggestedAction NVARCHAR(200) NULL,
    ReasonText NVARCHAR(MAX) NULL,
    DepartmentOpinion NVARCHAR(200) NULL,
    FeedbackStatusId INT NOT NULL DEFAULT 1,
    ProcessedBy INT NULL,
    ProcessedAt DATETIME2(0) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2(0) NULL,
    IsDeleted BIT NOT NULL DEFAULT 0,
    CONSTRAINT FK_Feedbacks_Runs FOREIGN KEY (PredictionRunId) REFERENCES dbo.PredictionRuns(PredictionRunId),
    CONSTRAINT FK_Feedbacks_Results FOREIGN KEY (PredictionResultId) REFERENCES dbo.PredictionResults(PredictionResultId),
    CONSTRAINT FK_Feedbacks_Users FOREIGN KEY (FeedbackUserId) REFERENCES dbo.Users(UserId),
    CONSTRAINT FK_Feedbacks_Drugs FOREIGN KEY (DrugId) REFERENCES dbo.Drugs(DrugId),
    CONSTRAINT FK_Feedbacks_Diseases FOREIGN KEY (DiseaseId) REFERENCES dbo.Diseases(DiseaseId),
    CONSTRAINT FK_Feedbacks_Status FOREIGN KEY (FeedbackStatusId) REFERENCES dbo.FeedbackStatuses(FeedbackStatusId),
    CONSTRAINT FK_Feedbacks_ProcessedBy FOREIGN KEY (ProcessedBy) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.FeedbackReferences (
    FeedbackReferenceId INT IDENTITY(1,1) PRIMARY KEY,
    FeedbackId INT NOT NULL,
    ReferenceText NVARCHAR(1000) NULL,
    ReferenceUrl NVARCHAR(500) NULL,
    DataSourceId INT NULL,
    CONSTRAINT FK_FeedbackReferences_Feedbacks FOREIGN KEY (FeedbackId) REFERENCES dbo.PredictionFeedbacks(FeedbackId),
    CONSTRAINT FK_FeedbackReferences_DataSources FOREIGN KEY (DataSourceId) REFERENCES dbo.DataSources(DataSourceId)
);
GO

CREATE TABLE dbo.FeedbackStatusHistory (
    FeedbackStatusHistoryId INT IDENTITY(1,1) PRIMARY KEY,
    FeedbackId INT NOT NULL,
    OldStatusId INT NULL,
    NewStatusId INT NOT NULL,
    ChangedBy INT NULL,
    ChangedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    Note NVARCHAR(1000) NULL,
    CONSTRAINT FK_FeedbackStatusHistory_Feedbacks FOREIGN KEY (FeedbackId) REFERENCES dbo.PredictionFeedbacks(FeedbackId),
    CONSTRAINT FK_FeedbackStatusHistory_OldStatus FOREIGN KEY (OldStatusId) REFERENCES dbo.FeedbackStatuses(FeedbackStatusId),
    CONSTRAINT FK_FeedbackStatusHistory_NewStatus FOREIGN KEY (NewStatusId) REFERENCES dbo.FeedbackStatuses(FeedbackStatusId),
    CONSTRAINT FK_FeedbackStatusHistory_Users FOREIGN KEY (ChangedBy) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.FeedbackActions (
    FeedbackActionId INT IDENTITY(1,1) PRIMARY KEY,
    FeedbackId INT NOT NULL,
    ActionType NVARCHAR(100) NOT NULL CHECK (ActionType IN ('KEEP_RESULT','UPDATE_SOURCE','REMOVE_SUGGESTION','ADD_TO_VALIDATION','OTHER')),
    ActionNote NVARCHAR(1000) NULL,
    ActionBy INT NULL,
    ActionAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_FeedbackActions_Feedbacks FOREIGN KEY (FeedbackId) REFERENCES dbo.PredictionFeedbacks(FeedbackId),
    CONSTRAINT FK_FeedbackActions_Users FOREIGN KEY (ActionBy) REFERENCES dbo.Users(UserId)
);
GO

CREATE TABLE dbo.FeedbackModelImprovementLogs (
    ImprovementLogId INT IDENTITY(1,1) PRIMARY KEY,
    FeedbackId INT NOT NULL,
    DatasetVersionId INT NULL,
    ModelVersionId INT NULL,
    ImprovementType NVARCHAR(100) NOT NULL CHECK (ImprovementType IN ('ADD_DATA','UPDATE_LABEL','RETRAIN_MODEL','CHANGE_FEATURE','OTHER')),
    ImprovementNote NVARCHAR(1000) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_ImprovementLogs_Feedbacks FOREIGN KEY (FeedbackId) REFERENCES dbo.PredictionFeedbacks(FeedbackId),
    CONSTRAINT FK_ImprovementLogs_DatasetVersions FOREIGN KEY (DatasetVersionId) REFERENCES dbo.DatasetVersions(DatasetVersionId),
    CONSTRAINT FK_ImprovementLogs_ModelVersions FOREIGN KEY (ModelVersionId) REFERENCES dbo.ModelVersions(ModelVersionId)
);
GO

/* ==========================================================
   10. INDEX TỐI ƯU TRUY VẤN
   ========================================================== */
CREATE INDEX IX_Drugs_ActiveName ON dbo.Drugs(ActiveName) INCLUDE (DrugCode, TradeName);
CREATE INDEX IX_Diseases_DiseaseName ON dbo.Diseases(DiseaseName) INCLUDE (DiseaseCode);
CREATE INDEX IX_DrugDiseaseLinks_Drug ON dbo.DrugDiseaseLinks(DrugId, LinkTypeId, EvidenceStatusId);
CREATE INDEX IX_DrugDiseaseLinks_Disease ON dbo.DrugDiseaseLinks(DiseaseId, LinkTypeId, EvidenceStatusId);
CREATE INDEX IX_PredictionRequests_UserDate ON dbo.PredictionRequests(RequesterId, CreatedAt DESC);
CREATE INDEX IX_PredictionRuns_Request ON dbo.PredictionRuns(PredictionRequestId, CreatedAt DESC);
CREATE INDEX IX_PredictionResults_RunRank ON dbo.PredictionResults(PredictionRunId, RankNo);
CREATE INDEX IX_PredictionFeedbacks_Status ON dbo.PredictionFeedbacks(FeedbackStatusId, CreatedAt DESC);
CREATE INDEX IX_ModelDeployments_Status ON dbo.ModelDeployments(DeploymentStatus, DeployedAt DESC);
GO

/* ==========================================================
   11. DỮ LIỆU MẪU LOOKUP
   ========================================================== */
INSERT INTO dbo.Roles(RoleCode, RoleName) VALUES
('USER',N'Người dùng'),('RESEARCHER',N'Nhà nghiên cứu'),('DOCTOR_PHARMACIST',N'Bác sĩ/Dược sĩ'),
('ADMIN',N'Admin'),('DATA_TEAM',N'Nhóm dữ liệu'),('EXPERT',N'Chuyên gia'),('ML_TEAM',N'Nhóm ML');

INSERT INTO dbo.DataSources(SourceCode, SourceName, SourceUrl) VALUES
('DRUGBANK',N'DrugBank',N'https://go.drugbank.com'),('DRUGCENTRAL',N'DrugCentral',N'https://drugcentral.org'),
('CTD',N'Comparative Toxicogenomics Database',N'https://ctdbase.org'),('REPO_DB',N'repoDB',NULL),
('CLINICAL_TRIALS',N'ClinicalTrials.gov',N'https://clinicaltrials.gov'),('OPENFDA',N'openFDA',N'https://open.fda.gov'),
('DISGENET',N'DisGeNET',N'https://www.disgenet.org'),('SCIENTIFIC_PAPER',N'Tài liệu khoa học',NULL),('INTERNAL',N'CSDL nội bộ',NULL);

INSERT INTO dbo.ApprovalStatuses(StatusCode, StatusName) VALUES
('APPROVED',N'Đã phê duyệt'),('TRIAL',N'Đang thử nghiệm'),('OFF_LABEL',N'Off-label'),('WITHDRAWN',N'Ngừng sử dụng'),('UNKNOWN',N'Chưa rõ');

INSERT INTO dbo.ReviewStatuses(StatusCode, StatusName) VALUES
('PENDING',N'Chờ kiểm duyệt'),('APPROVED',N'Đã duyệt'),('REJECTED',N'Từ chối'),('NEED_REVIEW',N'Cần xem lại');

INSERT INTO dbo.ConfidenceLevels(LevelCode, LevelName, MinScore, MaxScore) VALUES
('LOW',N'Thấp',0.0000,0.4999),('MEDIUM',N'Trung bình',0.5000,0.6999),('HIGH',N'Cao',0.7000,1.0000);

INSERT INTO dbo.DrugGroups(GroupCode, GroupName) VALUES
('ANTIBIOTIC',N'Kháng sinh'),('ANTI_INFLAMMATORY',N'Kháng viêm'),('CARDIO',N'Tim mạch'),('METABOLIC',N'Chuyển hóa'),('CANCER',N'Ung thư'),('NEURO',N'Thần kinh'),('OTHER',N'Khác');

INSERT INTO dbo.DiseaseGroups(GroupCode, GroupName) VALUES
('CARDIO',N'Tim mạch'),('METABOLIC',N'Chuyển hóa'),('CANCER',N'Ung thư'),('NEURO',N'Thần kinh'),('INFECTIOUS',N'Truyền nhiễm'),('IMMUNE',N'Miễn dịch'),('OTHER',N'Khác');

INSERT INTO dbo.AdministrationRoutes(RouteCode, RouteName) VALUES
('ORAL',N'Uống'),('INJECTION',N'Tiêm'),('INFUSION',N'Truyền'),('TOPICAL',N'Bôi ngoài da'),('INHALED',N'Hít'),('OTHER',N'Khác');

INSERT INTO dbo.LinkTypes(LinkTypeCode, LinkTypeName) VALUES
('INDICATION',N'Chỉ định điều trị'),('CONTRAINDICATION',N'Chống chỉ định'),('SIDE_EFFECT',N'Tác dụng phụ'),('OFF_LABEL',N'Off-label'),('CLINICAL_TRIAL',N'Thử nghiệm lâm sàng'),('FAILED_TRIAL',N'Thất bại thử nghiệm');

INSERT INTO dbo.EvidenceStatuses(EvidenceStatusCode, EvidenceStatusName) VALUES
('APPROVED',N'Đã phê duyệt'),('SUPPORTED_STUDY',N'Có nghiên cứu hỗ trợ'),('TRIAL',N'Đang thử nghiệm'),('INFERRED',N'Dữ liệu suy luận'),('UNVERIFIED',N'Chưa kiểm chứng');

INSERT INTO dbo.PredictionTypes(PredictionTypeCode, PredictionTypeName) VALUES
('DRUG_TO_DISEASE',N'Từ thuốc tìm bệnh liên quan'),('DISEASE_TO_DRUG',N'Từ bệnh tìm thuốc tiềm năng'),('PAIR_PREDICTION',N'Dự đoán một cặp thuốc – bệnh cụ thể');

INSERT INTO dbo.ResultDeliveryChannels(ChannelCode, ChannelName) VALUES
('WEB',N'Xem trên web'),('EXCEL_CSV',N'Xuất Excel/CSV'),('EMAIL',N'Email'),('OTHER',N'Khác');

INSERT INTO dbo.ModelAlgorithms(AlgorithmCode, AlgorithmName) VALUES
('LOGISTIC_REGRESSION',N'Logistic Regression'),('RANDOM_FOREST',N'Random Forest'),('SVM',N'SVM'),('NEURAL_NETWORK',N'Neural Network'),('GRAPH_ML',N'Graph ML'),('MATRIX_FACTORIZATION',N'Matrix Factorization'),('XGBOOST',N'XGBoost');

INSERT INTO dbo.FeedbackStatuses(StatusCode, StatusName) VALUES
('NEW',N'Chưa xem'),('PROCESSING',N'Đang xử lý'),('DATA_UPDATED',N'Đã cập nhật dữ liệu'),('RESPONDED',N'Đã phản hồi người dùng'),('CLOSED',N'Đóng phản hồi');

INSERT INTO dbo.ModelDeploymentDecisions(DecisionCode, DecisionName) VALUES
('READY_FOR_TRIAL',N'Đạt yêu cầu triển khai thử nghiệm'),('NEED_MORE_DATA',N'Cần bổ sung dữ liệu'),('CHANGE_MODEL',N'Cần đổi mô hình'),('NOT_USED',N'Chưa sử dụng');

INSERT INTO dbo.FeatureDefinitions(EntityType, FeatureCode, FeatureName, DataType, EncodingMethod) VALUES
('DRUG','DRUG_GROUP',N'Nhóm thuốc','NVARCHAR','ONE_HOT'),('DRUG','TARGET_GENE',N'Target/gene thuốc','JSON','EMBEDDING'),
('DISEASE','DISEASE_GROUP',N'Nhóm bệnh','NVARCHAR','ONE_HOT'),('DISEASE','GENE_PATHWAY',N'Gene/pathway bệnh','JSON','EMBEDDING'),
('PAIR','DRUG_DISEASE_MATRIX',N'Ma trận thuốc - bệnh','JSON','MATRIX');
GO

/* ==========================================================
   12. DỮ LIỆU MẪU NGHIỆP VỤ
   ========================================================== */
INSERT INTO dbo.Users(UserCode, FullName, Email, Phone, PasswordHash) VALUES
('U-ADMIN-01',N'Quản trị viên hệ thống','admin@drugml.local','0900000001','HASH_SAMPLE'),
('U-ML-01',N'Thành viên nhóm ML','mlteam@drugml.local','0900000002','HASH_SAMPLE'),
('U-USER-01',N'Người dùng nghiên cứu','researcher@drugml.local','0900000003','HASH_SAMPLE');

INSERT INTO dbo.UserRoles(UserId, RoleId) VALUES (1,4),(1,5),(2,7),(3,2);

INSERT INTO dbo.Drugs(DrugCode, ActiveName, TradeName, DrugGroupId, DosageFormStrength, RouteId, ApprovalStatusId, MechanismOfAction, KnownIndications, ConfidenceLevelId, ReviewStatusId, CreatedBy)
VALUES ('DRUG-0001',N'Metformin',N'Glucophage',4,N'500mg tablet',1,1,N'Giảm sản xuất glucose ở gan và cải thiện độ nhạy insulin.',N'Điều trị đái tháo đường type 2.',3,2,1),
       ('DRUG-0002',N'Aspirin',N'Bayer Aspirin',2,N'81mg tablet',1,1,N'Ức chế cyclooxygenase và giảm tổng hợp prostaglandin.',N'Giảm đau, kháng viêm, dự phòng biến cố tim mạch.',3,2,1);

INSERT INTO dbo.DrugExternalCodes(DrugId, DataSourceId, ExternalCode) VALUES (1,1,'DB00331'),(2,1,'DB00945');
INSERT INTO dbo.DrugTargets(DrugId, TargetName, TargetType) VALUES (1,'AMPK','PROTEIN'),(2,'PTGS1','GENE'),(2,'PTGS2','GENE');
INSERT INTO dbo.DrugSources(DrugId, DataSourceId) VALUES (1,1),(1,2),(2,1),(2,6);

INSERT INTO dbo.Diseases(DiseaseCode, DiseaseName, DiseaseGroupId, PrevalenceLevel, Description, Symptoms, KnownTreatments, ConfidenceLevelId, ReviewStatusId, CreatedBy)
VALUES ('DIS-0001',N'Đái tháo đường type 2',2,N'Phổ biến',N'Rối loạn chuyển hóa mạn tính gây tăng đường huyết.',N'Khát nước, tiểu nhiều, mệt mỏi.',N'Metformin, thay đổi lối sống.',3,2,1),
       ('DIS-0002',N'Bệnh tim mạch do xơ vữa',1,N'Phổ biến',N'Nhóm bệnh liên quan đến xơ vữa động mạch.',N'Đau ngực, khó thở.',N'Aspirin, statin.',3,2,1);

INSERT INTO dbo.DiseaseExternalCodes(DiseaseId, DataSourceId, ExternalCode) VALUES (1,7,'C0011860'),(2,7,'C0004153');
INSERT INTO dbo.DiseaseGenes(DiseaseId, GeneSymbol, GeneName) VALUES (1,'TCF7L2','Transcription Factor 7 Like 2'),(2,'APOE','Apolipoprotein E');
INSERT INTO dbo.DiseaseSources(DiseaseId, DataSourceId) VALUES (1,7),(2,7),(2,3);

INSERT INTO dbo.DrugDiseaseLinks(LinkCode, DrugId, DiseaseId, LinkTypeId, EvidenceStatusId, ConfidenceLevelId, SourceScore, FormationBasis, EvidenceDescription, ReviewStatusId, VerifiedBy, VerifiedRole, VerifiedAt, CreatedBy)
VALUES ('LINK-0001',1,1,1,1,3,0.9500,N'Đã có chỉ định điều trị',N'Metformin là thuốc điều trị đầu tay cho đái tháo đường type 2.',2,1,N'Admin dữ liệu',SYSUTCDATETIME(),1),
       ('LINK-0002',2,2,1,2,3,0.8800,N'Có nghiên cứu hỗ trợ',N'Aspirin được dùng trong dự phòng biến cố tim mạch ở một số nhóm bệnh nhân.',2,1,N'Chuyên gia',SYSUTCDATETIME(),1);

INSERT INTO dbo.LinkEvidenceReferences(LinkId, DataSourceId, ReferenceType, ReferenceCode, ReferenceUrl) VALUES
(1,1,'URL','DrugBank-DB00331','https://go.drugbank.com/drugs/DB00331'),
(2,6,'URL','openFDA-Aspirin','https://open.fda.gov');

INSERT INTO dbo.LinkTrainingLabels(LinkId, DrugId, DiseaseId, LabelValue) VALUES (1,1,1,1),(2,2,2,1),(NULL,1,2,0),(NULL,2,1,0);

INSERT INTO dbo.TrainingDatasets(DatasetCode, DatasetName, Description, CreatedBy) VALUES ('DATA-0001',N'Dataset thuốc-bệnh mẫu',N'Dataset minh họa cho demo hệ thống.',2);
INSERT INTO dbo.DatasetSources(TrainingDatasetId, DataSourceId) VALUES (1,1),(1,3),(1,7);
INSERT INTO dbo.DatasetVersions(TrainingDatasetId, VersionCode, DrugCount, DiseaseCount, PositiveLinkCount, NegativeUnknownLinkCount, DataFilePath, MetadataJson)
VALUES (1,'VER-0001',2,2,2,2,N'/data/processed/drug_disease_v1.csv',N'{"note":"sample dataset"}');
INSERT INTO dbo.DatasetItems(DatasetVersionId, DrugId, DiseaseId, LabelValue, FeatureVectorJson, SplitName, SourceLinkId) VALUES
(1,1,1,1,N'{"x":[1,0,1]}','TRAIN',1),(1,2,2,1,N'{"x":[0,1,1]}','TRAIN',2),(1,1,2,0,N'{"x":[1,1,0]}','TEST',NULL);
INSERT INTO dbo.PreprocessingRuns(DatasetVersionId, NormalizeDrugName, NormalizeDiseaseName, RemoveDuplicates, AssignStandardCodes, CreateFeatures, SplitTrainTest, RunBy)
VALUES (1,1,1,1,1,1,1,2);

INSERT INTO dbo.ModelVersions(ModelCode, ModelName, AlgorithmId, VersionLabel, HyperParametersJson, IsCurrent, CreatedBy)
VALUES ('MODEL-0001',N'Random Forest thuốc-bệnh',2,'v1.0',N'{"n_estimators":100,"max_depth":8}',1,2);
INSERT INTO dbo.ModelTrainingRuns(ModelVersionId, DatasetVersionId, TrainTestSplit, FinishedAt, RunStatus, Note, TrainedBy)
VALUES (1,1,'80/20',SYSUTCDATETIME(),'SUCCESS',N'Model demo đạt yêu cầu.',2);
INSERT INTO dbo.ModelMetrics(TrainingRunId, Accuracy, PrecisionScore, RecallScore, F1Score, AUC)
VALUES (1,0.8600,0.8400,0.8200,0.8300,0.9000);
INSERT INTO dbo.ModelFiles(ModelVersionId, FileType, FilePath) VALUES (1,'MODEL',N'/models/random_forest_v1.pkl'),(1,'REPORT',N'/outputs/metrics_v1.json');
INSERT INTO dbo.ModelDeployments(ModelVersionId, DecisionId, EnvironmentName, DeploymentStatus, DecisionNote, DeployedBy, DeployedAt)
VALUES (1,1,'DEMO','DEPLOYED',N'Cho phép dùng trong bản demo.',2,SYSUTCDATETIME());

INSERT INTO dbo.PredictionRequests(RequestCode, RequesterId, RequesterRoleText, ContactEmail, PredictionTypeId, InputDrugId, TopK, ScoreThreshold, DataPriority, ChannelId, RequestContent, Purpose, MedicalWarningAccepted)
VALUES ('REQ-0001',3,N'Nhà nghiên cứu','researcher@drugml.local',1,1,5,0.5000,N'Ưu tiên dữ liệu mới',1,N'Tìm bệnh liên quan đến Metformin',N'Nghiên cứu',1);
INSERT INTO dbo.PredictionRuns(PredictionRunCode, PredictionRequestId, ModelVersionId, InputSummary, ScoreThreshold, SystemComment, ProcessingConclusion, RunStatus)
VALUES ('PRED-0001',1,1,N'Input drug: Metformin',0.5000,N'Kết quả demo từ model Random Forest.',N'Lưu lịch sử dự đoán','SUCCESS');
INSERT INTO dbo.PredictionResults(PredictionRunId, RankNo, DrugId, DiseaseId, PredictionScore, ConfidenceLevelId, LinkTypeId, ShortExplanation, KnownLinkId)
VALUES (1,1,1,1,0.930000,3,1,N'Liên kết có bằng chứng điều trị đã biết và điểm dự đoán cao.',1),
       (1,2,1,2,0.420000,1,1,N'Điểm dự đoán thấp, chỉ dùng để tham khảo.',NULL);
INSERT INTO dbo.PredictionWarnings(PredictionRunId, WarningType, WarningText)
VALUES (1,'MEDICAL_DISCLAIMER',N'Kết quả dự đoán chỉ dùng để tham khảo, không thay thế tư vấn bác sĩ/dược sĩ.');
INSERT INTO dbo.PredictionHistory(UserId, PredictionRequestId, PredictionRunId, ActionName, Note)
VALUES (3,1,1,'VIEW_RESULT',N'Người dùng xem kết quả dự đoán.');

INSERT INTO dbo.PredictionFeedbacks(FeedbackCode, PredictionRunId, PredictionResultId, FeedbackUserId, FeedbackRoleText, DrugId, DiseaseId, GeneralAssessment, UsefulScore, SuggestedAction, ReasonText, FeedbackStatusId)
VALUES ('FB-0001',1,1,3,N'Nhà nghiên cứu',1,1,N'Hợp lý',5,N'Giữ kết quả',N'Kết quả phù hợp với liên kết đã biết.',1);
GO

/* ==========================================================
   13. VIEW PHỤC VỤ TRA CỨU
   ========================================================== */
CREATE OR ALTER VIEW dbo.vw_DrugDetails AS
SELECT d.DrugId, d.DrugCode, d.ActiveName, d.TradeName, dg.GroupName AS DrugGroup, ar.RouteName,
       aps.StatusName AS ApprovalStatus, cl.LevelName AS ConfidenceLevel, rs.StatusName AS ReviewStatus,
       d.MechanismOfAction, d.KnownIndications, d.SideEffectsWarnings, d.ContraindicationsInteractions
FROM dbo.Drugs d
LEFT JOIN dbo.DrugGroups dg ON d.DrugGroupId = dg.DrugGroupId
LEFT JOIN dbo.AdministrationRoutes ar ON d.RouteId = ar.RouteId
LEFT JOIN dbo.ApprovalStatuses aps ON d.ApprovalStatusId = aps.ApprovalStatusId
LEFT JOIN dbo.ConfidenceLevels cl ON d.ConfidenceLevelId = cl.ConfidenceLevelId
LEFT JOIN dbo.ReviewStatuses rs ON d.ReviewStatusId = rs.ReviewStatusId
WHERE d.IsDeleted = 0;
GO

CREATE OR ALTER VIEW dbo.vw_DiseaseDetails AS
SELECT ds.DiseaseId, ds.DiseaseCode, ds.DiseaseName, dg.GroupName AS DiseaseGroup, ds.PrevalenceLevel,
       cl.LevelName AS ConfidenceLevel, rs.StatusName AS ReviewStatus, ds.Description, ds.Symptoms, ds.KnownTreatments
FROM dbo.Diseases ds
LEFT JOIN dbo.DiseaseGroups dg ON ds.DiseaseGroupId = dg.DiseaseGroupId
LEFT JOIN dbo.ConfidenceLevels cl ON ds.ConfidenceLevelId = cl.ConfidenceLevelId
LEFT JOIN dbo.ReviewStatuses rs ON ds.ReviewStatusId = rs.ReviewStatusId
WHERE ds.IsDeleted = 0;
GO

CREATE OR ALTER VIEW dbo.vw_KnownDrugDiseaseLinks AS
SELECT l.LinkId, l.LinkCode, d.DrugCode, d.ActiveName, dis.DiseaseCode, dis.DiseaseName,
       lt.LinkTypeName, es.EvidenceStatusName, cl.LevelName AS ConfidenceLevel, l.SourceScore, l.FormationBasis, l.EvidenceDescription
FROM dbo.DrugDiseaseLinks l
JOIN dbo.Drugs d ON l.DrugId = d.DrugId
JOIN dbo.Diseases dis ON l.DiseaseId = dis.DiseaseId
JOIN dbo.LinkTypes lt ON l.LinkTypeId = lt.LinkTypeId
JOIN dbo.EvidenceStatuses es ON l.EvidenceStatusId = es.EvidenceStatusId
LEFT JOIN dbo.ConfidenceLevels cl ON l.ConfidenceLevelId = cl.ConfidenceLevelId
WHERE l.IsDeleted = 0;
GO

CREATE OR ALTER VIEW dbo.vw_PredictionHistory AS
SELECT ph.PredictionHistoryId, u.FullName, pr.RequestCode, run.PredictionRunCode, ph.ActionName, ph.ActionAt, ph.Note
FROM dbo.PredictionHistory ph
LEFT JOIN dbo.Users u ON ph.UserId = u.UserId
JOIN dbo.PredictionRequests pr ON ph.PredictionRequestId = pr.PredictionRequestId
LEFT JOIN dbo.PredictionRuns run ON ph.PredictionRunId = run.PredictionRunId;
GO

CREATE OR ALTER VIEW dbo.vw_PredictionResultDetails AS
SELECT run.PredictionRunCode, res.RankNo, d.ActiveName, dis.DiseaseName, res.PredictionScore,
       cl.LevelName AS ConfidenceLevel, lt.LinkTypeName, res.ShortExplanation, run.MandatoryMedicalWarning
FROM dbo.PredictionResults res
JOIN dbo.PredictionRuns run ON res.PredictionRunId = run.PredictionRunId
JOIN dbo.Drugs d ON res.DrugId = d.DrugId
JOIN dbo.Diseases dis ON res.DiseaseId = dis.DiseaseId
LEFT JOIN dbo.ConfidenceLevels cl ON res.ConfidenceLevelId = cl.ConfidenceLevelId
LEFT JOIN dbo.LinkTypes lt ON res.LinkTypeId = lt.LinkTypeId;
GO

CREATE OR ALTER VIEW dbo.vw_TrainingDatasetSummary AS
SELECT td.DatasetCode, td.DatasetName, dv.VersionCode, dv.DrugCount, dv.DiseaseCount, dv.PositiveLinkCount, dv.NegativeUnknownLinkCount, dv.CreatedAt
FROM dbo.TrainingDatasets td
JOIN dbo.DatasetVersions dv ON td.TrainingDatasetId = dv.TrainingDatasetId;
GO

CREATE OR ALTER VIEW dbo.vw_ModelEvaluationSummary AS
SELECT mv.ModelCode, mv.ModelName, ma.AlgorithmName, mv.VersionLabel, mtr.RunStatus,
       mm.Accuracy, mm.PrecisionScore, mm.RecallScore, mm.F1Score, mm.AUC, mtr.FinishedAt
FROM dbo.ModelVersions mv
JOIN dbo.ModelAlgorithms ma ON mv.AlgorithmId = ma.AlgorithmId
LEFT JOIN dbo.ModelTrainingRuns mtr ON mv.ModelVersionId = mtr.ModelVersionId
LEFT JOIN dbo.ModelMetrics mm ON mtr.TrainingRunId = mm.TrainingRunId;
GO

CREATE OR ALTER VIEW dbo.vw_FeedbackForModelImprovement AS
SELECT fb.FeedbackCode, fb.GeneralAssessment, fb.UsefulScore, fb.SuggestedAction, fs.StatusName,
       d.ActiveName, dis.DiseaseName, fb.ReasonText, fb.CreatedAt
FROM dbo.PredictionFeedbacks fb
JOIN dbo.FeedbackStatuses fs ON fb.FeedbackStatusId = fs.FeedbackStatusId
LEFT JOIN dbo.Drugs d ON fb.DrugId = d.DrugId
LEFT JOIN dbo.Diseases dis ON fb.DiseaseId = dis.DiseaseId
WHERE fb.IsDeleted = 0;
GO

/* ==========================================================
   14. STORED PROCEDURE CHÍNH
   ========================================================== */
CREATE OR ALTER PROCEDURE dbo.sp_CreateDrug
    @DrugCode NVARCHAR(50), @ActiveName NVARCHAR(255), @TradeName NVARCHAR(255)=NULL,
    @DrugGroupId INT=NULL, @RouteId INT=NULL, @ApprovalStatusId INT=NULL, @CreatedBy INT=NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.Drugs(DrugCode, ActiveName, TradeName, DrugGroupId, RouteId, ApprovalStatusId, CreatedBy)
    VALUES(@DrugCode, @ActiveName, @TradeName, @DrugGroupId, @RouteId, @ApprovalStatusId, @CreatedBy);
    SELECT SCOPE_IDENTITY() AS DrugId;
END
GO

CREATE OR ALTER PROCEDURE dbo.sp_CreateDisease
    @DiseaseCode NVARCHAR(50), @DiseaseName NVARCHAR(255), @DiseaseGroupId INT=NULL,
    @PrevalenceLevel NVARCHAR(50)=NULL, @CreatedBy INT=NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.Diseases(DiseaseCode, DiseaseName, DiseaseGroupId, PrevalenceLevel, CreatedBy)
    VALUES(@DiseaseCode, @DiseaseName, @DiseaseGroupId, @PrevalenceLevel, @CreatedBy);
    SELECT SCOPE_IDENTITY() AS DiseaseId;
END
GO

CREATE OR ALTER PROCEDURE dbo.sp_CreateKnownDrugDiseaseLink
    @LinkCode NVARCHAR(50), @DrugId INT, @DiseaseId INT, @LinkTypeId INT, @EvidenceStatusId INT,
    @ConfidenceLevelId INT=NULL, @SourceScore DECIMAL(7,4)=NULL, @FormationBasis NVARCHAR(500)=NULL,
    @EvidenceDescription NVARCHAR(MAX)=NULL, @VerifiedBy INT=NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.DrugDiseaseLinks(LinkCode, DrugId, DiseaseId, LinkTypeId, EvidenceStatusId, ConfidenceLevelId, SourceScore, FormationBasis, EvidenceDescription, VerifiedBy, VerifiedAt, ReviewStatusId)
    VALUES(@LinkCode, @DrugId, @DiseaseId, @LinkTypeId, @EvidenceStatusId, @ConfidenceLevelId, @SourceScore, @FormationBasis, @EvidenceDescription, @VerifiedBy, SYSUTCDATETIME(), 2);
    SELECT SCOPE_IDENTITY() AS LinkId;
END
GO

CREATE OR ALTER PROCEDURE dbo.sp_SubmitPredictionRequest
    @RequestCode NVARCHAR(50), @RequesterId INT=NULL, @PredictionTypeId INT, @InputDrugId INT=NULL, @InputDiseaseId INT=NULL,
    @TopK INT=10, @ScoreThreshold DECIMAL(7,4)=NULL, @ChannelId INT=1, @RequestContent NVARCHAR(MAX)=NULL, @Purpose NVARCHAR(200)=NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.PredictionRequests(RequestCode, RequesterId, PredictionTypeId, InputDrugId, InputDiseaseId, TopK, ScoreThreshold, ChannelId, RequestContent, Purpose, MedicalWarningAccepted)
    VALUES(@RequestCode, @RequesterId, @PredictionTypeId, @InputDrugId, @InputDiseaseId, @TopK, @ScoreThreshold, @ChannelId, @RequestContent, @Purpose, 1);
    SELECT SCOPE_IDENTITY() AS PredictionRequestId;
END
GO

CREATE OR ALTER PROCEDURE dbo.sp_SavePredictionRun
    @PredictionRunCode NVARCHAR(50), @PredictionRequestId INT, @ModelVersionId INT=NULL, @InputSummary NVARCHAR(MAX)=NULL, @ScoreThreshold DECIMAL(7,4)=NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.PredictionRuns(PredictionRunCode, PredictionRequestId, ModelVersionId, InputSummary, ScoreThreshold, RunStatus)
    VALUES(@PredictionRunCode, @PredictionRequestId, @ModelVersionId, @InputSummary, @ScoreThreshold, 'SUCCESS');
    UPDATE dbo.PredictionRequests SET RequestStatus='COMPLETED', UpdatedAt=SYSUTCDATETIME() WHERE PredictionRequestId=@PredictionRequestId;
    SELECT SCOPE_IDENTITY() AS PredictionRunId;
END
GO

CREATE OR ALTER PROCEDURE dbo.sp_SavePredictionResult
    @PredictionRunId INT, @RankNo INT, @DrugId INT, @DiseaseId INT, @PredictionScore DECIMAL(9,6),
    @ConfidenceLevelId INT=NULL, @LinkTypeId INT=NULL, @ShortExplanation NVARCHAR(1000)=NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.PredictionResults(PredictionRunId, RankNo, DrugId, DiseaseId, PredictionScore, ConfidenceLevelId, LinkTypeId, ShortExplanation)
    VALUES(@PredictionRunId, @RankNo, @DrugId, @DiseaseId, @PredictionScore, @ConfidenceLevelId, @LinkTypeId, @ShortExplanation);
    SELECT SCOPE_IDENTITY() AS PredictionResultId;
END
GO

CREATE OR ALTER PROCEDURE dbo.sp_SubmitPredictionFeedback
    @FeedbackCode NVARCHAR(50), @PredictionRunId INT, @PredictionResultId INT=NULL, @FeedbackUserId INT=NULL,
    @GeneralAssessment NVARCHAR(100), @UsefulScore TINYINT=NULL, @SuggestedAction NVARCHAR(200)=NULL, @ReasonText NVARCHAR(MAX)=NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.PredictionFeedbacks(FeedbackCode, PredictionRunId, PredictionResultId, FeedbackUserId, GeneralAssessment, UsefulScore, SuggestedAction, ReasonText, FeedbackStatusId)
    VALUES(@FeedbackCode, @PredictionRunId, @PredictionResultId, @FeedbackUserId, @GeneralAssessment, @UsefulScore, @SuggestedAction, @ReasonText, 1);
    SELECT SCOPE_IDENTITY() AS FeedbackId;
END
GO

CREATE OR ALTER PROCEDURE dbo.sp_CreateTrainingDataset
    @DatasetCode NVARCHAR(50), @DatasetName NVARCHAR(255), @Description NVARCHAR(1000)=NULL, @CreatedBy INT=NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.TrainingDatasets(DatasetCode, DatasetName, Description, CreatedBy)
    VALUES(@DatasetCode, @DatasetName, @Description, @CreatedBy);
    SELECT SCOPE_IDENTITY() AS TrainingDatasetId;
END
GO

CREATE OR ALTER PROCEDURE dbo.sp_RegisterModelVersion
    @ModelCode NVARCHAR(50), @ModelName NVARCHAR(255), @AlgorithmId INT, @VersionLabel NVARCHAR(50), @CreatedBy INT=NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.ModelVersions(ModelCode, ModelName, AlgorithmId, VersionLabel, CreatedBy)
    VALUES(@ModelCode, @ModelName, @AlgorithmId, @VersionLabel, @CreatedBy);
    SELECT SCOPE_IDENTITY() AS ModelVersionId;
END
GO

CREATE OR ALTER PROCEDURE dbo.sp_DeployModelVersion
    @ModelVersionId INT, @DecisionId INT, @EnvironmentName NVARCHAR(50)='DEMO', @DeployedBy INT=NULL, @DecisionNote NVARCHAR(1000)=NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.ModelVersions SET IsCurrent = 0;
    UPDATE dbo.ModelVersions SET IsCurrent = 1 WHERE ModelVersionId = @ModelVersionId;
    INSERT INTO dbo.ModelDeployments(ModelVersionId, DecisionId, EnvironmentName, DeploymentStatus, DecisionNote, DeployedBy, DeployedAt)
    VALUES(@ModelVersionId, @DecisionId, @EnvironmentName, 'DEPLOYED', @DecisionNote, @DeployedBy, SYSUTCDATETIME());
END
GO

/* ==========================================================
   15. TRIGGER AUDIT MẪU CHO BẢNG QUAN TRỌNG
   ========================================================== */
CREATE OR ALTER TRIGGER dbo.trg_Drugs_Audit ON dbo.Drugs
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Action NVARCHAR(20);
    IF EXISTS(SELECT 1 FROM inserted) AND EXISTS(SELECT 1 FROM deleted) SET @Action='UPDATE';
    ELSE IF EXISTS(SELECT 1 FROM inserted) SET @Action='INSERT';
    ELSE SET @Action='DELETE';

    INSERT INTO dbo.AuditLogs(TableName, RecordId, ActionType, ChangedBy)
    SELECT 'Drugs', CAST(COALESCE(i.DrugId,d.DrugId) AS NVARCHAR(100)), @Action, COALESCE(i.UpdatedBy,i.CreatedBy,d.UpdatedBy,d.CreatedBy)
    FROM inserted i FULL OUTER JOIN deleted d ON i.DrugId = d.DrugId;
END
GO

CREATE OR ALTER TRIGGER dbo.trg_Diseases_Audit ON dbo.Diseases
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Action NVARCHAR(20);
    IF EXISTS(SELECT 1 FROM inserted) AND EXISTS(SELECT 1 FROM deleted) SET @Action='UPDATE';
    ELSE IF EXISTS(SELECT 1 FROM inserted) SET @Action='INSERT';
    ELSE SET @Action='DELETE';

    INSERT INTO dbo.AuditLogs(TableName, RecordId, ActionType, ChangedBy)
    SELECT 'Diseases', CAST(COALESCE(i.DiseaseId,d.DiseaseId) AS NVARCHAR(100)), @Action, COALESCE(i.UpdatedBy,i.CreatedBy,d.UpdatedBy,d.CreatedBy)
    FROM inserted i FULL OUTER JOIN deleted d ON i.DiseaseId = d.DiseaseId;
END
GO

CREATE OR ALTER TRIGGER dbo.trg_DrugDiseaseLinks_Audit ON dbo.DrugDiseaseLinks
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Action NVARCHAR(20);
    IF EXISTS(SELECT 1 FROM inserted) AND EXISTS(SELECT 1 FROM deleted) SET @Action='UPDATE';
    ELSE IF EXISTS(SELECT 1 FROM inserted) SET @Action='INSERT';
    ELSE SET @Action='DELETE';

    INSERT INTO dbo.AuditLogs(TableName, RecordId, ActionType, ChangedBy)
    SELECT 'DrugDiseaseLinks', CAST(COALESCE(i.LinkId,d.LinkId) AS NVARCHAR(100)), @Action, COALESCE(i.UpdatedBy,i.CreatedBy,d.UpdatedBy,d.CreatedBy)
    FROM inserted i FULL OUTER JOIN deleted d ON i.LinkId = d.LinkId;
END
GO

/* ==========================================================
   16. QUERY MẪU KIỂM TRA LUỒNG
   ========================================================== */
-- 1. Tìm bệnh liên quan đến một thuốc
-- SELECT * FROM dbo.vw_KnownDrugDiseaseLinks WHERE ActiveName LIKE N'%Metformin%';

-- 2. Tìm thuốc tiềm năng cho một bệnh
-- SELECT * FROM dbo.vw_KnownDrugDiseaseLinks WHERE DiseaseName LIKE N'%Đái tháo đường%';

-- 3. Xem kết quả dự đoán của một user
-- SELECT h.* FROM dbo.vw_PredictionHistory h WHERE h.FullName = N'Người dùng nghiên cứu';

-- 4. Lấy dữ liệu train cho model
-- SELECT di.DatasetVersionId, dr.ActiveName, ds.DiseaseName, di.LabelValue, di.FeatureVectorJson, di.SplitName
-- FROM dbo.DatasetItems di JOIN dbo.Drugs dr ON di.DrugId=dr.DrugId JOIN dbo.Diseases ds ON di.DiseaseId=ds.DiseaseId;

-- 5. Xem model version đang deployed
-- SELECT * FROM dbo.vw_ModelEvaluationSummary WHERE ModelCode IN (SELECT ModelCode FROM dbo.ModelVersions WHERE IsCurrent=1);

-- 6. Xem phản hồi chưa xử lý
-- SELECT * FROM dbo.vw_FeedbackForModelImprovement WHERE StatusName = N'Chưa xem';
GO
