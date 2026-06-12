using DrugDisease.Api.DTOs;

namespace DrugDisease.Api.Services;

public interface IFeedbackService
{
    Task<FeedbackResponseDto> CreateFeedbackAsync(FeedbackCreateRequest request, CancellationToken cancellationToken);
}