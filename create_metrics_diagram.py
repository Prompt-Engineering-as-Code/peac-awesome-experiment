#!/usr/bin/env python3
"""
Create a bar chart diagram showing token reduction from PEaC modularization.
Similar to Figure 4 in the research paper.
"""

import matplotlib.pyplot as plt
import numpy as np
from common import (
    calculate_token_reduction_ratio, 
    calculate_reuse_efficiency, 
    calculate_modularity_index,
    count_tokens,
    get_all_sentences_from_yaml
)
import os

def calculate_actual_token_counts(original_dir, refactored_dir):
    """Calculate the actual token counts for original and refactored versions."""
    
    # Count tokens in original (self-contained) modules
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
    
    # Count tokens in refactored modules (including base modules)
    all_peac_sentences = []
    
    # 1. Get sentences from leaf modules
    refactored_files = [f for f in os.listdir(refactored_dir) if f.endswith('.yaml')]
    for filename in refactored_files:
        yaml_path = os.path.join(refactored_dir, filename)
        try:
            sentences = get_all_sentences_from_yaml(yaml_path)
            all_peac_sentences.extend(sentences)
        except Exception as e:
            print(f"Warning: Could not process refactored file {filename}: {e}")
    
    # 2. Get sentences from base modules (extends directory)
    from common import collect_base_modules_and_sentences
    _, base_sentences, _ = collect_base_modules_and_sentences(refactored_dir)
    for module_path, sentences in base_sentences.items():
        all_peac_sentences.extend(sentences)
    
    total_peac_tokens = count_tokens(' '.join(all_peac_sentences))
    
    return total_orig_tokens, total_peac_tokens

def create_token_reduction_diagram():
    """Create a horizontal bar chart showing token reduction."""
    
    # Directory paths
    original_dir = "peac_modules_single"
    refactored_dir = "refactored_peac_modules"
    
    # Calculate actual token counts
    orig_tokens, refactored_tokens = calculate_actual_token_counts(original_dir, refactored_dir)
    
    # Calculate metrics
    trr = calculate_token_reduction_ratio(original_dir, refactored_dir)
    re = calculate_reuse_efficiency(original_dir, refactored_dir)
    mi = calculate_modularity_index(refactored_dir)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Data for the bars
    categories = ['Refactored', 'Self-contained']
    token_counts = [refactored_tokens, orig_tokens]


    y_pos = np.array([0, 0.2])   # ← distanza ridotta tra le barre

    bars = ax.barh(
        y_pos,
        token_counts,
        height=0.08,
        color='#4472C4'
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)


    
    # Create horizontal bar chart
    # bars = ax.barh(categories, token_counts, color=['#4472C4', '#4472C4'], height=0.3)
    
    # Add token count labels on the bars
    for i, (bar, count) in enumerate(zip(bars, token_counts)):
        ax.text(bar.get_width() + max(token_counts) * 0.01, bar.get_y() + bar.get_height()/2, 
                str(count), ha='left', va='center', fontweight='bold', fontsize=14)
    
    # Customize the plot
    ax.set_xlabel('Token count', fontsize=14)
    # ax.set_title('Advancing PEaC: Formal Specification, Modularity, and Usability', 
    #             fontsize=16, fontweight='bold', pad=20)
    
    # Set x-axis limits with some padding
    ax.set_xlim(0, max(token_counts) * 1.15)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add grid for better readability
    ax.grid(axis='x', alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)

    ax.tick_params(axis='y', labelsize=14)
    ax.tick_params(axis='x', labelsize=12)
    for label in ax.get_yticklabels():
        label.set_fontweight('bold')


    
    # Calculate token reduction
    token_reduction = orig_tokens - refactored_tokens
    
    # Add figure caption
    # caption = f"Figure 4: Token counts before and after PEaC modularization. The reduction represents a savings of {token_reduction:,} tokens."
    # fig.text(0.1, 0.02, caption, fontsize=12, ha='left', style='italic')
    
    # Add metrics summary as text box
#     metrics_text = f"""Metrics Summary:
# Token Reduction Ratio (TRR): {trr:.2f}%
# Reuse Efficiency (RE): {re:.2f}%
# Modularity Index (MI): {mi:.2f}

# Analysis:
# • Modularization achieved {trr:.1f}% token reduction
# • High reuse efficiency ({re:.1f}%) - base modules well utilized
# • Good modular structure (MI = {mi:.2f}) - rich composition"""
    
    # Add text box with metrics
    props = dict(boxstyle='round', facecolor='lightgray', alpha=0.8)
    # ax.text(0.98, 0.98, metrics_text, transform=ax.transAxes, fontsize=10,
    #         verticalalignment='top', horizontalalignment='right', bbox=props)
    
    # Adjust layout to prevent clipping
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    
    return fig, ax

def main():
    """Generate and save the token reduction diagram."""
    
    print("Creating PEaC Token Reduction Diagram...")
    
    # Check if directories exist
    if not os.path.exists("peac_modules_single"):
        print("Error: Directory peac_modules_single not found")
        return
    
    if not os.path.exists("refactored_peac_modules"):
        print("Error: Directory refactored_peac_modules not found")
        return
    
    # Create the diagram
    fig, ax = create_token_reduction_diagram()

    out_dir = "out"
    os.makedirs(out_dir, exist_ok=True)
    
    # Save the figure
    output_file = os.path.join(out_dir, "peac_token_reduction_diagram.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Diagram saved as: {output_file}")
    
    # Also save as PDF for publication quality
    pdf_file = os.path.join(out_dir, "peac_token_reduction_diagram.pdf")
    plt.savefig(pdf_file, bbox_inches='tight', facecolor='white')
    print(f"Diagram also saved as: {pdf_file}")
    
    # Show the plot
    plt.show()

if __name__ == "__main__":
    main()