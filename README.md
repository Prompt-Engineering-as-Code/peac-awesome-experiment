# PEaC Experiment Reproduction

This branch contains the artifact set needed to reproduce the experiment reported in the PEaC manuscript.

The experiment evaluates whether modular prompt composition improves token efficiency and reuse by comparing:

- non-modular, self-contained PEaC modules
- refactored modular PEaC modules that reuse shared base modules through `extends`

The repository is organized to support the analyses described in the paper:

- dataset characterization based on the enriched Awesome ChatGPT Prompts corpus
- quantitative modularization metrics: Token Reduction Ratio (TRR), Reuse Efficiency (RE), and Modularity Index (MI)
- paired statistical reporting over the 210 prompt pairs
- semantic similarity analysis between self-contained and modularized prompts
- generation of the token-reduction figure used in the manuscript

## Repository contents

### Datasets

- `awesome_chatgpt_prompts_enriched.csv`: enriched prompt dataset used for dataset-level reporting
- `peac_modules_single/`: 210 non-modular PEaC modules
- `refactored_peac_modules/`: 210 modular PEaC leaf modules
- `extends/`: 173 reusable base modules used by the modular PEaC corpus

### Analysis scripts

- `dataset_analysis.py`
  Purpose: summarizes the enriched dataset used in the experiment.
  Input: `awesome_chatgpt_prompts_enriched.csv`, `peac_modules_single/`, `refactored_peac_modules/`, `extends/`.
  Output: prints dataset counts to the terminal and writes `out/dataset_domain_counts.csv`.
- `detailed_metrics.py`
  Purpose: computes the core modularization metrics reported in the manuscript.
  Input: `peac_modules_single/`, `refactored_peac_modules/`, `extends/`.
  Output: prints `ΣT_orig`, `ΣT_peac`, `|M|`, `|L|`, `d_avg`, `TRR`, `RE`, and `MI` to the terminal, together with a LaTeX-ready table snippet.
- `create_metrics_diagram.py`
  Purpose: generates the token-reduction figure comparing self-contained and modular PEaC corpora.
  Input: `peac_modules_single/`, `refactored_peac_modules/`, `extends/`.
  Output: writes `out/peac_token_reduction_diagram.png` and `out/peac_token_reduction_diagram.pdf`.
- `statistical_reporting.py`
  Purpose: computes the paired statistical analysis for token differences before and after refactoring.
  Input: `peac_modules_single/`, `refactored_peac_modules/`.
  Output: prints descriptive statistics, median/IQR, normality diagnostics, Wilcoxon signed-rank test, paired $t$-test, and effect sizes; writes `out/statistical_reporting_pairs.csv` and `out/statistical_reporting.txt`.
  Main option: `--token-source {stored,rendered,raw}` controls how per-file tokens are counted. The manuscript-aligned default is `stored`.
- `semantic_similarity_analysis.py`
  Purpose: evaluates semantic preservation between self-contained and modularized prompts.
  Input: `peac_modules_single/`, `refactored_peac_modules/`, `extends/`.
  Output: prints summary statistics for cosine similarity, BLEU, BERTScore, and ROUGE; by default writes `out/semantic_similarity_results.csv` and `out/semantic_similarity_plot.png`.
  Main options: `--output` sets the CSV output path and `--sample N` runs the analysis on a subset of file pairs.

### Support code

- `common.py`
- `peac.py`

## Environment setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Reproducing the paper analyses

Run the following commands from the repository root:

```bash
python dataset_analysis.py
python detailed_metrics.py
python create_metrics_diagram.py
python statistical_reporting.py
python semantic_similarity_analysis.py --output out/semantic_similarity_results.csv
```

All generated artifacts are written to `out/`.

## Script inputs and outputs at a glance

| Script | Main inputs | Main outputs |
|---|---|---|
| `dataset_analysis.py` | `awesome_chatgpt_prompts_enriched.csv`, module directories | `out/dataset_domain_counts.csv` |
| `detailed_metrics.py` | `peac_modules_single/`, `refactored_peac_modules/`, `extends/` | terminal report and LaTeX table snippet |
| `create_metrics_diagram.py` | `peac_modules_single/`, `refactored_peac_modules/`, `extends/` | `out/peac_token_reduction_diagram.png`, `out/peac_token_reduction_diagram.pdf` |
| `statistical_reporting.py` | paired PEaC modules | `out/statistical_reporting_pairs.csv`, `out/statistical_reporting.txt` |
| `semantic_similarity_analysis.py` | paired PEaC modules, `extends/` | `out/semantic_similarity_results.csv`, `out/semantic_similarity_plot.png` |

## Expected findings

The main quantitative results obtained when executing the analysis are as follows:

- dataset size: 215 enriched prompts across 10 domains
- analyzed PEaC pairs: 210
- reusable base modules: 173
- `ΣT_orig = 65,145`
- `ΣT_peac = 49,465`
- `TRR = 24.07%`
- `RE = 51.25%`
- `MI = 2.707`

The paired token analysis should report a negative mean difference of approximately `-84.33` tokens per pair, a median of `-52.00`, an IQR of `135.00`, a 95% confidence interval close to `[-93.47, -75.19]`, and a statistically significant Wilcoxon signed-rank result (`W = 0.00`, `p < 0.0001`).

The semantic similarity analysis is intended as supplementary evidence that modularization preserves prompt meaning. The manuscript reports high similarity across all 210 prompt pairs, including approximately:

- cosine similarity: `0.944 ± 0.039`
- BLEU: `0.701 ± 0.192`
- BERTScore F1: `0.930 ± 0.028`
- ROUGE-1 F1: `0.838 ± 0.109`
- ROUGE-2 F1: `0.794 ± 0.121`
