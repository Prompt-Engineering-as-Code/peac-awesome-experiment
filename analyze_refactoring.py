#!/usr/bin/env python3
"""
Analyzer script to identify duplicate sentences and improve refactoring opportunities.
"""

import os
from collections import Counter, defaultdict
from common import get_all_sentences_from_yaml, clean_sentence


def analyze_duplications(original_dir: str):
    """Analyze all sentences across original files to find duplicates."""
    
    all_sentences = []
    sentence_files = defaultdict(list)  # Track which files contain each sentence
    section_sentences = defaultdict(list)  # Track sentences by section
    
    files = [f for f in os.listdir(original_dir) if f.endswith('.yaml')]
    
    print(f"Analyzing {len(files)} files in {original_dir}...")
    
    for filename in files:
        yaml_path = os.path.join(original_dir, filename)
        try:
            sentences = get_all_sentences_from_yaml(yaml_path)
            
            # Also get sentences by section
            import yaml
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if 'prompt' in data:
                prompt = data['prompt']
                for section in ['instruction', 'context', 'output']:
                    if section in prompt and 'base' in prompt[section]:
                        base_rules = prompt[section]['base']
                        if isinstance(base_rules, list):
                            for sentence in base_rules:
                                if sentence and sentence.strip():
                                    cleaned = clean_sentence(sentence)
                                    section_sentences[section].append(sentence)
                                    sentence_files[cleaned].append(f"{filename}:{section}")
                        elif isinstance(base_rules, str) and base_rules.strip():
                            cleaned = clean_sentence(base_rules)
                            section_sentences[section].append(base_rules)
                            sentence_files[cleaned].append(f"{filename}:{section}")
            
            for sentence in sentences:
                if sentence and sentence.strip():
                    all_sentences.append(sentence)
                    cleaned = clean_sentence(sentence)
                    if cleaned not in sentence_files:  # Avoid double counting from section analysis
                        sentence_files[cleaned].append(filename)
                        
        except Exception as e:
            print(f"Warning: Could not process {filename}: {e}")
    
    return all_sentences, sentence_files, section_sentences


def find_common_patterns(sentences, min_frequency=3):
    """Find sentences that appear in multiple files."""
    
    # Clean sentences and count frequency
    cleaned_sentences = [clean_sentence(s) for s in sentences if s and s.strip()]
    sentence_counts = Counter(cleaned_sentences)
    
    # Find sentences that appear multiple times
    common_patterns = {sentence: count for sentence, count in sentence_counts.items() 
                      if count >= min_frequency and len(sentence) > 10}  # Skip very short sentences
    
    return common_patterns


def suggest_new_modules(sentence_files, section_sentences, min_reuse=3):
    """Suggest new base modules based on sentence frequency."""
    
    suggestions = []
    
    # Analyze by section
    for section, sentences in section_sentences.items():
        cleaned_sentences = [clean_sentence(s) for s in sentences if s and s.strip()]
        sentence_counts = Counter(cleaned_sentences)
        
        common_in_section = {sentence: count for sentence, count in sentence_counts.items() 
                           if count >= min_reuse and len(sentence) > 15}
        
        if common_in_section:
            suggestions.append({
                'section': section,
                'type': f'common_{section}_rules',
                'sentences': common_in_section,
                'suggested_module': f"{section}/common_rules.yaml"
            })
    
    # Find cross-section patterns
    all_cleaned = defaultdict(int)
    original_sentences = {}
    
    for section, sentences in section_sentences.items():
        for sentence in sentences:
            if sentence and sentence.strip():
                cleaned = clean_sentence(sentence)
                all_cleaned[cleaned] += 1
                if cleaned not in original_sentences:
                    original_sentences[cleaned] = sentence
    
    cross_section_common = {cleaned: count for cleaned, count in all_cleaned.items() 
                           if count >= min_reuse and len(cleaned) > 15}
    
    if cross_section_common:
        suggestions.append({
            'section': 'cross-section',
            'type': 'universal_rules',
            'sentences': cross_section_common,
            'suggested_module': "universal/common_rules.yaml"
        })
    
    return suggestions, original_sentences


def main():
    original_dir = "peac_modules_single"
    
    if not os.path.exists(original_dir):
        print(f"Error: Directory {original_dir} not found")
        return
    
    print("🔍 ANALYZING REFACTORING OPPORTUNITIES")
    print("=" * 50)
    
    # Analyze duplications
    all_sentences, sentence_files, section_sentences = analyze_duplications(original_dir)
    
    print(f"\n📊 BASIC STATISTICS:")
    print(f"Total sentences found: {len(all_sentences)}")
    print(f"Unique sentences: {len(set(clean_sentence(s) for s in all_sentences))}")
    print(f"Potential duplication: {len(all_sentences) - len(set(clean_sentence(s) for s in all_sentences))} sentences")
    
    # Find common patterns
    common_patterns = find_common_patterns(all_sentences, min_frequency=3)
    
    print(f"\n🎯 MOST FREQUENT DUPLICATE SENTENCES:")
    print("-" * 40)
    for sentence, count in sorted(common_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"[{count}x] {sentence[:80]}{'...' if len(sentence) > 80 else ''}")
        # Show which files use this sentence
        files_using = sentence_files.get(sentence, [])
        if files_using:
            print(f"     Used in: {', '.join(files_using[:5])}{'...' if len(files_using) > 5 else ''}")
        print()
    
    # Suggest new modules
    suggestions, original_sentences = suggest_new_modules(sentence_files, section_sentences, min_reuse=3)
    
    print(f"\n💡 REFACTORING SUGGESTIONS:")
    print("-" * 40)
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. Create module: {suggestion['suggested_module']}")
        print(f"   Type: {suggestion['type']} ({suggestion['section']} section)")
        print(f"   Contains {len(suggestion['sentences'])} common sentences")
        
        # Show top sentences for this module
        top_sentences = sorted(suggestion['sentences'].items(), key=lambda x: x[1], reverse=True)[:3]
        for sentence, count in top_sentences:
            original = original_sentences.get(sentence, sentence)
            print(f"   [{count}x] {original[:60]}{'...' if len(original) > 60 else ''}")
        print()
    
    print(f"\n📈 POTENTIAL IMPROVEMENTS:")
    total_duplicates = sum(count - 1 for count in common_patterns.values())
    print(f"Estimated additional token reduction: ~{total_duplicates} duplicate sentences could be modularized")
    print(f"This could potentially improve TRR from current ~4.6% to ~{4.6 + (total_duplicates / len(all_sentences)) * 100:.1f}%")


if __name__ == "__main__":
    main()