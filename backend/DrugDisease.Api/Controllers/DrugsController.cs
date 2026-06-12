using DrugDisease.Api.DTOs;
using DrugDisease.Api.Repositories;
using Microsoft.AspNetCore.Mvc;

namespace DrugDisease.Api.Controllers;

[ApiController]
[Route("api/drugs")]
public class DrugsController : ControllerBase
{
    private readonly IDrugDiseaseRepository _repository;

    public DrugsController(IDrugDiseaseRepository repository)
    {
        _repository = repository;
    }

    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<DrugDto>>> GetDrugs(
        [FromQuery] string? keyword,
        [FromQuery] int take = 20,
        CancellationToken cancellationToken = default)
    {
        var data = await _repository.SearchDrugsAsync(keyword, take, cancellationToken);
        return Ok(data);
    }
}