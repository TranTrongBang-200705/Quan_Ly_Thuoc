using DrugDisease.Api.Data;
using DrugDisease.Api.Domain.Entities;
using DrugDisease.Api.DTOs;
using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;

namespace DrugDisease.Api.Services;

public class PredictionService : IPredictionService
{
    private readonly DrugDiseaseDbContext _db;

    public PredictionService(DrugDiseaseDbContext db)
    {
        _db = db;
    }

    public async Task<PredictionResponseDto> CreatePredictionAsync(
        PredictionCreateRequest request,
        CancellationToken cancellationToken)
    {
        ValidateRequest(request);

        var predictionTypeId = await ResolvePredictionTypeIdAsync(request.PredictionType, cancellationToken);

        var predictionRequest = new PredictionRequest
        {
            RequestCode = CreateCode("REQ"),
            RequesterId = null,
            PredictionTypeId = predictionTypeId,
            InputDrugId = request.DrugId,
            InputDiseaseId = request.DiseaseId,
            TopK = request.TopK,
            ScoreThreshold = request.ScoreThreshold,
            Purpose = request.Purpose,
            ContactEmail = request.ContactEmail,
            MedicalWarningAccepted = request.MedicalWarningAccepted,
            RequestStatus = "PROCESSING",
            CreatedAt = DateTime.UtcNow,
            IsDeleted = false
        };

        _db.PredictionRequests.Add(predictionRequest);
        await _db.SaveChangesAsync(cancellationToken);

        var modelVersionId = await _db.ModelVersions
            .AsNoTracking()
            .Where(x => x.IsCurrent)
            .Select(x => (int?)x.ModelVersionId)
            .FirstOrDefaultAsync(cancellationToken);

        var predictionRun = new PredictionRun
        {
            PredictionRunCode = CreateCode("PRED"),
            PredictionRequestId = predictionRequest.PredictionRequestId,
            ModelVersionId = modelVersionId,
            ModuleName = "ML_PREDICTION_MODULE",
            InputSummary = BuildInputSummary(request),
            ScoreThreshold = request.ScoreThreshold,
            SystemComment = "Rule-based MVP from known DrugDiseaseLinks. Replace by ML model later.",
            RunStatus = "SUCCESS",
            ProcessingConclusion = "COMPLETED",
            CreatedAt = DateTime.UtcNow
        };

        _db.PredictionRuns.Add(predictionRun);
        await _db.SaveChangesAsync(cancellationToken);

        var candidates = await BuildCandidatesAsync(request, cancellationToken);

        var threshold = request.ScoreThreshold ?? 0;
        var results = candidates
            .Where(x => x.Score >= threshold)
            .OrderByDescending(x => x.Score)
            .Take(request.TopK)
            .Select((x, index) => new PredictionResult
            {
                PredictionRunId = predictionRun.PredictionRunId,
                RankNo = index + 1,
                DrugId = x.DrugId,
                DiseaseId = x.DiseaseId,
                KnownLinkId = x.KnownLinkId,
                PredictionScore = x.Score,
                ConfidenceLevelId = ResolveConfidenceLevelId(x.Score),
                LinkTypeId = x.LinkTypeId,
                ShortExplanation = x.ExplanationText,
                CreatedAt = DateTime.UtcNow
            })
            .ToList();

        _db.PredictionResults.AddRange(results);

        predictionRequest.RequestStatus = "COMPLETED";
        predictionRequest.UpdatedAt = DateTime.UtcNow;

        await _db.SaveChangesAsync(cancellationToken);

        return await GetPredictionAsync(predictionRequest.PredictionRequestId, cancellationToken)
            ?? throw new InvalidOperationException("Không đọc được kết quả dự đoán vừa tạo.");
    }

