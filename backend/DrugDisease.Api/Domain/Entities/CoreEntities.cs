namespace DrugDisease.Api.Domain.Entities;

public class Drug
{
    public int DrugId { get; set; }
    public string DrugCode { get; set; } = string.Empty;
    public string ActiveName { get; set; } = string.Empty;
    public string? TradeName { get; set; }
    public string? Description { get; set; }
    public string? KnownIndications { get; set; }
    public bool IsDeleted { get; set; }

    public ICollection<DrugDiseaseLink> DrugDiseaseLinks { get; set; } = new List<DrugDiseaseLink>();
}

public class Disease
{
    public int DiseaseId { get; set; }
    public string DiseaseCode { get; set; } = string.Empty;
    public string DiseaseName { get; set; } = string.Empty;
    public string? Description { get; set; }
    public bool IsDeleted { get; set; }

    public ICollection<DrugDiseaseLink> DrugDiseaseLinks { get; set; } = new List<DrugDiseaseLink>();
}

public class DrugDiseaseLink
{
    public int LinkId { get; set; }
    public string LinkCode { get; set; } = string.Empty;

    public int DrugId { get; set; }
    public Drug Drug { get; set; } = null!;

    public int DiseaseId { get; set; }
    public Disease Disease { get; set; } = null!;

    public int? LinkTypeId { get; set; }
    public LinkType? LinkType { get; set; }

    public int? ConfidenceLevelId { get; set; }
    public ConfidenceLevel? ConfidenceLevel { get; set; }

    public int? EvidenceStatusId { get; set; }

    public decimal? SourceScore { get; set; }
    public string? EvidenceDescription { get; set; }
    public bool IsDeleted { get; set; }
}