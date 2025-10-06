#!/usr/bin/env python3
"""
Script to improve refactoring by applying common modules to reduce duplications.
"""

import os
import yaml
from collections import defaultdict
from common import get_all_sentences_from_yaml, clean_sentence


# Define common patterns and their corresponding modules
COMMON_PATTERNS = {
    # Instruction patterns
    "Avoid unsafe, private, or unverifiable claims.": "instruction/common_professional.yaml",
    "Maintain a professional, helpful tone.": "instruction/common_professional.yaml", 
    "Infer any missing details sensibly from common scenarios in this domain.": "instruction/common_professional.yaml",
    "Keep explanations compact and practical.": "instruction/common_professional.yaml",
    "Draw on relevant background knowledge the user might expect (e.g., prior examples, local notes, or public references) to ground the response.": "instruction/common_professional.yaml",
    "Include brief examples or snippets when they help the user act immediately.": "instruction/common_professional.yaml",
    "Finish with a lightweight next step or prompt the user could follow to continue.": "instruction/common_professional.yaml",
    
    # Context patterns  
    "Draw on relevant background knowledge the user might expect (e.g., prior examples, local notes, or public references) to ground the response.": "context/professional_grounding.yaml",
    "Maintain a professional, helpful tone; avoid unsafe, private, or unverifiable claims.": "context/professional_grounding.yaml",
    
    # Output patterns
    "Finish with a lightweight next step or prompt the user could follow to continue.": "output/actionable_conclusion.yaml",
    "Include brief examples or snippets when they help the user act immediately.": "output/actionable_conclusion.yaml",
    "Maintain a professional, helpful tone.": "output/actionable_conclusion.yaml",
    
    # Formatting patterns
    "Shape the result so it feels ready-to-use: organize ideas cleanly in Markdown with readable sections, short paragraphs, and bullet points where that improves clarity.": "format/structured_output.yaml",
    "Organize the response in Markdown with clear sections.": "markdown/clarity.yaml",
    "Use short paragraphs and bullet points where they improve clarity.": "markdown/clarity.yaml",
}


def normalize_sentence(sentence):
    """Normalize sentence for matching."""
    if not sentence:
        return ""
    return sentence.strip().rstrip('.')


def should_add_module(sentences, module_sentences, threshold=0.3):
    """Check if enough sentences match to justify adding a module."""
    if not sentences or not module_sentences:
        return False
    
    matches = 0
    normalized_sentences = [normalize_sentence(s) for s in sentences]
    
    for module_sentence in module_sentences:
        normalized_module = normalize_sentence(module_sentence)
        for sentence in normalized_sentences:
            if normalized_module in sentence or sentence in normalized_module:
                matches += 1
                break
    
    return matches / len(module_sentences) >= threshold


def get_module_sentences(module_path):
    """Get sentences from a module file."""
    full_path = os.path.join("extends", module_path)
    if os.path.exists(full_path):
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            sentences = []
            if 'prompt' in data:
                for section in ['instruction', 'context', 'output']:
                    if section in data['prompt'] and 'base' in data['prompt'][section]:
                        base_rules = data['prompt'][section]['base']
                        if isinstance(base_rules, list):
                            sentences.extend(base_rules)
                        elif isinstance(base_rules, str):
                            sentences.append(base_rules)
            return sentences
        except Exception as e:
            print(f"Warning: Could not read module {module_path}: {e}")
    return []


