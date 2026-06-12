using DrugDisease.Api.DTOs;

namespace DrugDisease.Api.Repositories;

public interface IDrugDiseaseRepository
{
    Task<IReadOnlyList<DrugDto>> SearchDrugsAsync(string? keyword, int take, CancellationToken cancellationToken);
    Task<IReadOnlyList<DiseaseDto>> SearchDiseasesAsync(string? keyword, int take, CancellationToken cancellationToken);
    Task<IReadOnlyList<DrugDiseaseLinkDto>> SearchLinksAsync(int? drugId, int? diseaseId, CancellationToken cancellationToken);
}