    public async Task<PredictionResponseDto?> GetPredictionAsync(
        int requestId,
        CancellationToken cancellationToken)
    {
        var request = await _db.PredictionRequests
            .AsNoTracking()
            .Include(x => x.PredictionRuns)
            .FirstOrDefaultAsync(x => x.PredictionRequestId == requestId, cancellationToken);

        if (request == null)
        {
            return null;
        }

        var run = await _db.PredictionRuns
            .AsNoTracking()
            .Where(x => x.PredictionRequestId == requestId)
            .OrderByDescending(x => x.PredictionRunId)
            .FirstOrDefaultAsync(cancellationToken);

        if (run == null)
        {
            return new PredictionResponseDto(
                request.PredictionRequestId,
                request.RequestCode,
                0,
                string.Empty,
                request.RequestStatus,
                request.CreatedAt,
                Array.Empty<PredictionResultDto>()
            );
        }

        var results = await _db.PredictionResults
            .AsNoTracking()
            .Include(x => x.Drug)
            .Include(x => x.Disease)
            .Include(x => x.ConfidenceLevel)
            .Include(x => x.LinkType)
            .Where(x => x.PredictionRunId == run.PredictionRunId)
            .OrderBy(x => x.RankNo)
            .Select(x => new PredictionResultDto(
                x.PredictionResultId,
                x.RankNo,
                x.DrugId,
                x.Drug.ActiveName,
                x.DiseaseId,
                x.Disease.DiseaseName,
                x.PredictionScore,
                x.ConfidenceLevel != null ? x.ConfidenceLevel.LevelName : null,
                x.LinkType != null ? x.LinkType.LinkTypeName : null,
                x.ShortExplanation,
                "Kết quả chỉ mang tính hỗ trợ tham khảo, không thay thế tư vấn y khoa."
            ))
            .ToListAsync(cancellationToken);

        return new PredictionResponseDto(
            request.PredictionRequestId,
            request.RequestCode,
            run.PredictionRunId,
            run.PredictionRunCode,
            request.RequestStatus,
            request.CreatedAt,
            results
        );
    }

    public async Task<IReadOnlyList<PredictionHistoryDto>> GetHistoryAsync(
        int? userId,
        CancellationToken cancellationToken)
    {
        var query = _db.PredictionRequests
            .AsNoTracking()
            .Include(x => x.PredictionType)
            .Include(x => x.InputDrug)
            .Include(x => x.InputDisease)
            .AsQueryable();

        if (userId.HasValue)
        {
            query = query.Where(x => x.RequesterId == userId.Value);
        }

        return await query
            .OrderByDescending(x => x.CreatedAt)
            .Take(100)
            .Select(x => new PredictionHistoryDto(
                x.PredictionRequestId,
                x.RequestCode,
                x.PredictionType.PredictionTypeName,
                x.InputDrug != null ? x.InputDrug.ActiveName : null,
                x.InputDisease != null ? x.InputDisease.DiseaseName : null,
                x.RequestStatus,
                x.CreatedAt,
                x.PredictionRuns
                    .SelectMany(r => r.PredictionResults)
                    .Count()
            ))
            .ToListAsync(cancellationToken);
    }

    private async Task<IReadOnlyList<CandidateResult>> BuildCandidatesAsync(
        PredictionCreateRequest request,
        CancellationToken cancellationToken)
    {
        var type = request.PredictionType.Trim().ToUpperInvariant();

        if (type == "PAIR_PREDICTION")
        {
            var link = await _db.DrugDiseaseLinks
                .AsNoTracking()
                .FirstOrDefaultAsync(x =>
                    x.DrugId == request.DrugId &&
                    x.DiseaseId == request.DiseaseId &&
                    !x.IsDeleted,
                    cancellationToken);

            var score = link?.SourceScore ?? 0.42m;

            return new[]
            {
                new CandidateResult(
                    request.DrugId!.Value,
                    request.DiseaseId!.Value,
                    link?.LinkId,
                    score,
                    link?.LinkTypeId,
                    link != null
                        ? "Tìm thấy liên kết đã biết trong DrugDiseaseLinks."
                        : "Chưa tìm thấy liên kết đã biết. Điểm hiện tại là fallback MVP, cần thay bằng ML model."
                )
            };
        }

        if (type == "DRUG_TO_DISEASE")
        {
            var links = await _db.DrugDiseaseLinks
                .AsNoTracking()
                .Where(x => x.DrugId == request.DrugId && !x.IsDeleted)
                .OrderByDescending(x => x.SourceScore)
                .Take(100)
                .ToListAsync(cancellationToken);

            if (links.Count > 0)
            {
                return links.Select(x => new CandidateResult(
                    x.DrugId,
                    x.DiseaseId,
                    x.LinkId,
                    x.SourceScore ?? 0.75m,
                    x.LinkTypeId,
                    "Dự đoán dựa trên liên kết thuốc - bệnh đã biết."
                )).ToList();
            }

            var fallbackDiseases = await _db.Diseases
                .AsNoTracking()
                .Where(x => !x.IsDeleted)
                .OrderBy(x => x.DiseaseName)
                .Take(request.TopK)
                .ToListAsync(cancellationToken);

            return fallbackDiseases.Select(x => new CandidateResult(
                request.DrugId!.Value,
                x.DiseaseId,
                null,
                0.35m,
                null,
                "Fallback khi chưa có liên kết đã biết. Cần model ML để tính chính xác."
            )).ToList();
        }

        if (type == "DISEASE_TO_DRUG")
        {
            var links = await _db.DrugDiseaseLinks
                .AsNoTracking()
                .Where(x => x.DiseaseId == request.DiseaseId && !x.IsDeleted)
                .OrderByDescending(x => x.SourceScore)
                .Take(100)
                .ToListAsync(cancellationToken);

            if (links.Count > 0)
            {
                return links.Select(x => new CandidateResult(
                    x.DrugId,
                    x.DiseaseId,
                    x.LinkId,
                    x.SourceScore ?? 0.75m,
                    x.LinkTypeId,
                    "Dự đoán dựa trên liên kết bệnh - thuốc đã biết."
                )).ToList();
            }

            var fallbackDrugs = await _db.Drugs
                .AsNoTracking()
                .Where(x => !x.IsDeleted)
                .OrderBy(x => x.ActiveName)
                .Take(request.TopK)
                .ToListAsync(cancellationToken);

            return fallbackDrugs.Select(x => new CandidateResult(
                x.DrugId,
                request.DiseaseId!.Value,
                null,
                0.35m,
                null,
                "Fallback khi chưa có liên kết đã biết. Cần model ML để tính chính xác."
            )).ToList();
        }

        throw new ValidationException("PredictionType không hợp lệ.");
    }

