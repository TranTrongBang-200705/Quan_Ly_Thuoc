using DrugDisease.Api.DTOs;
using DrugDisease.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace DrugDisease.Api.Controllers;

[ApiController]
[Route("api/predictions")]
public class PredictionsController : ControllerBase
{
    private readonly IPredictionService _predictionService;

    public PredictionsController(IPredictionService predictionService)
    {
        _predictionService = predictionService;
    }

    [HttpPost]
    public async Task<ActionResult<PredictionResponseDto>> CreatePrediction(
        [FromBody] PredictionCreateRequest request,
        CancellationToken cancellationToken)
    {
        var data = await _predictionService.CreatePredictionAsync(request, cancellationToken);

        return CreatedAtAction(
            nameof(GetPredictionById),
            new { id = data.RequestId },
            data
        );
    }

    [HttpGet("{id:int}")]
    public async Task<ActionResult<PredictionResponseDto>> GetPredictionById(
        int id,
        CancellationToken cancellationToken)
    {
        var data = await _predictionService.GetPredictionAsync(id, cancellationToken);

        if (data == null)
        {
            return NotFound(new { message = "Không tìm thấy yêu cầu dự đoán." });
        }

        return Ok(data);
    }

    [HttpGet("history")]
    public async Task<ActionResult<IReadOnlyList<PredictionHistoryDto>>> GetHistory(
        [FromQuery] int? userId,
        CancellationToken cancellationToken)
    {
        var data = await _predictionService.GetHistoryAsync(userId, cancellationToken);
        return Ok(data);
    }
}