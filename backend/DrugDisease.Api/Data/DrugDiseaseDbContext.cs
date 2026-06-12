using DrugDisease.Api.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace DrugDisease.Api.Data;

public class DrugDiseaseDbContext : DbContext
{
    public DrugDiseaseDbContext(DbContextOptions<DrugDiseaseDbContext> options)
        : base(options)
    {
    }

    public DbSet<Drug> Drugs => Set<Drug>();
    public DbSet<Disease> Diseases => Set<Disease>();
    public DbSet<DrugDiseaseLink> DrugDiseaseLinks => Set<DrugDiseaseLink>();

    public DbSet<PredictionType> PredictionTypes => Set<PredictionType>();
    public DbSet<ConfidenceLevel> ConfidenceLevels => Set<ConfidenceLevel>();
    public DbSet<LinkType> LinkTypes => Set<LinkType>();
    public DbSet<FeedbackStatus> FeedbackStatuses => Set<FeedbackStatus>();
    public DbSet<ModelVersion> ModelVersions => Set<ModelVersion>();

    public DbSet<PredictionRequest> PredictionRequests => Set<PredictionRequest>();
    public DbSet<PredictionRun> PredictionRuns => Set<PredictionRun>();
    public DbSet<PredictionResult> PredictionResults => Set<PredictionResult>();
    public DbSet<PredictionFeedback> PredictionFeedbacks => Set<PredictionFeedback>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Drug>(entity =>
        {
            entity.ToTable("Drugs");
            entity.HasKey(x => x.DrugId);
            entity.Property(x => x.DrugCode).HasMaxLength(50);
            entity.Property(x => x.ActiveName).HasMaxLength(255);
            entity.Property(x => x.TradeName).HasMaxLength(255);
        });

        modelBuilder.Entity<Disease>(entity =>
        {
            entity.ToTable("Diseases");
            entity.HasKey(x => x.DiseaseId);
            entity.Property(x => x.DiseaseCode).HasMaxLength(50);
            entity.Property(x => x.DiseaseName).HasMaxLength(255);
        });

        modelBuilder.Entity<DrugDiseaseLink>(entity =>
        {
            entity.ToTable("DrugDiseaseLinks");
            entity.HasKey(x => x.LinkId);
            entity.Property(x => x.LinkCode).HasMaxLength(50);
            entity.Property(x => x.SourceScore).HasPrecision(7, 4);

            entity.HasOne(x => x.Drug)
                .WithMany(x => x.DrugDiseaseLinks)
                .HasForeignKey(x => x.DrugId);

            entity.HasOne(x => x.Disease)
                .WithMany(x => x.DrugDiseaseLinks)
                .HasForeignKey(x => x.DiseaseId);

            entity.HasOne(x => x.LinkType)
                .WithMany()
                .HasForeignKey(x => x.LinkTypeId);

            entity.HasOne(x => x.ConfidenceLevel)
                .WithMany()
                .HasForeignKey(x => x.ConfidenceLevelId);
        });

        

        

        modelBuilder.Entity<PredictionType>(entity =>
        {
            entity.ToTable("PredictionTypes");
            entity.HasKey(x => x.PredictionTypeId);
            entity.Property(x => x.PredictionTypeCode).HasMaxLength(50);
            entity.Property(x => x.PredictionTypeName).HasMaxLength(255);
        });

        modelBuilder.Entity<ConfidenceLevel>(entity =>
        {
            entity.ToTable("ConfidenceLevels");
            entity.HasKey(x => x.ConfidenceLevelId);
            entity.Property(x => x.LevelCode).HasMaxLength(50);
            entity.Property(x => x.LevelName).HasMaxLength(255);
            entity.Property(x => x.MinScore).HasPrecision(7, 4);
            entity.Property(x => x.MaxScore).HasPrecision(7, 4);
        });

        modelBuilder.Entity<LinkType>(entity =>
        {
            entity.ToTable("LinkTypes");
            entity.HasKey(x => x.LinkTypeId);
            entity.Property(x => x.LinkTypeCode).HasMaxLength(50);
            entity.Property(x => x.LinkTypeName).HasMaxLength(255);
        });

        modelBuilder.Entity<FeedbackStatus>(entity =>
        {
            entity.ToTable("FeedbackStatuses");
            entity.HasKey(x => x.FeedbackStatusId);
            entity.Property(x => x.StatusCode).HasMaxLength(50);
            entity.Property(x => x.StatusName).HasMaxLength(255);
        });

