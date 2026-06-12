namespace DrugDisease.Api.DTOs;

public record LookupItemDto(
    int Id,
    string Code,
    string Name
);

public record LookupsResponseDto(
    IReadOnlyList<LookupItemDto> PredictionTypes,
    IReadOnlyList<LookupItemDto> ConfidenceLevels,
    IReadOnlyList<LookupItemDto> LinkTypes
);