namespace DrugDisease.Api.DTOs;

public record DrugDto(
    int DrugId,
    string DrugCode,
    string ActiveName,
    string? TradeName,
    string? KnownIndications
);

public record DiseaseDto(
    int DiseaseId,
    string DiseaseCode,
    string DiseaseName,
    string? Description
);

public record DrugDiseaseLinkDto(
    int LinkId,
    int DrugId,
    string DrugName,
    int DiseaseId,
    string DiseaseName,
    decimal? SourceScore,
    string? ConfidenceLevel,
    string? EvidenceDescription
);