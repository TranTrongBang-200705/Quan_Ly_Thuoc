using DrugDisease.Api.DTOs;

namespace DrugDisease.Api.Services;

public interface IPredictionService
{
    Task<PredictionResponseDto> CreatePredictionAsync(PredictionCreateRequest request, CancellationToken cancellationToken);
    Task<PredictionResponseDto?> GetPredictionAsync(int requestId, CancellationToken cancellationToken);
    Task<IReadOnlyList<PredictionHistoryDto>> GetHistoryAsync(int? userId, CancellationToken cancellationToken);
}