# RandomForest Evaluation

The training script evaluates the drug-disease link classifier on a stratified holdout set.

## Metrics

- `accuracy`: Overall classification correctness.
- `precision`: How many predicted links are correct.
- `recall`: How many known links are recovered.
- `f1`: Balance between precision and recall.
- `roc_auc`: Ranking quality for link probability.
- `confusion_matrix`: True negative, false positive, false negative, true positive counts.

The report is written to `reports/random_forest_metrics.json`.
