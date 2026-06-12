using DrugDisease.Api.Data;
using DrugDisease.Api.DTOs;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace DrugDisease.Api.Controllers;

[ApiController]
[Route("api/lookups")]
public class LookupsController : ControllerBase
{
    private readonly DrugDiseaseDbContext _db;

    public LookupsController(DrugDiseaseDbContext db)
    {
        _db = db;
    }

    [HttpGet]
    public async Task<ActionResult<LookupsResponseDto>> GetLookups(CancellationToken cancellationToken)
    {
        var predictionTypes = await _db.PredictionTypes
            .AsNoTracking()
            .OrderBy(x => x.PredictionTypeId)
            .Select(x => new LookupItemDto(
                x.PredictionTypeId,
                x.PredictionTypeCode,
                x.PredictionTypeName
            ))
            .ToListAsync(cancellationToken);

        var confidenceLevels = await _db.ConfidenceLevels
            .AsNoTracking()
            .OrderBy(x => x.ConfidenceLevelId)
            .Select(x => new LookupItemDto(
                x.ConfidenceLevelId,
                x.LevelCode,
                x.LevelName
            ))
            .ToListAsync(cancellationToken);

        var linkTypes = await _db.LinkTypes
            .AsNoTracking()
            .OrderBy(x => x.LinkTypeId)
            .Select(x => new LookupItemDto(
                x.LinkTypeId,
                x.LinkTypeCode,
                x.LinkTypeName
            ))
            .ToListAsync(cancellationToken);

        return Ok(new LookupsResponseDto(
            predictionTypes,
            confidenceLevels,
            linkTypes
        ));
    }
}