#!/usr/bin/env python3
"""
Summarize the experiment datasets used in the manuscript.
"""

import argparse
import os
from pathlib import Path

import pandas as pd


DOMAIN_LABELS = {
    "entertainment-games": "Entertainment Games",
    "education-training": "Education Training",
    "technology-development": "Technology Development",
    "creative-arts": "Creative Arts",
    "health-wellness": "Health Wellness",
    "business-finance": "Business Finance",
    "utilities-tools": "Utilities Tools",
    "specialized-roles": "Specialized Roles",
    "personal-lifestyle": "Personal Lifestyle",
    "talk": "Talk",
}


def build_domain_counts(csv_path: str = "awesome_chatgpt_prompts_enriched.csv") -> pd.DataFrame:
    """Return prompt counts by domain from the enriched dataset CSV."""
    df = pd.read_csv(csv_path)
    counts = df["domain"].value_counts().rename_axis("domain").reset_index(name="prompts")
    counts["Domain"] = counts["domain"].map(DOMAIN_LABELS).fillna(counts["domain"])
    counts = counts[["Domain", "prompts"]]
    return counts.sort_values(["Domain"]).reset_index(drop=True)


def dataset_summary(
    csv_path: str = "awesome_chatgpt_prompts_enriched.csv",
    original_dir: str = "peac_modules_single",
    refactored_dir: str = "refactored_peac_modules",
    extends_dir: str = "extends",
) -> dict:
    """Compute the headline dataset counts used in the paper."""
    enriched_df = pd.read_csv(csv_path)
    original_modules = len([f for f in os.listdir(original_dir) if f.endswith(".yaml")])
    refactored_modules = len([f for f in os.listdir(refactored_dir) if f.endswith(".yaml")])
    base_modules = sum(1 for path in Path(extends_dir).rglob("*.yaml"))

    return {
        "total_prompts_in_csv": len(enriched_df),
        "domains": enriched_df["domain"].nunique(),
        "non_modular_modules": original_modules,
        "modular_leaf_modules": refactored_modules,
        "base_modules": base_modules,
        "excluded_prompts": len(enriched_df) - original_modules,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize the experiment datasets")
    parser.add_argument(
        "--csv-output",
        default="out/dataset_domain_counts.csv",
        help="Path for the domain-count CSV",
    )
    args = parser.parse_args()

    counts = build_domain_counts()
    summary = dataset_summary()

    csv_path = Path(args.csv_output)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(csv_path, index=False)

    print("DATASET SUMMARY")
    print("=" * 80)
    print(f"Total prompts in enriched CSV: {summary['total_prompts_in_csv']}")
    print(f"Domains: {summary['domains']}")
    print(f"Non-modular PEaC modules: {summary['non_modular_modules']}")
    print(f"Modular leaf modules: {summary['modular_leaf_modules']}")
    print(f"Reusable base modules: {summary['base_modules']}")
    print(f"Excluded prompts: {summary['excluded_prompts']}")
    print()
    print("PROMPTS PER DOMAIN")
    print(counts.to_string(index=False))
    print()
    print(f"domain_counts_csv={csv_path}")


if __name__ == "__main__":
    main()
