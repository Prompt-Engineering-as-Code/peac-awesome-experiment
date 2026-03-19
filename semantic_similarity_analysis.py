#!/usr/bin/env python3
"""
Semantic Similarity Analysis between Self-Contained and Refactored PEaC Modules

This script addresses the reviewer's concern: "The authors do not present any 
experiment or discussion addressing whether prompts generated with PEaC maintain 
comparable performance to non-modular PEaC files."

We measure semantic similarity to demonstrate that despite token reduction through
modularization, the semantic content and intent of prompts is preserved.
"""

import os
import yaml
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from common import get_all_sentences_from_yaml, count_tokens
from peac import PromptYaml

# Metrics we'll compute
METRICS = {
    'cosine': 'Cosine Similarity (TF-IDF)',
    'bleu': 'BLEU Score',
    'bert': 'BERTScore',
    'rouge': 'ROUGE-L'
}

OUT_DIR = "out"


def resolve_extends_manually(yaml_path: str, extends_dir: str, visited=None) -> List[str]:
    """
    Manually resolve and collect all sentences from a YAML and its extends.
    This is a custom implementation that properly handles the extends resolution.
    """
    if visited is None:
        visited = set()
    
    if yaml_path in visited:
        return []
    visited.add(yaml_path)
    
    all_sentences = []
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if 'prompt' not in data:
            return []
        
        prompt = data['prompt']
        
        # First, recursively process extends
        if 'extends' in prompt:
            extends_list = prompt['extends']
            if not isinstance(extends_list, list):
                extends_list = [extends_list]
            
            for extend_path in extends_list:
                # Resolve extend_path relative to extends_dir
                full_extend_path = os.path.join(extends_dir, extend_path)
                if os.path.exists(full_extend_path):
                    extend_sentences = resolve_extends_manually(full_extend_path, extends_dir, visited)
                    all_sentences.extend(extend_sentences)
        
        # Then add sentences from this file
        for section in ['instruction', 'context', 'output']:
            if section in prompt and 'base' in prompt[section]:
                base_rules = prompt[section]['base']
                if isinstance(base_rules, list):
                    all_sentences.extend(base_rules)
                elif isinstance(base_rules, str):
                    all_sentences.append(base_rules)
        
        # Add query if present
        if 'query' in prompt:
            if isinstance(prompt['query'], str):
                all_sentences.append(prompt['query'])
        
    except Exception as e:
        print(f"Warning: Could not process {yaml_path}: {e}")
    
    return [s for s in all_sentences if s and s.strip()]


def get_full_rendered_prompt(yaml_path: str, workspace_root: str) -> str:
    """
    Get the fully rendered prompt from a YAML file, resolving all extends.
    This gives us what the LLM would actually see.
    
    For refactored modules, we manually resolve extends.
    For self-contained modules, we use the PromptYaml class.
    """
    try:
        # Check if this is a refactored module
        is_refactored = 'refactored_peac_modules' in yaml_path
        
        if is_refactored:
            # For refactored modules, manually resolve extends
            extends_dir = os.path.join(workspace_root, 'extends')
            sentences = resolve_extends_manually(yaml_path, extends_dir)
            return ' '.join(sentences)
        else:
            # For self-contained modules, use PromptYaml
            py = PromptYaml(yaml_path)
            return py.get_prompt_sentence()
        
    except Exception as e:
        print(f"Warning: Could not render {yaml_path}: {e}")
        return ""


