#!/usr/bin/env python3
"""
Compute the paired statistical analysis reported in the manuscript.

By default, the analysis compares paired token counts of the stored PEaC module
contents before and after refactoring:

    Delta_i = T_peac,i - T_orig,i

Negative values therefore indicate token reduction after refactoring.
"""

import argparse
import math
import os
import statistics
from pathlib import Path

import pandas as pd
from scipy import stats

from common import count_tokens, get_all_sentences_from_yaml
from semantic_similarity_analysis import get_full_rendered_prompt


def get_token_count(yaml_path: str, token_source: str, workspace_root: str) -> int:
    """Count tokens according to the selected token source."""
    if token_source == "raw":
        return count_tokens(Path(yaml_path).read_text(encoding="utf-8"))

    if token_source == "stored":
        return count_tokens(" ".join(get_all_sentences_from_yaml(yaml_path)))

    if token_source == "rendered":
        return count_tokens(get_full_rendered_prompt(yaml_path, workspace_root))

    raise ValueError(f"Unsupported token source: {token_source}")


def build_paired_token_dataframe(
    original_dir: str = "peac_modules_single",
    refactored_dir: str = "refactored_peac_modules",
    token_source: str = "stored",
) -> pd.DataFrame:
    """Build paired token counts for original/refactored modules."""
    workspace_root = os.path.abspath(".")

    original_files = {f for f in os.listdir(original_dir) if f.endswith(".yaml")}
    refactored_files = {f for f in os.listdir(refactored_dir) if f.endswith(".yaml")}
    common_files = sorted(original_files & refactored_files)

    rows = []
    for filename in common_files:
        original_path = os.path.join(original_dir, filename)
        refactored_path = os.path.join(refactored_dir, filename)

        original_tokens = get_token_count(original_path, token_source, workspace_root)
        refactored_tokens = get_token_count(refactored_path, token_source, workspace_root)

        rows.append(
            {
                "filename": filename,
                "original_tokens": original_tokens,
                "refactored_tokens": refactored_tokens,
                "delta": refactored_tokens - original_tokens,
            }
        )

    return pd.DataFrame(rows)


def compute_statistics(df: pd.DataFrame) -> dict:
    """Compute descriptive and inferential paired statistics."""
    deltas = df["delta"].tolist()
    n = len(deltas)

    mean_delta = statistics.mean(deltas)
    std_delta = statistics.stdev(deltas)
    variance_delta = statistics.variance(deltas)
    se_delta = std_delta / math.sqrt(n)
    median_delta = statistics.median(deltas)
    quartiles = statistics.quantiles(deltas, n=4, method="inclusive")
    q1_delta = quartiles[0]
    q3_delta = quartiles[2]
    iqr_delta = q3_delta - q1_delta

    ci_low, ci_high = stats.t.interval(0.95, df=n - 1, loc=mean_delta, scale=se_delta)
    shapiro_result = stats.shapiro(deltas)
    wilcoxon_result = stats.wilcoxon(deltas, alternative="less", method="approx")
    ttest_result = stats.ttest_rel(df["refactored_tokens"], df["original_tokens"], alternative="less")

    zstat = getattr(wilcoxon_result, "zstatistic", None)
    wilcoxon_r = (zstat / math.sqrt(n)) if zstat is not None else None
    cohen_dz = mean_delta / std_delta if std_delta else 0.0

    return {
        "n": n,
        "mean_delta": mean_delta,
        "std_delta": std_delta,
        "variance_delta": variance_delta,
        "se_delta": se_delta,
        "median_delta": median_delta,
        "q1_delta": q1_delta,
        "q3_delta": q3_delta,
        "iqr_delta": iqr_delta,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "shapiro_w": shapiro_result.statistic,
        "shapiro_pvalue": shapiro_result.pvalue,
        "wilcoxon_statistic": wilcoxon_result.statistic,
        "wilcoxon_pvalue": wilcoxon_result.pvalue,
        "wilcoxon_z": zstat,
        "wilcoxon_r": wilcoxon_r,
        "ttest_statistic": ttest_result.statistic,
        "ttest_pvalue": ttest_result.pvalue,
        "ttest_df": ttest_result.df,
        "cohen_dz": cohen_dz,
        "negative_deltas": int(sum(1 for x in deltas if x < 0)),
        "zero_deltas": int(sum(1 for x in deltas if x == 0)),
        "positive_deltas": int(sum(1 for x in deltas if x > 0)),
    }


def format_report(stats_dict: dict, token_source: str) -> str:
    """Format a manuscript-friendly report."""
    lines = [
        "STATISTICAL REPORTING",
        "=" * 80,
        f"token_source = {token_source}",
        f"n = {stats_dict['n']}",
        f"mean(delta) = {stats_dict['mean_delta']:.5f}",
        f"std(delta) = {stats_dict['std_delta']:.6f}",
        f"variance(delta) = {stats_dict['variance_delta']:.2f}",
        f"SE(delta) = {stats_dict['se_delta']:.7f}",
        f"median(delta) = {stats_dict['median_delta']:.5f}",
        f"Q1(delta) = {stats_dict['q1_delta']:.5f}",
        f"Q3(delta) = {stats_dict['q3_delta']:.5f}",
        f"IQR(delta) = {stats_dict['iqr_delta']:.5f}",
        f"95% CI = [{stats_dict['ci_low']:.5f}, {stats_dict['ci_high']:.5f}]",
        "",
        "Normality diagnostic",
        f"Shapiro-Wilk W = {stats_dict['shapiro_w']:.5f}",
        f"Shapiro-Wilk p-value = {stats_dict['shapiro_pvalue']:.8g}",
        "",
        "Wilcoxon signed-rank test",
        f"W = {stats_dict['wilcoxon_statistic']:.5f}",
        f"p-value = {stats_dict['wilcoxon_pvalue']:.8g}",
    ]

    if stats_dict["wilcoxon_z"] is not None:
        lines.append(f"z = {stats_dict['wilcoxon_z']:.5f}")
    if stats_dict["wilcoxon_r"] is not None:
        lines.append(f"r = {stats_dict['wilcoxon_r']:.5f}")

    lines.extend(
        [
            "",
            "Paired t-test (robustness check)",
            f"t = {stats_dict['ttest_statistic']:.5f}",
            f"df = {stats_dict['ttest_df']}",
            f"p-value = {stats_dict['ttest_pvalue']:.8g}",
            "",
            "Effect size",
            f"Cohen's d_z = {stats_dict['cohen_dz']:.5f}",
            "",
            "Delta counts",
            f"negative = {stats_dict['negative_deltas']}",
            f"zero = {stats_dict['zero_deltas']}",
            f"positive = {stats_dict['positive_deltas']}",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute paired token statistics for the PEaC experiment")
    parser.add_argument(
        "--token-source",
        choices=["stored", "rendered", "raw"],
        default="stored",
        help="How tokens are counted for each paired module",
    )
    parser.add_argument(
        "--csv-output",
        default="out/statistical_reporting_pairs.csv",
        help="Path for the paired token CSV",
    )
    parser.add_argument(
        "--report-output",
        default="out/statistical_reporting.txt",
        help="Path for the text report",
    )
    args = parser.parse_args()

    df = build_paired_token_dataframe(token_source=args.token_source)
    stats_dict = compute_statistics(df)
    report = format_report(stats_dict, token_source=args.token_source)

    csv_path = Path(args.csv_output)
    report_path = Path(args.report_output)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(csv_path, index=False)
    report_path.write_text(report + "\n", encoding="utf-8")

    print(report)
    print()
    print(f"paired_csv={csv_path}")
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
