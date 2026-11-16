# Explainable AI for Network Intrusion Detection

Code for the master's thesis *Evaluating Explainable AI Methods for Intrusion Detection Systems:
From Model Explanations to Security Decisions* (Marco Avila, Universität Hamburg, 2026). It
trains four class-weighted classifiers (random forest, XGBoost, multilayer perceptron, linear SVM)
on UNSW-NB15 and CIC-IDS2017, explains them with SHAP, LIME and permutation feature importance,
and measures how far the explanations agree. The expert interviews (thesis Section 3.5 and
Appendix A.4-A.6) are documented in the thesis only; this repository produces the plots that were
shown in them.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/xai_thesis/datasets/` | Dataset adapters: loading and cleaning of the raw files |
| `src/xai_thesis/preprocessing.py` | Train/test split and the preprocessing pipeline (imputation, scaling, encoding) |
| `src/xai_thesis/screening.py` | Constant and near-duplicate column screen |
| `src/xai_thesis/models.py` | The four models and their hyperparameter search spaces |
| `src/xai_thesis/torch_mlp.py` | The class-weighted PyTorch MLP with a scikit-learn interface |
| `src/xai_thesis/evaluation.py` | Metrics, confusion matrices and data plots |
| `src/xai_thesis/explainability.py` | SHAP, LIME, permutation feature importance and their plots |
| `src/xai_thesis/agreement.py` | Feature and rank agreement (Krishna et al., 2024) |
| `src/xai_thesis/explanation_report.py` | The global and local explanation tables reported in the thesis |
| `src/xai_thesis/stimuli.py` | Error profiles used to choose the interview stimuli |
| `src/xai_thesis/pipeline.py` | End-to-end steps called by the scripts |
| `scripts/` | Command-line entry points, one per pipeline step |
| `configs/datasets/`, `configs/experiments/` | Dataset settings and the eight model configurations, including the selected hyperparameters (Table A.3) |
| `tests/` | Unit and integration tests |
| `results/` | The metrics and tables reported in the thesis (see below) |

## Setup

The experiments were run with Python 3.14.0 on Windows 11; `requirements.lock` pins the exact
environment (scikit-learn 1.9.0, xgboost 3.4.1, PyTorch 2.13.0 (CPU), shap 0.52.0, lime 0.2.0.1).

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock --extra-index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python -m pip install -e . --no-deps
.venv\Scripts\Activate.ps1
```

## Data

The datasets are not included. Place the original CSV files as follows:

| Dataset | Source | Files |
| --- | --- | --- |
| UNSW-NB15 | <https://research.unsw.edu.au/projects/unsw-nb15-dataset> | `UNSW-NB15_1.csv` to `UNSW-NB15_4.csv` and `NUSW-NB15_features.csv` in `data/raw/UNSW_NB15/` |
| CIC-IDS2017 | <https://www.unb.ca/cic/datasets/ids-2017.html> (MachineLearningCVE) | the eight `*.pcap_ISCX.csv` files in `data/raw/CIC_IDS2017/` |

## Reproducing the results

Run the steps in order from the repository root. Each script processes all datasets or
configurations unless restricted with `--dataset` or `--experiment`. Generated files go to
`data/processed/` and `outputs/`, which are not tracked.

```powershell
# 1. Cleaning, deduplication and the stratified 70/30 split (writes data/processed/)
python scripts/preprocess.py

# 2. Class distributions and the redundancy screen
python scripts/label_distribution.py
python scripts/feature_screen.py

# 3. Training and test-set evaluation (add --tune to rerun the hyperparameter search first)
Get-ChildItem configs/experiments/*.yaml | ForEach-Object { python scripts/train.py --experiment $_.FullName }
python scripts/confusion_matrix.py
python scripts/roc_curve.py

# 4. Global explanations: SHAP and permutation feature importance
python scripts/explain.py

# 5. Local agreement between SHAP and LIME
python scripts/agreement.py

# 6. Report tables and the agreement figure
python scripts/stimulus_candidates.py
python scripts/explanation_report.py
python scripts/thesis_agreement_figure.py

# 7. Local SHAP and LIME plots of the interview alerts
python scripts/interview_stimuli.py
```

All results were produced on an AMD Ryzen 9 9955HX (16 cores) with 16 GB RAM. There, the random
forest, XGBoost and the MLP train in minutes and the SVM in up to a few hours. The SVM's SHAP
values are estimated by sampling and dominate the run time: its local agreement takes about 1.5
hours (UNSW-NB15) and 7 hours (CIC-IDS2017). Global SHAP for the CIC-IDS2017 SVM is skipped by
default (see its config); to compute it, set `skip_global_shap: false` and run it in parallel
chunks:

```powershell
python scripts/explain.py --experiment configs/experiments/cic_ids2017_svm_baseline.yaml --shap-chunk-size 5 --shap-n-jobs 8
```

