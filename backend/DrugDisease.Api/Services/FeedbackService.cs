using DrugDisease.Api.Data;
using DrugDisease.Api.Domain.Entities;
using DrugDisease.Api.DTOs;
using Microsoft.EntityFrameworkCore;

namespace DrugDisease.Api.Services;

public class FeedbackService : IFeedbackService
{
    private readonly DrugDiseaseDbContext _db;

    public FeedbackService(DrugDiseaseDbContext db)
    {
        _db = db;
    }

    public async Task<FeedbackResponseDto> CreateFeedbackAsync(
        FeedbackCreateRequest request,
        CancellationToken cancellationToken)
    {
        var runExists = await _db.PredictionRuns
            .AnyAsync(x => x.PredictionRunId == request.PredictionRunId, cancellationToken);

        if (!runExists)
        {
            throw new InvalidOperationException("PredictionRunId không tồn tại.");
        }

        if (request.PredictionResultId.HasValue)
        {
            var resultExists = await _db.PredictionResults
                .AnyAsync(x => x.PredictionResultId == request.PredictionResultId.Value, cancellationToken);

            if (!resultExists)
            {
                throw new InvalidOperationException("PredictionResultId không tồn tại.");
            }
        }

        var defaultStatusId = await _db.FeedbackStatuses
            .AsNoTracking()
            .OrderBy(x => x.FeedbackStatusId)
            .Select(x => (int?)x.FeedbackStatusId)
            .FirstOrDefaultAsync(cancellationToken);

        var feedback = new PredictionFeedback
        {
            FeedbackCode = $"FB-{DateTime.UtcNow:yyyyMMddHHmmssfff}",
            PredictionRunId = request.PredictionRunId,
            PredictionResultId = request.PredictionResultId,
            FeedbackUserId = request.UserId,
            GeneralAssessment = NormalizeGeneralAssessment(request.GeneralAssessment),
            UsefulScore = request.UsefulScore,
            SuggestedAction = request.SuggestedAction,
            ReasonText = request.ReasonText,
            FeedbackStatusId = defaultStatusId ?? 1,
            CreatedAt = DateTime.UtcNow,
            IsDeleted = false
        };

        _db.PredictionFeedbacks.Add(feedback);
        await _db.SaveChangesAsync(cancellationToken);

        return new FeedbackResponseDto(
            feedback.FeedbackId,
            feedback.FeedbackCode,
            feedback.GeneralAssessment,
            feedback.UsefulScore,
            feedback.SuggestedAction,
            feedback.ReasonText,
            feedback.CreatedAt
        );
    }

    private static string NormalizeGeneralAssessment(string value)
    {
        var normalized = value.Trim().ToLowerInvariant();

        return normalized switch
        {
            "useful" => "Hợp lý",
            "reasonable" => "Hợp lý",
            "ok" => "Hợp lý",
            "not_useful" => "Chưa hợp lý",
            "incorrect" => "Chưa hợp lý",
            "need_check" => "Cần kiểm chứng thêm",
            "unknown" => "Không đủ thông tin để đánh giá",
            "hợp lý" => "Hợp lý",
            "chưa hợp lý" => "Chưa hợp lý",
            "cần kiểm chứng thêm" => "Cần kiểm chứng thêm",
            "không đủ thông tin để đánh giá" => "Không đủ thông tin để đánh giá",
            _ => "Cần kiểm chứng thêm"
        };
    }
}