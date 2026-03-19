#!/usr/bin/env python3
"""
Calculate detailed metrics for the LaTeX table.
"""

import os
import yaml
from common import (
    calculate_token_reduction_ratio, 
    calculate_reuse_efficiency, 
    calculate_modularity_index,
    count_tokens,
    get_all_sentences_from_yaml,
    collect_base_modules_and_sentences
)

def get_detailed_metrics():
    """Calculate all metrics needed for the LaTeX table."""
    
    original_dir = "peac_modules_single"
    refactored_dir = "refactored_peac_modules"
    
    print("Calculating detailed metrics for LaTeX table...")
    print("=" * 60)
    
    # Calculate token counts
    # Original tokens (Σ T_orig)
    all_orig_sentences = []
    orig_files = [f for f in os.listdir(original_dir) if f.endswith('.yaml')]
    
    for filename in orig_files:
        yaml_path = os.path.join(original_dir, filename)
        try:
            sentences = get_all_sentences_from_yaml(yaml_path)
            all_orig_sentences.extend(sentences)
        except Exception as e:
            print(f"Warning: Could not process original file {filename}: {e}")
    
    total_orig_tokens = count_tokens(' '.join(all_orig_sentences))
    
    # PEaC tokens (Σ T_peac)
    all_peac_sentences = []
    
    # Get sentences from leaf modules
    refactored_files = [f for f in os.listdir(refactored_dir) if f.endswith('.yaml')]
    for filename in refactored_files:
        yaml_path = os.path.join(refactored_dir, filename)
        try:
            sentences = get_all_sentences_from_yaml(yaml_path)
            all_peac_sentences.extend(sentences)
        except Exception as e:
            print(f"Warning: Could not process refactored file {filename}: {e}")
    
    # Get sentences from base modules
    base_modules, base_sentences, _ = collect_base_modules_and_sentences(refactored_dir)
    for module_path, sentences in base_sentences.items():
        all_peac_sentences.extend(sentences)
    
    total_peac_tokens = count_tokens(' '.join(all_peac_sentences))
    
    # Number of base modules (|M|)
    num_base_modules = len(base_modules)
    
    # Number of leaf prompts (|L|)
    num_leaf_prompts = len(refactored_files)
    
    # Calculate d_avg (average number of extends per leaf)
    total_extends = 0
    valid_leaves = 0
    
    for filename in refactored_files:
        yaml_path = os.path.join(refactored_dir, filename)
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            extends_count = 0
            if 'prompt' in data and 'extends' in data['prompt']:
                extends_list = data['prompt']['extends']
                if isinstance(extends_list, list):
                    extends_count = len(extends_list)
                elif isinstance(extends_list, str):
                    extends_count = 1
            
            total_extends += extends_count
            valid_leaves += 1
            
        except Exception as e:
            print(f"Warning: Could not parse {yaml_path}: {e}")
    
    d_avg = total_extends / valid_leaves if valid_leaves > 0 else 0
    
    # Calculate the main metrics
    trr = calculate_token_reduction_ratio(original_dir, refactored_dir)
    re = calculate_reuse_efficiency(original_dir, refactored_dir)
    mi = calculate_modularity_index(refactored_dir)
    
    # Print results
    print(f"Σ T_orig (Original tokens):     {total_orig_tokens:,}")
    print(f"Σ T_peac (PEaC tokens):        {total_peac_tokens:,}")
    print(f"|M| (Base modules):            {num_base_modules}")
    print(f"|L| (Leaf prompts):            {num_leaf_prompts}")
    print(f"d_avg (Avg extends per leaf):  {d_avg:.2f}")
    print(f"TRR (Token Reduction Ratio):   {trr:.2f}%")
    print(f"RE (Reuse Efficiency):         {re:.2f}%")
    print(f"MI (Modularity Index):         {mi:.3f}")
    
    print("\n" + "=" * 60)
    print("LATEX TABLE FORMAT:")
    print("=" * 60)
    
    # Format for LaTeX table
    latex_table = f"""\\label{{tab:metrics}}
\\begin{{tabular}}{{l r}}
\\toprule
\\textbf{{Metric}} & \\textbf{{Value}} \\\\
\\midrule
$\\Sigma T_{{orig}}$ & ${total_orig_tokens:,}$ \\\\
$\\Sigma T_{{peac}}$ & ${total_peac_tokens:,}$ \\\\
$|M|$ & ${num_base_modules}$ \\\\
$|L|$ & ${num_leaf_prompts}$ \\\\
$d_{{avg}}$ & ${d_avg:.2f}$ \\\\
$TRR$ & ${trr:.2f}\\,\\%$ \\\\
$RE$ & ${re:.2f}\\,\\%$ \\\\
$MI$ & ${mi:.3f}$ \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}"""
    
    print(latex_table)
    
    return {
        'total_orig_tokens': total_orig_tokens,
        'total_peac_tokens': total_peac_tokens,
        'num_base_modules': num_base_modules,
        'num_leaf_prompts': num_leaf_prompts,
        'd_avg': d_avg,
        'trr': trr,
        're': re,
        'mi': mi
    }

if __name__ == "__main__":
    get_detailed_metrics()