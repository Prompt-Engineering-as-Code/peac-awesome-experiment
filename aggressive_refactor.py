#!/usr/bin/env python3
"""
Aggressive refactoring script to maximize token reduction.
"""

import os
import yaml
from collections import Counter, defaultdict
from common import get_all_sentences_from_yaml, clean_sentence


def extract_most_common_sentences(original_dir, min_frequency=5):
    """Extract the most common sentences to create focused modules."""
    
    all_sentences = []
    sentence_to_files = defaultdict(set)
    section_sentences = defaultdict(list)
    
    files = [f for f in os.listdir(original_dir) if f.endswith('.yaml')]
    
    for filename in files:
        yaml_path = os.path.join(original_dir, filename)
        try:
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
                                    if len(cleaned) > 20:  # Skip very short sentences
                                        all_sentences.append(sentence)
                                        section_sentences[section].append(sentence)
                                        sentence_to_files[sentence].add(filename)
        except Exception as e:
            print(f"Warning: Could not process {filename}: {e}")
    
    # Find most frequent sentences by section
    frequent_by_section = {}
    for section, sentences in section_sentences.items():
        counter = Counter(sentences)
        frequent = {sent: count for sent, count in counter.items() if count >= min_frequency}
        if frequent:
            frequent_by_section[section] = frequent
    
    return frequent_by_section, sentence_to_files


def create_super_modules(frequent_by_section):
    """Create highly reusable super modules."""
    
    modules_created = []
    
    for section, frequent_sentences in frequent_by_section.items():
        if not frequent_sentences:
            continue
        
        # Group by frequency tiers
        very_common = {s: c for s, c in frequent_sentences.items() if c >= 20}
        common = {s: c for s, c in frequent_sentences.items() if 10 <= c < 20}
        moderate = {s: c for s, c in frequent_sentences.items() if 5 <= c < 10}
        
        # Create super common module
        if very_common:
            module_path = f"extends/{section}/super_common.yaml"
            module_content = {
                'prompt': {
                    section: {
                        'base': list(very_common.keys())
                    }
                }
            }
            
            os.makedirs(os.path.dirname(module_path), exist_ok=True)
            with open(module_path, 'w', encoding='utf-8') as f:
                yaml.dump(module_content, f, default_flow_style=False, allow_unicode=True)
            
            modules_created.append((f"{section}/super_common.yaml", len(very_common), sum(very_common.values())))
        
        # Create common module
        if common:
            module_path = f"extends/{section}/common.yaml"
            module_content = {
                'prompt': {
                    section: {
                        'base': list(common.keys())
                    }
                }
            }
            
            os.makedirs(os.path.dirname(module_path), exist_ok=True)
            with open(module_path, 'w', encoding='utf-8') as f:
                yaml.dump(module_content, f, default_flow_style=False, allow_unicode=True)
            
            modules_created.append((f"{section}/common.yaml", len(common), sum(common.values())))
    
    return modules_created


def aggressively_refactor_files(refactored_dir, frequent_by_section):
    """Aggressively refactor files to use the new super modules."""
    
    files_updated = 0
    total_removals = 0
    
    files = [f for f in os.listdir(refactored_dir) if f.endswith('.yaml')]
    
    for filename in files:
        yaml_path = os.path.join(refactored_dir, filename)
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if 'prompt' not in data:
                continue
            
            changes_made = False
            extends_to_add = set()
            
            # Current extends
            current_extends = data['prompt'].get('extends', [])
            if isinstance(current_extends, str):
                current_extends = [current_extends]
            elif current_extends is None:
                current_extends = []
            
            for section in ['instruction', 'context', 'output']:
                if section not in data['prompt'] or 'base' not in data['prompt'][section]:
                    continue
                
                base_rules = data['prompt'][section]['base']
                if not isinstance(base_rules, list):
                    continue
                
                original_count = len(base_rules)
                
                # Remove sentences that are in super_common
                if section in frequent_by_section:
                    # Very common sentences (20+ occurrences)
                    very_common = {s for s, c in frequent_by_section[section].items() if c >= 20}
                    if very_common:
                        new_base = [s for s in base_rules if s not in very_common]
                        if len(new_base) < len(base_rules):
                            data['prompt'][section]['base'] = new_base
                            extends_to_add.add(f"{section}/super_common.yaml")
                            changes_made = True
                    
                    # Common sentences (10-19 occurrences)
                    common = {s for s, c in frequent_by_section[section].items() if 10 <= c < 20}
                    if common:
                        current_base = data['prompt'][section]['base']
                        new_base = [s for s in current_base if s not in common]
                        if len(new_base) < len(current_base):
                            data['prompt'][section]['base'] = new_base
                            extends_to_add.add(f"{section}/common.yaml")
                            changes_made = True
                
                removed_count = original_count - len(data['prompt'][section]['base'])
                total_removals += removed_count
            
            # Add new extends
            if extends_to_add:
                all_extends = list(set(current_extends) | extends_to_add)
                data['prompt']['extends'] = all_extends
                changes_made = True
            
            if changes_made:
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                files_updated += 1
        
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    return files_updated, total_removals


def main():
    original_dir = "peac_modules_single"
    refactored_dir = "refactored_peac_modules"
    
    print("🚀 AGGRESSIVE REFACTORING FOR MAXIMUM TOKEN REDUCTION")
    print("=" * 60)
    
    # Analyze frequency patterns
    print("1. Analyzing sentence frequencies...")
    frequent_by_section, sentence_to_files = extract_most_common_sentences(original_dir, min_frequency=5)
    
    total_frequent = sum(len(sentences) for sentences in frequent_by_section.values())
    print(f"   Found {total_frequent} frequently repeated sentences")
    
    # Create super modules
    print("2. Creating super-reusable modules...")
    modules_created = create_super_modules(frequent_by_section)
    
    for module, sentence_count, total_occurrences in modules_created:
        print(f"   ✓ {module}: {sentence_count} sentences, {total_occurrences} total occurrences")
    
    # Aggressively refactor
    print("3. Aggressively refactoring files...")
    files_updated, total_removals = aggressively_refactor_files(refactored_dir, frequent_by_section)
    
    print(f"   ✓ Updated {files_updated} files")
    print(f"   ✓ Removed {total_removals} duplicate sentences")
    
    # Test final metrics
    print("4. Computing final metrics...")
    from common import calculate_token_reduction_ratio, calculate_reuse_efficiency, calculate_modularity_index
    
    trr = calculate_token_reduction_ratio(original_dir, refactored_dir)
    re = calculate_reuse_efficiency(original_dir, refactored_dir)
    mi = calculate_modularity_index(refactored_dir)
    
    print(f"\n🎯 FINAL OPTIMIZED METRICS:")
    print("=" * 40)
    print(f"Token Reduction Ratio (TRR):   {trr:.2f}%")
    print(f"Reuse Efficiency (RE):         {re:.2f}%")
    print(f"Modularity Index (MI):         {mi:.2f}")
    
    print(f"\n📊 IMPROVEMENT SUMMARY:")
    print(f"Files with super-modules: {len(modules_created)}")
    print(f"Total sentence removals: {total_removals}")
    print(f"Estimated token savings: ~{total_removals * 15} tokens")  # Rough estimate


if __name__ == "__main__":
    main()