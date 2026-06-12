using System.ComponentModel.DataAnnotations;

namespace DrugDisease.Api.DTOs;

public class PredictionCreateRequest
{
    [Required]
    public string PredictionType { get; set; } = string.Empty;

    public int? DrugId { get; set; }

    public int? DiseaseId { get; set; }

    [Range(1, 100)]
    public int TopK { get; set; } = 10;

    [Range(0, 1)]
    public decimal? ScoreThreshold { get; set; } = 0.5m;

    [MaxLength(500)]
    public string? Purpose { get; set; }

    [EmailAddress]
    public string? ContactEmail { get; set; }

    public bool MedicalWarningAccepted { get; set; } = true;
}

public record PredictionResultDto(
    int PredictionResultId,
    int RankNo,
    int DrugId,
    string DrugName,
    int DiseaseId,
    string DiseaseName,
    decimal PredictionScore,
    string? ConfidenceLevel,
    string? LinkType,
    string? ExplanationText,
    string? WarningText
);

public record PredictionResponseDto(
    int RequestId,
    string RequestCode,
    int PredictionRunId,
    string RunCode,
    string RequestStatus,
    DateTime CreatedAt,
    IReadOnlyList<PredictionResultDto> Results
);

public record PredictionHistoryDto(
    int RequestId,
    string RequestCode,
    string PredictionType,
    string? InputDrugName,
    string? InputDiseaseName,
    string RequestStatus,
    DateTime CreatedAt,
    int ResultCount
);