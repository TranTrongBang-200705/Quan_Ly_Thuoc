using DrugDisease.Api.DTOs;
using DrugDisease.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace DrugDisease.Api.Controllers;

[ApiController]
[Route("api/feedbacks")]
public class FeedbacksController : ControllerBase
{
    private readonly IFeedbackService _feedbackService;

    public FeedbacksController(IFeedbackService feedbackService)
    {
        _feedbackService = feedbackService;
    }

    [HttpPost]
    public async Task<ActionResult<FeedbackResponseDto>> CreateFeedback(
        [FromBody] FeedbackCreateRequest request,
        CancellationToken cancellationToken)
    {
        var data = await _feedbackService.CreateFeedbackAsync(request, cancellationToken);
        return Ok(data);
    }
}