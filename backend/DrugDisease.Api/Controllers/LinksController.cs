using DrugDisease.Api.DTOs;
using DrugDisease.Api.Repositories;
using Microsoft.AspNetCore.Mvc;

namespace DrugDisease.Api.Controllers;

[ApiController]
[Route("api/links")]
public class LinksController : ControllerBase
{
    private readonly IDrugDiseaseRepository _repository;

    public LinksController(IDrugDiseaseRepository repository)
    {
        _repository = repository;
    }

    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<DrugDiseaseLinkDto>>> GetLinks(
        [FromQuery] int? drugId,
        [FromQuery] int? diseaseId,
        CancellationToken cancellationToken)
    {
        var data = await _repository.SearchLinksAsync(drugId, diseaseId, cancellationToken);
        return Ok(data);
    }
}