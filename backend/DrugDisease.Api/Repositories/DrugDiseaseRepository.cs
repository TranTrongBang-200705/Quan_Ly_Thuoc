using DrugDisease.Api.Data;
using DrugDisease.Api.DTOs;
using Microsoft.EntityFrameworkCore;

namespace DrugDisease.Api.Repositories;

public class DrugDiseaseRepository : IDrugDiseaseRepository
{
    private readonly DrugDiseaseDbContext _db;

    public DrugDiseaseRepository(DrugDiseaseDbContext db)
    {
        _db = db;
    }

    public async Task<IReadOnlyList<DrugDto>> SearchDrugsAsync(
        string? keyword,
        int take,
        CancellationToken cancellationToken)
    {
        take = Math.Clamp(take, 1, 100);
        keyword = keyword?.Trim();

        var query = _db.Drugs
            .AsNoTracking()
            .Where(x => !x.IsDeleted);

        if (!string.IsNullOrWhiteSpace(keyword))
        {
            query = query.Where(x =>
                x.ActiveName.Contains(keyword) ||
                (x.TradeName != null && x.TradeName.Contains(keyword)) ||
                x.DrugCode.Contains(keyword));
        }

        return await query
            .OrderBy(x => x.ActiveName)
            .Take(take)
            .Select(x => new DrugDto(
                x.DrugId,
                x.DrugCode,
                x.ActiveName,
                x.TradeName,
                x.KnownIndications
            ))
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<DiseaseDto>> SearchDiseasesAsync(
    string? keyword,
    int take,
    CancellationToken cancellationToken)
{
    take = Math.Clamp(take, 1, 100);
    keyword = keyword?.Trim();

    var query = _db.Diseases
        .AsNoTracking()
        .Where(x => !x.IsDeleted);

    if (!string.IsNullOrWhiteSpace(keyword))
    {
        query = query.Where(x =>
            x.DiseaseName.Contains(keyword) ||
            x.DiseaseCode.Contains(keyword) ||
            (x.Description != null && x.Description.Contains(keyword)));
    }

    return await query
        .OrderBy(x => x.DiseaseName)
        .Take(take)
        .Select(x => new DiseaseDto(
            x.DiseaseId,
            x.DiseaseCode,
            x.DiseaseName,
            x.Description
        ))
        .ToListAsync(cancellationToken);
}

    public async Task<IReadOnlyList<DrugDiseaseLinkDto>> SearchLinksAsync(
        int? drugId,
        int? diseaseId,
        CancellationToken cancellationToken)
    {
        var query = _db.DrugDiseaseLinks
            .AsNoTracking()
            .Include(x => x.Drug)
            .Include(x => x.Disease)
            .Include(x => x.ConfidenceLevel)
            .Where(x => !x.IsDeleted);

        if (drugId.HasValue)
        {
            query = query.Where(x => x.DrugId == drugId.Value);
        }

        if (diseaseId.HasValue)
        {
            query = query.Where(x => x.DiseaseId == diseaseId.Value);
        }

        return await query
            .OrderByDescending(x => x.SourceScore)
            .Take(100)
            .Select(x => new DrugDiseaseLinkDto(
                x.LinkId,
                x.DrugId,
                x.Drug.ActiveName,
                x.DiseaseId,
                x.Disease.DiseaseName,
                x.SourceScore,
                x.ConfidenceLevel != null ? x.ConfidenceLevel.LevelName : null,
                x.EvidenceDescription
            ))
            .ToListAsync(cancellationToken);
    }
}