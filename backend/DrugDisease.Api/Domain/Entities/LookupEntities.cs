namespace DrugDisease.Api.Domain.Entities;

public class PredictionType
{
    public int PredictionTypeId { get; set; }
    public string PredictionTypeCode { get; set; } = string.Empty;
    public string PredictionTypeName { get; set; } = string.Empty;
}

public class ConfidenceLevel
{
    public int ConfidenceLevelId { get; set; }
    public string LevelCode { get; set; } = string.Empty;
    public string LevelName { get; set; } = string.Empty;
    public decimal? MinScore { get; set; }
    public decimal? MaxScore { get; set; }
}

public class LinkType
{
    public int LinkTypeId { get; set; }
    public string LinkTypeCode { get; set; } = string.Empty;
    public string LinkTypeName { get; set; } = string.Empty;
}

public class FeedbackStatus
{
    public int FeedbackStatusId { get; set; }
    public string StatusCode { get; set; } = string.Empty;
    public string StatusName { get; set; } = string.Empty;
}

public class ModelVersion
{
    public int ModelVersionId { get; set; }
    public string ModelCode { get; set; } = string.Empty;
    public string ModelName { get; set; } = string.Empty;
    public bool IsCurrent { get; set; }
}