        modelBuilder.Entity<ModelVersion>(entity =>
        {
            entity.ToTable("ModelVersions");
            entity.HasKey(x => x.ModelVersionId);
            entity.Property(x => x.ModelCode).HasMaxLength(50);
            entity.Property(x => x.ModelName).HasMaxLength(255);
        });

        

        

        modelBuilder.Entity<PredictionRequest>(entity =>
        {
            entity.ToTable("PredictionRequests");
            entity.HasKey(x => x.PredictionRequestId);

            entity.Property(x => x.RequestCode).HasMaxLength(50);
            entity.Property(x => x.ScoreThreshold).HasPrecision(7, 4);
            entity.Property(x => x.RequestStatus).HasMaxLength(50);
            entity.Property(x => x.Purpose).HasMaxLength(200);
            entity.Property(x => x.ContactEmail).HasMaxLength(255);

            entity.HasOne(x => x.PredictionType)
                .WithMany()
                .HasForeignKey(x => x.PredictionTypeId);

            entity.HasOne(x => x.InputDrug)
                .WithMany()
                .HasForeignKey(x => x.InputDrugId);

            entity.HasOne(x => x.InputDisease)
                .WithMany()
                .HasForeignKey(x => x.InputDiseaseId);
        });

        modelBuilder.Entity<PredictionRun>(entity =>
        {
            entity.ToTable("PredictionRuns");
            entity.HasKey(x => x.PredictionRunId);

            entity.Property(x => x.PredictionRunCode).HasMaxLength(50);
            entity.Property(x => x.ModuleName).HasMaxLength(150);
            entity.Property(x => x.ScoreThreshold).HasPrecision(7, 4);
            entity.Property(x => x.ProcessingConclusion).HasMaxLength(200);
            entity.Property(x => x.RunStatus).HasMaxLength(50);
            entity.Property(x => x.MandatoryMedicalWarning).HasMaxLength(1000);

            entity.HasOne(x => x.PredictionRequest)
                .WithMany(x => x.PredictionRuns)
                .HasForeignKey(x => x.PredictionRequestId);

            entity.HasOne(x => x.ModelVersion)
                .WithMany()
                .HasForeignKey(x => x.ModelVersionId);
        });

        modelBuilder.Entity<PredictionResult>(entity =>
        {
            entity.ToTable("PredictionResults");
            entity.HasKey(x => x.PredictionResultId);

            entity.Property(x => x.PredictionScore).HasPrecision(9, 6);
            entity.Property(x => x.ShortExplanation).HasMaxLength(1000);

            entity.HasOne(x => x.PredictionRun)
                .WithMany(x => x.PredictionResults)
                .HasForeignKey(x => x.PredictionRunId);

            entity.HasOne(x => x.Drug)
                .WithMany()
                .HasForeignKey(x => x.DrugId);

            entity.HasOne(x => x.Disease)
                .WithMany()
                .HasForeignKey(x => x.DiseaseId);

            entity.HasOne(x => x.KnownLink)
                .WithMany()
                .HasForeignKey(x => x.KnownLinkId);

            entity.HasOne(x => x.ConfidenceLevel)
                .WithMany()
                .HasForeignKey(x => x.ConfidenceLevelId);

            entity.HasOne(x => x.LinkType)
                .WithMany()
                .HasForeignKey(x => x.LinkTypeId);
        });

        modelBuilder.Entity<PredictionFeedback>(entity =>
        {
            entity.ToTable("PredictionFeedbacks");
            entity.HasKey(x => x.FeedbackId);

            entity.Property(x => x.FeedbackCode).HasMaxLength(50);
            entity.Property(x => x.GeneralAssessment).HasMaxLength(100);
            entity.Property(x => x.SuggestedAction).HasMaxLength(200);

            entity.HasOne(x => x.PredictionRun)
                .WithMany()
                .HasForeignKey(x => x.PredictionRunId);

            entity.HasOne(x => x.PredictionResult)
                .WithMany()
                .HasForeignKey(x => x.PredictionResultId);

            entity.HasOne(x => x.FeedbackStatus)
                .WithMany()
                .HasForeignKey(x => x.FeedbackStatusId);
        });
    }
}