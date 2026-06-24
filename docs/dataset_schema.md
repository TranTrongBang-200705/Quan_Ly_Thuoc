# Drug-Disease Link Dataset

This dataset is a small training sample for predicting whether a drug is linked to a disease.

## Columns

- `drug_id`: Stable identifier for the drug.
- `drug_name`: Drug display name.
- `disease_id`: Stable identifier for the disease.
- `disease_name`: Disease display name.
- `drug_class`: Pharmacological class.
- `disease_group`: Disease category.
- `mechanism_overlap`: Numeric score from 0 to 1 describing biological mechanism similarity.
- `clinical_evidence`: Numeric score from 0 to 1 describing observed evidence strength.
- `known_link`: Target label. `1` means linked, `0` means not linked.

## Goal

Train a RandomForest classifier to estimate the probability that a drug and disease should be linked.