    private async Task<int> ResolvePredictionTypeIdAsync(
        string predictionType,
        CancellationToken cancellationToken)
    {
        var code = predictionType.Trim().ToUpperInvariant();

        var id = await _db.PredictionTypes
            .AsNoTracking()
            .Where(x => x.PredictionTypeCode.ToUpper() == code)
            .Select(x => (int?)x.PredictionTypeId)
            .FirstOrDefaultAsync(cancellationToken);

        if (id.HasValue)
        {
            return id.Value;
        }

        throw new ValidationException($"Không tìm thấy PredictionTypeCode = {code} trong bảng PredictionTypes.");
    }

    private static int? ResolveConfidenceLevelId(decimal score)
    {
        if (score >= 0.75m) return 3;
        if (score >= 0.5m) return 2;
        return 1;
    }

    private static void ValidateRequest(PredictionCreateRequest request)
    {
        var type = request.PredictionType.Trim().ToUpperInvariant();

        if (!request.MedicalWarningAccepted)
        {
            throw new ValidationException("Người dùng cần xác nhận cảnh báo y khoa trước khi dự đoán.");
        }

        if (type == "DRUG_TO_DISEASE" && request.DrugId == null)
        {
            throw new ValidationException("Dự đoán từ thuốc sang bệnh cần DrugId.");
        }

        if (type == "DISEASE_TO_DRUG" && request.DiseaseId == null)
        {
            throw new ValidationException("Dự đoán từ bệnh sang thuốc cần DiseaseId.");
        }

        if (type == "PAIR_PREDICTION" && (request.DrugId == null || request.DiseaseId == null))
        {
            throw new ValidationException("Dự đoán cặp thuốc - bệnh cần DrugId và DiseaseId.");
        }

        if (type is not "DRUG_TO_DISEASE" and not "DISEASE_TO_DRUG" and not "PAIR_PREDICTION")
        {
            throw new ValidationException("PredictionType chỉ nhận DRUG_TO_DISEASE, DISEASE_TO_DRUG hoặc PAIR_PREDICTION.");
        }
    }

    private static string BuildInputSummary(PredictionCreateRequest request)
    {
        return $"Type={request.PredictionType}; DrugId={request.DrugId}; DiseaseId={request.DiseaseId}; TopK={request.TopK}; Threshold={request.ScoreThreshold}";
    }

    private static string CreateCode(string prefix)
    {
        return $"{prefix}-{DateTime.UtcNow:yyyyMMddHHmmssfff}";
    }

    private record CandidateResult(
        int DrugId,
        int DiseaseId,
        int? KnownLinkId,
        decimal Score,
        int? LinkTypeId,
        string ExplanationText
    );
}