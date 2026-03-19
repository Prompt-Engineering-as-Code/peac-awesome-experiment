#!/usr/bin/env python3
"""Generate JMP-ready CSV files for paired token reduction analysis."""

import os
import pandas as pd
from common import count_tokens
from semantic_similarity_analysis import get_full_rendered_prompt


def build_jmp_datasets(original_dir: str = "peac_modules_single",
                       refactored_dir: str = "refactored_peac_modules",
                       output_paired: str = "out/jmp_token_paired.csv",
                       output_long: str = "out/jmp_token_long.csv") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build paired and long-format datasets for JMP."""
    root = os.path.abspath(".")

    os.makedirs(os.path.dirname(output_paired) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_long) or ".", exist_ok=True)

    original_files = {f for f in os.listdir(original_dir) if f.endswith(".yaml")}
    refactored_files = {f for f in os.listdir(refactored_dir) if f.endswith(".yaml")}
    common_files = sorted(original_files & refactored_files)

    rows = []
    for idx, filename in enumerate(common_files, start=1):
        original_path = os.path.join(original_dir, filename)
        refactored_path = os.path.join(refactored_dir, filename)

        original_text = get_full_rendered_prompt(original_path, root)
        refactored_text = get_full_rendered_prompt(refactored_path, root)

        original_tokens = count_tokens(original_text)
        refactored_tokens = count_tokens(refactored_text)
        token_diff = original_tokens - refactored_tokens
        token_reduction_pct = (token_diff / original_tokens * 100.0) if original_tokens > 0 else 0.0

        rows.append({
            "pair_id": idx,
            "filename": filename,
            "original_tokens": original_tokens,
            "refactored_tokens": refactored_tokens,
            "token_diff": token_diff,
            "token_reduction_pct": token_reduction_pct,
        })

    paired_df = pd.DataFrame(rows)
    paired_df.to_csv(output_paired, index=False)

    long_df = pd.concat(
        [
            paired_df[["pair_id", "filename", "original_tokens"]]
            .rename(columns={"original_tokens": "tokens"})
            .assign(version="original"),
            paired_df[["pair_id", "filename", "refactored_tokens"]]
            .rename(columns={"refactored_tokens": "tokens"})
            .assign(version="refactored"),
        ],
        ignore_index=True,
    )
    long_df = long_df[["pair_id", "filename", "version", "tokens"]]
    long_df.to_csv(output_long, index=False)

    return paired_df, long_df


def main() -> None:
    output_paired = "out/jmp_token_paired.csv"
    output_long = "out/jmp_token_long.csv"
    paired_df, _ = build_jmp_datasets(output_paired=output_paired, output_long=output_long)

    print(f"paired_rows={len(paired_df)}")
    print(f"saved={output_paired},{output_long}")
    print(f"mean_original={paired_df['original_tokens'].mean():.2f}")
    print(f"mean_refactored={paired_df['refactored_tokens'].mean():.2f}")
    print(f"mean_diff={paired_df['token_diff'].mean():.2f}")
    print(f"mean_reduction_pct={paired_df['token_reduction_pct'].mean():.2f}")
    print(f"median_reduction_pct={paired_df['token_reduction_pct'].median():.2f}")
    print(f"n_positive_diff={(paired_df['token_diff'] > 0).sum()}")
    print(f"n_zero_diff={(paired_df['token_diff'] == 0).sum()}")
    print(f"n_negative_diff={(paired_df['token_diff'] < 0).sum()}")


if __name__ == "__main__":
    main()