Global SHAP computed in chunks seeds each chunk separately (seed 42 + chunk number), so its values
are reproducible for a given `--shap-chunk-size` but not bit-identical to a single-call run.

The two interview alerts (XGBoost on CIC-IDS2017) are pinned to test rows 59216 (DoS/DDoS) and
55480 (Brute Force), both correctly classified. The alert cards shown in the interviews are
mock-ups; their metadata and confidence values (0.98 for DoS/DDoS, 0.95 for Brute Force) are
illustrative and do not come from the model.

Two auxiliary scripts are not needed for the thesis results: `scripts/inspect_datasets.py`
summarizes the raw files (columns, missing and non-finite values, labels) and
`scripts/dataset_diagnostics.py` plots missing values, the train/test split and feature
correlations of the processed data.

## Where the thesis results come from

| Thesis content | Script | Output | Copy in `results/` |
| --- | --- | --- | --- |
| Raw class distributions (Figures 3.2, 3.3) | `label_distribution.py` | `outputs/plots/<dataset>/data/label_distribution_raw.png` | `dataset_inspection/<dataset>_label_distribution_raw.csv` |
| Class distribution after preprocessing (Table A.2) | `label_distribution.py` | `outputs/metrics/dataset_inspection/<dataset>/label_distribution_split.csv` | `dataset_inspection/<dataset>_label_distribution_split.csv` |
| Constant and near-duplicate columns (Table A.1) | `feature_screen.py` | `outputs/metrics/dataset_inspection/<dataset>/feature_screen.csv` | `dataset_inspection/<dataset>_feature_screen.csv` |
| Performance (Tables 4.1, 4.2) | `train.py` | `outputs/metrics/<experiment>.json` | `metrics/` |
| Confusion matrices (Figures 4.1-4.4) | `confusion_matrix.py` | `outputs/plots/<dataset>/<model>_baseline/performance/` | `confusion_matrices/` |
| Global explanations (Figures 4.5-4.8) and top-10 overlap (Table 4.3) | `explain.py`, `explanation_report.py` | `outputs/plots/<dataset>/<model>_baseline/global/` | `explanation_report/global_top10.csv`, `global_overlap.csv` |
| Local SHAP and LIME plots of the interview alerts (Figures 4.9, 4.10, Appendix A.4) | `interview_stimuli.py` | `outputs/plots/cic_ids2017/xgboost_baseline/interview/` | - |
| Local agreement between SHAP and LIME (Figure 4.11) | `agreement.py`, `explanation_report.py`, `thesis_agreement_figure.py` | `outputs/plots/thesis_figures/` | `explanation_report/local_agreement.csv` |

The report tables are written to `outputs/metrics/explanation_report/`; `sample_sizes.csv` there
gives the per-class composition of the global (500 and 437 flows) and local (60 and 56 flows)
explanation samples.

## Method summary

- **Cleaning:** label normalization (CIC-IDS2017: seven consolidated classes); infinite values
  treated as missing; removal of corrupted records, identifiers, timestamps, the destination-port
  proxy `service` (UNSW-NB15), constant columns and columns matching a retained one in at least
  99.99% of rows, and exact duplicate records. The dataset-specific steps are documented in
  `src/xai_thesis/datasets/` and `configs/datasets/`.
- **Preprocessing:** stratified 70/30 split; median imputation, min-max scaling and one-hot
  encoding (categories below 1% grouped), all fitted on the training partition.
- **Models:** balanced class weights for all four models. Hyperparameters are selected by
  randomized search (up to 30 configurations) with stratified 3-fold cross-validation and
  macro-F1 on a 200,000-row stratified subsample of the training partition. The MLP holds out
  10% of the training partition for early stopping. The SVM's final fit uses a stratified
  subsample of about 200,000 rows with at least 500 per class where available.
- **Explanations:** TreeExplainer for the tree ensembles (exact; XGBoost on the raw margin, labelled
  log-odds in the plots, the random forest in probabilities) and the permutation explainer for the
  SVM and the MLP (sampled, in probabilities, with 50 permutations and a class-balanced background
  of training rows: 5 per class on UNSW-NB15 (50 rows), 7 per class on CIC-IDS2017 (49 rows));
  LIME on the predicted probabilities; permutation importance as the macro-F1 drop over 10
  repetitions on the full pipeline. Global explanations use a class-balanced test sample (500 and
  437 instances), the agreement analysis another one (60 and 56 instances). For the tree models,
  the SHAP base value E[f(X)] is computed by TreeExplainer from statistics stored in the trees; for
  XGBoost it is not the average model output (see `compute_shap_values`).
- **Reproducibility:** all random components use the seed 42.

## Tests

```powershell
python -m pytest
```

## Citation

Avila, M. (2026). *Evaluating Explainable AI Methods for Intrusion Detection Systems: From Model
Explanations to Security Decisions* [Master's thesis, Universität Hamburg].
