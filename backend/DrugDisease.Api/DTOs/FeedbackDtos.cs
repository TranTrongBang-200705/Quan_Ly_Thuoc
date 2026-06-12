using System.ComponentModel.DataAnnotations;

namespace DrugDisease.Api.DTOs;

public class FeedbackCreateRequest
{
    [Required]
    public int PredictionRunId { get; set; }

    public int? PredictionResultId { get; set; }

    public int? UserId { get; set; }

    [Required]
    [MaxLength(100)]
    public string GeneralAssessment { get; set; } = string.Empty;

    [Range(1, 5)]
    public int? UsefulScore { get; set; }

    [MaxLength(255)]
    public string? SuggestedAction { get; set; }

    [MaxLength(2000)]
    public string? ReasonText { get; set; }
}

public record FeedbackResponseDto(
    int FeedbackId,
    string FeedbackCode,
    string GeneralAssessment,
    int? UsefulScore,
    string? SuggestedAction,
    string? ReasonText,
    DateTime CreatedAt
);