def compute_cosine_similarity(text1: str, text2: str) -> float:
    """Compute cosine similarity using TF-IDF vectors."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    if not text1 or not text2:
        return 0.0
    
    try:
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return similarity
    except Exception as e:
        print(f"Warning: Could not compute cosine similarity: {e}")
        return 0.0


def compute_bleu_score(reference: str, candidate: str) -> float:
    """Compute BLEU score between two texts."""
    try:
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        import nltk
        
        # Download necessary NLTK data if not available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        # Tokenize
        reference_tokens = [reference.lower().split()]
        candidate_tokens = candidate.lower().split()
        
        # Use smoothing for better results with short texts
        smooth = SmoothingFunction().method1
        score = sentence_bleu(reference_tokens, candidate_tokens, 
                            smoothing_function=smooth)
        return score
    except Exception as e:
        print(f"Warning: Could not compute BLEU score: {e}")
        return 0.0


def compute_bertscore(reference: str, candidate: str) -> Dict[str, float]:
    """Compute BERTScore between two texts."""
    try:
        from bert_score import score as bert_score
        
        if not reference or not candidate:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
        
        P, R, F1 = bert_score([candidate], [reference], lang='en', 
                             verbose=False, device='cpu')
        
        return {
            'precision': P.item(),
            'recall': R.item(),
            'f1': F1.item()
        }
    except ImportError:
        print("Warning: bert-score not installed. Install with: pip install bert-score")
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
    except Exception as e:
        print(f"Warning: Could not compute BERTScore: {e}")
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}


def compute_rouge_score(reference: str, candidate: str) -> Dict[str, float]:
    """Compute ROUGE scores between two texts."""
    try:
        from rouge_score import rouge_scorer
        
        if not reference or not candidate:
            return {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0}
        
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], 
                                         use_stemmer=True)
        scores = scorer.score(reference, candidate)
        
        return {
            'rouge1': scores['rouge1'].fmeasure,
            'rouge2': scores['rouge2'].fmeasure,
            'rougeL': scores['rougeL'].fmeasure
        }
    except ImportError:
        print("Warning: rouge-score not installed. Install with: pip install rouge-score")
        return {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0}
    except Exception as e:
        print(f"Warning: Could not compute ROUGE score: {e}")
        return {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0}


def analyze_file_pair(original_path: str, refactored_path: str, 
                     workspace_root: str) -> Dict:
    """Analyze a pair of original and refactored files."""
    
    filename = os.path.basename(original_path)
    
    # Get the fully rendered prompts (what LLM would see)
    original_text = get_full_rendered_prompt(original_path, workspace_root)
    refactored_text = get_full_rendered_prompt(refactored_path, workspace_root)
    
    # Count tokens
    original_tokens = count_tokens(original_text)
    refactored_tokens = count_tokens(refactored_text)
    token_reduction = ((original_tokens - refactored_tokens) / original_tokens * 100 
                      if original_tokens > 0 else 0)
    
    # Compute similarity metrics
    cosine_sim = compute_cosine_similarity(original_text, refactored_text)
    bleu = compute_bleu_score(original_text, refactored_text)
    bert_scores = compute_bertscore(original_text, refactored_text)
    rouge_scores = compute_rouge_score(original_text, refactored_text)
    
    return {
        'filename': filename,
        'original_tokens': original_tokens,
        'refactored_tokens': refactored_tokens,
        'token_reduction_pct': token_reduction,
        'cosine_similarity': cosine_sim,
        'bleu_score': bleu,
        'bertscore_f1': bert_scores['f1'],
        'bertscore_precision': bert_scores['precision'],
        'bertscore_recall': bert_scores['recall'],
        'rouge1_f1': rouge_scores['rouge1'],
        'rouge2_f1': rouge_scores['rouge2'],
        'rougeL_f1': rouge_scores['rougeL']
    }


def run_semantic_similarity_analysis(original_dir: str = "peac_modules_single",
                                    refactored_dir: str = "refactored_peac_modules",
                                    sample_size: int = None) -> pd.DataFrame:
    """
    Run comprehensive semantic similarity analysis.
    
    Args:
        original_dir: Directory with self-contained modules
        refactored_dir: Directory with refactored modular modules
        sample_size: If specified, randomly sample this many files (for quick testing)
    
    Returns:
        DataFrame with results for each file pair
    """
    
    print("=" * 80)
    print("SEMANTIC SIMILARITY ANALYSIS: PEaC Modularization")
    print("=" * 80)
    print()
    print("Comparing self-contained modules vs. refactored modular modules")
    print("to verify that semantic content is preserved despite token reduction.")
    print()
    
    # Get matching files
    original_files = [f for f in os.listdir(original_dir) if f.endswith('.yaml')]
    refactored_files = [f for f in os.listdir(refactored_dir) if f.endswith('.yaml')]
    
    # Find common files
    common_files = sorted(set(original_files) & set(refactored_files))
    
    if sample_size and sample_size < len(common_files):
        import random
        common_files = random.sample(common_files, sample_size)
        print(f"Analyzing random sample of {sample_size} files...")
    else:
        print(f"Analyzing all {len(common_files)} file pairs...")
    
    print()
    
    # Get workspace root (current directory)
    workspace_root = os.getcwd()
    
    # Analyze each pair
    results = []
    for i, filename in enumerate(common_files, 1):
        print(f"[{i}/{len(common_files)}] Processing {filename}...", end=' ')
        
        original_path = os.path.join(original_dir, filename)
        refactored_path = os.path.join(refactored_dir, filename)
        
        result = analyze_file_pair(original_path, refactored_path, workspace_root)
        results.append(result)
        
        print(f"✓ (Cosine: {result['cosine_similarity']:.3f}, "
              f"BLEU: {result['bleu_score']:.3f}, "
              f"Token reduction: {result['token_reduction_pct']:.1f}%)")
    
    print()
    print("=" * 80)
    
    return pd.DataFrame(results)


def print_summary_statistics(df: pd.DataFrame):
    """Print summary statistics of the analysis."""
    
    print()
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    
    # Token statistics
    print("TOKEN COUNTS:")
    print(f"  Original (mean):     {df['original_tokens'].mean():.1f} ± {df['original_tokens'].std():.1f}")
    print(f"  Refactored (mean):   {df['refactored_tokens'].mean():.1f} ± {df['refactored_tokens'].std():.1f}")
    print(f"  Reduction (mean):    {df['token_reduction_pct'].mean():.2f}% ± {df['token_reduction_pct'].std():.2f}%")
    print()
    
    # Semantic similarity metrics
    print("SEMANTIC SIMILARITY METRICS:")
    print(f"  Cosine Similarity:   {df['cosine_similarity'].mean():.4f} ± {df['cosine_similarity'].std():.4f}")
    print(f"  BLEU Score:          {df['bleu_score'].mean():.4f} ± {df['bleu_score'].std():.4f}")
    
    if df['bertscore_f1'].mean() > 0:
        print(f"  BERTScore F1:        {df['bertscore_f1'].mean():.4f} ± {df['bertscore_f1'].std():.4f}")
        print(f"  BERTScore Precision: {df['bertscore_precision'].mean():.4f} ± {df['bertscore_precision'].std():.4f}")
        print(f"  BERTScore Recall:    {df['bertscore_recall'].mean():.4f} ± {df['bertscore_recall'].std():.4f}")
    
    if df['rougeL_f1'].mean() > 0:
        print(f"  ROUGE-1 F1:          {df['rouge1_f1'].mean():.4f} ± {df['rouge1_f1'].std():.4f}")
        print(f"  ROUGE-2 F1:          {df['rouge2_f1'].mean():.4f} ± {df['rouge2_f1'].std():.4f}")
        print(f"  ROUGE-L F1:          {df['rougeL_f1'].mean():.4f} ± {df['rougeL_f1'].std():.4f}")
    
    print()
    
    # Interpretation
    print("INTERPRETATION:")
    avg_cosine = df['cosine_similarity'].mean()
    avg_bleu = df['bleu_score'].mean()
    avg_token_reduction = df['token_reduction_pct'].mean()
    
    if avg_cosine > 0.8:
        cosine_interp = "EXCELLENT - Very high semantic similarity"
    elif avg_cosine > 0.6:
        cosine_interp = "GOOD - Strong semantic similarity"
    elif avg_cosine > 0.4:
        cosine_interp = "MODERATE - Acceptable semantic similarity"
    else:
        cosine_interp = "LOW - Weak semantic similarity"
    
    if avg_bleu > 0.5:
        bleu_interp = "EXCELLENT - Very high lexical overlap"
    elif avg_bleu > 0.3:
        bleu_interp = "GOOD - Strong lexical overlap"
    elif avg_bleu > 0.15:
        bleu_interp = "MODERATE - Acceptable lexical overlap"
    else:
        bleu_interp = "LOW - Weak lexical overlap"
    
    print(f"  • Cosine Similarity ({avg_cosine:.3f}): {cosine_interp}")
    print(f"  • BLEU Score ({avg_bleu:.3f}): {bleu_interp}")
    print(f"  • Token Reduction ({avg_token_reduction:.1f}%): ", end='')
    
    if avg_token_reduction > 20:
        print("Significant efficiency gain")
    elif avg_token_reduction > 10:
        print("Moderate efficiency gain")
    else:
        print("Modest efficiency gain")
    
    print()
    print("CONCLUSION:")
    if avg_cosine > 0.6 and avg_token_reduction > 10:
        print("  ✓ PEaC modularization achieves substantial token reduction while")
        print("    maintaining high semantic similarity. The refactored modules")
        print("    preserve the semantic content and intent of the original prompts.")
    elif avg_cosine > 0.4:
        print("  ⚠ Modularization achieves token reduction with moderate semantic")
        print("    similarity. Some semantic drift may occur but is acceptable.")
    else:
        print("  ✗ Significant semantic drift detected. Manual review recommended.")
    
    print()
    print("=" * 80)


def create_similarity_visualization(df: pd.DataFrame, output_file: str = os.path.join(OUT_DIR, "semantic_similarity_plot.png")):
    """Create visualization of semantic similarity results."""
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Scatter: Token Reduction vs Cosine Similarity
    ax1 = axes[0, 0]
    ax1.scatter(df['token_reduction_pct'], df['cosine_similarity'], 
               alpha=0.6, s=50)
    ax1.set_xlabel('Token Reduction (%)')
    ax1.set_ylabel('Cosine Similarity')
    ax1.set_title('Token Reduction vs Semantic Similarity')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0.8, color='g', linestyle='--', alpha=0.5, label='High similarity')
    ax1.axhline(y=0.6, color='orange', linestyle='--', alpha=0.5, label='Good similarity')
    ax1.legend()
    
    # 2. Distribution of Cosine Similarity
    ax2 = axes[0, 1]
    ax2.hist(df['cosine_similarity'], bins=20, color='skyblue', edgecolor='black')
    ax2.set_xlabel('Cosine Similarity')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution of Cosine Similarity')
    ax2.axvline(x=df['cosine_similarity'].mean(), color='red', 
               linestyle='--', label=f'Mean: {df["cosine_similarity"].mean():.3f}')
    ax2.legend()
    
    # 3. Distribution of BLEU Scores
    ax3 = axes[1, 0]
    ax3.hist(df['bleu_score'], bins=20, color='lightgreen', edgecolor='black')
    ax3.set_xlabel('BLEU Score')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Distribution of BLEU Scores')
    ax3.axvline(x=df['bleu_score'].mean(), color='red', 
               linestyle='--', label=f'Mean: {df["bleu_score"].mean():.3f}')
    ax3.legend()
    
    # 4. Token Reduction Distribution
    ax4 = axes[1, 1]
    ax4.hist(df['token_reduction_pct'], bins=20, color='coral', edgecolor='black')
    ax4.set_xlabel('Token Reduction (%)')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Distribution of Token Reduction')
    ax4.axvline(x=df['token_reduction_pct'].mean(), color='red', 
               linestyle='--', label=f'Mean: {df["token_reduction_pct"].mean():.1f}%')
    ax4.legend()
    
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved to: {output_file}")
    
    return fig


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Semantic similarity analysis between self-contained and refactored PEaC modules'
    )
    parser.add_argument('--sample', type=int, default=None,
                       help='Analyze a random sample of N files (for quick testing)')
    parser.add_argument('--output', type=str, default=os.path.join(OUT_DIR, 'semantic_similarity_results.csv'),
                       help='Output CSV file for results')
    
    args = parser.parse_args()
    
    # Check dependencies
    print("Checking dependencies...")
    required_packages = []
    
    try:
        import sklearn
    except ImportError:
        required_packages.append('scikit-learn')
    
    try:
        import nltk
    except ImportError:
        required_packages.append('nltk')
    
    if required_packages:
        print(f"\nRequired packages missing: {', '.join(required_packages)}")
        print("Install with:")
        print(f"  pip install {' '.join(required_packages)}")
        return
    
    # Run analysis
    df = run_semantic_similarity_analysis(sample_size=args.sample)
    
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    # Save results
    df.to_csv(args.output, index=False)
    print(f"\nResults saved to: {args.output}")
    
    # Print summary
    print_summary_statistics(df)
    
    # Create visualization
    try:
        import matplotlib
        create_similarity_visualization(df)
    except ImportError:
        print("\nNote: Install matplotlib to generate visualizations:")
        print("  pip install matplotlib")
    
    # Show top 10 most similar and least similar
    print("\nTOP 10 MOST SIMILAR FILES (highest cosine similarity):")
    top10 = df.nlargest(10, 'cosine_similarity')[['filename', 'cosine_similarity', 
                                                   'bleu_score', 'token_reduction_pct']]
    for idx, row in top10.iterrows():
        print(f"  • {row['filename']:50s} "
              f"Cosine: {row['cosine_similarity']:.3f}, "
              f"BLEU: {row['bleu_score']:.3f}, "
              f"Token reduction: {row['token_reduction_pct']:.1f}%")
    
    print("\nTOP 10 LEAST SIMILAR FILES (lowest cosine similarity):")
    bottom10 = df.nsmallest(10, 'cosine_similarity')[['filename', 'cosine_similarity', 
                                                       'bleu_score', 'token_reduction_pct']]
    for idx, row in bottom10.iterrows():
        print(f"  • {row['filename']:50s} "
              f"Cosine: {row['cosine_similarity']:.3f}, "
              f"BLEU: {row['bleu_score']:.3f}, "
              f"Token reduction: {row['token_reduction_pct']:.1f}%")


if __name__ == "__main__":
    main()
