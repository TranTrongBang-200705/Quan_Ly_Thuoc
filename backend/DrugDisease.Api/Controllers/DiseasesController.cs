using DrugDisease.Api.DTOs;
using DrugDisease.Api.Repositories;
using Microsoft.AspNetCore.Mvc;

namespace DrugDisease.Api.Controllers;

[ApiController]
[Route("api/diseases")]
public class DiseasesController : ControllerBase
{
    private readonly IDrugDiseaseRepository _repository;

    public DiseasesController(IDrugDiseaseRepository repository)
    {
        _repository = repository;
    }

    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<DiseaseDto>>> GetDiseases(
        [FromQuery] string? keyword,
        [FromQuery] int take = 20,
        CancellationToken cancellationToken = default)
    {
        var data = await _repository.SearchDiseasesAsync(keyword, take, cancellationToken);
        return Ok(data);
    }
}