def improve_file_refactoring(yaml_path):
    """Improve refactoring of a single file by adding appropriate modules."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if 'prompt' not in data:
            return False
        
        changes_made = False
        modules_to_add = set()
        
        # Get current extends
        current_extends = data['prompt'].get('extends', [])
        if isinstance(current_extends, str):
            current_extends = [current_extends]
        elif current_extends is None:
            current_extends = []
        
        # Analyze each section
        for section in ['instruction', 'context', 'output']:
            if section in data['prompt'] and 'base' in data['prompt'][section]:
                base_rules = data['prompt'][section]['base']
                if not isinstance(base_rules, list):
                    continue
                
                # Check which modules could apply to this section
                section_modules = defaultdict(list)
                
                for sentence in base_rules[:]:  # Copy to allow modification
                    normalized = normalize_sentence(sentence)
                    
                    # Find matching modules
                    for pattern, module in COMMON_PATTERNS.items():
                        if module.startswith(f"{section}/") and normalize_sentence(pattern) in normalized:
                            section_modules[module].append(sentence)
                
                # Add modules that have enough matches
                for module, matching_sentences in section_modules.items():
                    if module not in current_extends:
                        module_sentences = get_module_sentences(module)
                        if should_add_module(base_rules, module_sentences, threshold=0.4):
                            modules_to_add.add(module)
                            
                            # Remove matching sentences from base
                            for sentence in matching_sentences:
                                if sentence in base_rules:
                                    base_rules.remove(sentence)
                                    changes_made = True
        
        # Add universal modules if many common patterns found
        all_sentences = []
        for section in ['instruction', 'context', 'output']:
            if section in data['prompt'] and 'base' in data['prompt'][section]:
                base_rules = data['prompt'][section]['base']
                if isinstance(base_rules, list):
                    all_sentences.extend(base_rules)
        
        # Check for markdown formatting patterns
        markdown_patterns = [s for s in all_sentences if 'markdown' in s.lower() or 'bullet point' in s.lower()]
        if markdown_patterns and 'markdown/clarity.yaml' not in current_extends:
            modules_to_add.add('markdown/clarity.yaml')
            # Remove markdown-related sentences
            for section in ['instruction', 'context', 'output']:
                if section in data['prompt'] and 'base' in data['prompt'][section]:
                    base_rules = data['prompt'][section]['base']
                    if isinstance(base_rules, list):
                        data['prompt'][section]['base'] = [s for s in base_rules 
                                                          if 'bullet point' not in s.lower() and 
                                                             'short paragraphs' not in s.lower()]
            changes_made = True
        
        # Update extends if we have new modules
        if modules_to_add:
            all_extends = list(set(current_extends + list(modules_to_add)))
            data['prompt']['extends'] = all_extends
            changes_made = True
        
        # Save if changes were made
        if changes_made:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            return True
            
    except Exception as e:
        print(f"Error processing {yaml_path}: {e}")
        return False
    
    return False


def main():
    refactored_dir = "refactored_peac_modules"
    
    if not os.path.exists(refactored_dir):
        print(f"Error: Directory {refactored_dir} not found")
        return
    
    print("🚀 IMPROVING REFACTORING WITH COMMON MODULES")
    print("=" * 50)
    
    files_processed = 0
    files_changed = 0
    
    files = [f for f in os.listdir(refactored_dir) if f.endswith('.yaml')]
    
    for filename in files:
        yaml_path = os.path.join(refactored_dir, filename)
        
        try:
            changed = improve_file_refactoring(yaml_path)
            files_processed += 1
            if changed:
                files_changed += 1
                print(f"✓ Updated {filename}")
        except Exception as e:
            print(f"✗ Error with {filename}: {e}")
    
    print(f"\n📊 REFACTORING IMPROVEMENT COMPLETE")
    print(f"Files processed: {files_processed}")
    print(f"Files updated: {files_changed}")
    print(f"Improvement rate: {(files_changed/files_processed*100):.1f}%")
    
    print("\n🧪 Testing new metrics...")
    
    # Test new metrics
    from common import calculate_token_reduction_ratio, calculate_reuse_efficiency, calculate_modularity_index
    
    original_dir = "peac_modules_single"
    
    trr = calculate_token_reduction_ratio(original_dir, refactored_dir)
    re = calculate_reuse_efficiency(original_dir, refactored_dir)
    mi = calculate_modularity_index(refactored_dir)
    
    print(f"\n📈 NEW METRICS:")
    print(f"Token Reduction Ratio (TRR):   {trr:.2f}%")
    print(f"Reuse Efficiency (RE):         {re:.2f}%")
    print(f"Modularity Index (MI):         {mi:.2f}")


if __name__ == "__main__":
    main()