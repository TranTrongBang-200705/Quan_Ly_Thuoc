namespace DrugDisease.Api.Domain.Entities;

public class PredictionRequest
{
    public int PredictionRequestId { get; set; }
    public string RequestCode { get; set; } = string.Empty;

    public int? RequesterId { get; set; }

    public int PredictionTypeId { get; set; }
    public PredictionType PredictionType { get; set; } = null!;

    public int? InputDrugId { get; set; }
    public Drug? InputDrug { get; set; }

    public int? InputDiseaseId { get; set; }
    public Disease? InputDisease { get; set; }

    public int TopK { get; set; } = 10;
    public decimal? ScoreThreshold { get; set; }
    public string? Purpose { get; set; }
    public string? ContactEmail { get; set; }
    public bool MedicalWarningAccepted { get; set; }

    public string RequestStatus { get; set; } = "SUBMITTED";
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public bool IsDeleted { get; set; }

    public ICollection<PredictionRun> PredictionRuns { get; set; } = new List<PredictionRun>();
}

public class PredictionRun
{
    public int PredictionRunId { get; set; }
    public string PredictionRunCode { get; set; } = string.Empty;

    public int PredictionRequestId { get; set; }
    public PredictionRequest PredictionRequest { get; set; } = null!;

    public int? ModelVersionId { get; set; }
    public ModelVersion? ModelVersion { get; set; }

    public string ModuleName { get; set; } = "ML_PREDICTION_MODULE";
    public string? InputSummary { get; set; }
    public decimal? ScoreThreshold { get; set; }
    public string? SystemComment { get; set; }
    public string? ProcessingConclusion { get; set; }

    public string MandatoryMedicalWarning { get; set; } =
        "Kết quả dự đoán chỉ phục vụ mục đích hỗ trợ nghiên cứu và tham khảo. Không sử dụng kết quả này như chỉ định điều trị hoặc thay thế ý kiến của bác sĩ/dược sĩ.";

    public string RunStatus { get; set; } = "SUCCESS";
    public DateTime CreatedAt { get; set; }

    public ICollection<PredictionResult> PredictionResults { get; set; } = new List<PredictionResult>();
}

public class PredictionResult
{
    public int PredictionResultId { get; set; }

    public int PredictionRunId { get; set; }
    public PredictionRun PredictionRun { get; set; } = null!;

    public int RankNo { get; set; }

    public int DrugId { get; set; }
    public Drug Drug { get; set; } = null!;

    public int DiseaseId { get; set; }
    public Disease Disease { get; set; } = null!;

    public decimal PredictionScore { get; set; }

    public int? ConfidenceLevelId { get; set; }
    public ConfidenceLevel? ConfidenceLevel { get; set; }

    public int? LinkTypeId { get; set; }
    public LinkType? LinkType { get; set; }

    public string? ShortExplanation { get; set; }

    public int? KnownLinkId { get; set; }
    public DrugDiseaseLink? KnownLink { get; set; }

    public DateTime CreatedAt { get; set; }
}

public class PredictionFeedback
{
    public int FeedbackId { get; set; }
    public string FeedbackCode { get; set; } = string.Empty;

    public int PredictionRunId { get; set; }
    public PredictionRun PredictionRun { get; set; } = null!;

    public int? PredictionResultId { get; set; }
    public PredictionResult? PredictionResult { get; set; }

    public int? FeedbackUserId { get; set; }

    public string GeneralAssessment { get; set; } = string.Empty;
    public int? UsefulScore { get; set; }
    public string? SuggestedAction { get; set; }
    public string? ReasonText { get; set; }

    public int FeedbackStatusId { get; set; } = 1;
    public FeedbackStatus? FeedbackStatus { get; set; }

    public DateTime CreatedAt { get; set; }
    public bool IsDeleted { get; set; }
}