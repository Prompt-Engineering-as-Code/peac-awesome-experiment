import pandas as pd
import os
from typing import TypedDict
from typing import List
import re
import yaml

from peac import PromptYaml

REFACTORED_PEAC_MODULES_DIR = 'refactored_peac_modules'





def open_sentences():
    sentences =  pd.read_csv('clustered_sentences.csv', sep=';')
    return sentences[sentences['cluster_id'].notna()]

def split_extend(text, sep=','):
    return [part.strip() for part in text.split(sep)]

def check_existence(extend_path):
    return os.path.exists(os.path.join('extends', extend_path))
    

class Row(TypedDict):
    cluster_id: int
    file: str
    section: str
    sentence: str
    extends: List[str]


def parse_row(row) -> Row:
    extends = split_extend(row['extend_section']) if pd.notna(row['extend_section']) else []
    for extend in extends:
        if not check_existence(extend):
            raise ValueError(f"Extend file {extend} does not exist.")
    return Row(
        cluster_id = int(row['cluster_id']),
        file = row['file'],
        section = row['section'],
        sentence = row['sentence'],
        extends = extends
    )


def encode_sections(sections):
    return sections
    # return [section.encode('utf-8') for section in sections]

def get_on_section_type(py, section):
    if section == 'instruction':
        return encode_sections(py.get_instruction_base_rules())
    elif section == 'input':
        return encode_sections(py.get_input_base_rules())
    elif section == 'output':
        return encode_sections(py.get_output_base_rules())
    elif section == 'context':
        return encode_sections(py.get_context_base_rules())
    elif section == 'query':
        return encode_sections([py.get_query()])
    else:
        raise ValueError(f"Unknown section type: {section}")

def replace_non_alpha(text: str) -> str:
    """
    Replace all non-alphabetic characters in a string with underscores.
    Keeps only A-Z and a-z.
    """
    return re.sub(r'[^A-Za-z]', '_', text)


def clean_sentence(sentence, strip_to_ascii: bool = False):
    if sentence is bytes:
        sentence = sentence.decode('utf-8', 'ignore')
    return replace_non_alpha(sentence).replace('_','')



def check_sentence_in_section(sentence, list_sentences):
    return clean_sentence(sentence) in [clean_sentence(s) for s in list_sentences]

def get_sentence_index(sentence, list_sentences):
    cleaned_sentence = clean_sentence(sentence)
    for i, s in enumerate(list_sentences):
        if clean_sentence(s) == cleaned_sentence:
            return i
    return -1

def remove_sentence_from_section(sentence, list_sentences):
    cleaned_sentence = clean_sentence(sentence)
    return [s for s in list_sentences if clean_sentence(s) != cleaned_sentence]


def replace_section(py, section, new_list):
    py.parsed_data['prompt'][section]['base'] = new_list

def remove_query_section(py):
    if 'query' in py.parsed_data['prompt']:
        del py.parsed_data['prompt']['query']
def add_extends(py, extends):
    py.parsed_data['prompt']['extends'] = extends



def save_yaml(py, path):
    os.makedirs(REFACTORED_PEAC_MODULES_DIR, exist_ok=True)
    yaml_filename = os.path.basename(path)
    new_yaml_path = os.path.join(REFACTORED_PEAC_MODULES_DIR, yaml_filename)
    # print(path)
    with open(new_yaml_path, 'w') as f:
        yaml.dump(py.parsed_data, f)


# Metrics calculation functions
import tiktoken
from collections import defaultdict


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")  # fallback
    return len(encoding.encode(text))


def get_all_sentences_from_yaml(yaml_path: str) -> list:
    """Extract all sentences from a YAML file as a list."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        sentences = []
        if 'prompt' in data:
            prompt = data['prompt']
            for section in ['instruction', 'context', 'output']:
                if section in prompt and 'base' in prompt[section]:
                    base_rules = prompt[section]['base']
                    if isinstance(base_rules, list):
                        sentences.extend(base_rules)
                    elif isinstance(base_rules, str):
                        sentences.append(base_rules)
            
            # Add query if present
            if 'query' in prompt:
                if isinstance(prompt['query'], str):
                    sentences.append(prompt['query'])
        
        return [s for s in sentences if s and s.strip()]
    except Exception as e:
        print(f"Warning: Could not parse {yaml_path}: {e}")
        return []


def get_yaml_text_content(yaml_path: str) -> str:
    """Extract all text content from a YAML file for token counting."""
    sentences = get_all_sentences_from_yaml(yaml_path)
    return ' '.join(sentences)


def collect_base_modules_and_sentences(refactored_dir: str) -> tuple:
    """Collect all base modules, their sentences, and count their reuse."""
    base_modules = {}
    base_sentences = {}
    reuse_count = defaultdict(int)
    
    # Find all extends files (base modules)
    extends_dir = os.path.join(os.path.dirname(refactored_dir), 'extends')
    if not os.path.exists(extends_dir):
        return base_modules, base_sentences, reuse_count
    
    # Recursively find all YAML files in extends directory and extract sentences
    for root, dirs, files in os.walk(extends_dir):
        for file in files:
            if file.endswith('.yaml'):
                full_path = os.path.join(root, file)
                # Create relative path from extends directory
                rel_path = os.path.relpath(full_path, extends_dir)
                base_modules[rel_path] = full_path
                base_sentences[rel_path] = get_all_sentences_from_yaml(full_path)
    
    # Count reuse by analyzing all refactored modules
    for filename in os.listdir(refactored_dir):
        if filename.endswith('.yaml'):
            yaml_path = os.path.join(refactored_dir, filename)
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if 'prompt' in data and 'extends' in data['prompt']:
                    extends_list = data['prompt']['extends']
                    if isinstance(extends_list, list):
                        for extend in extends_list:
                            reuse_count[extend] += 1
                    elif isinstance(extends_list, str):
                        reuse_count[extends_list] += 1
            except Exception as e:
                print(f"Warning: Could not parse {yaml_path}: {e}")
    
    return base_modules, base_sentences, reuse_count


def collect_base_modules(refactored_dir: str) -> dict:
    """Collect all base modules from extends directory and count their reuse."""
    base_modules, _, reuse_count = collect_base_modules_and_sentences(refactored_dir)
    return base_modules, reuse_count


def calculate_token_reduction_ratio(original_dir: str, refactored_dir: str) -> float:
    """
    Calculate Token Reduction Ratio (TRR).
    TRR = (Σ T_orig - Σ T_peac) / Σ T_orig × 100
    
    T_orig = sum of all sentences (including duplicates) in original modules
    T_peac = sum of unique sentences in refactored modules + base modules (counted once)
    """
    # Count all sentences in original modules (including duplicates)
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
    
    # Count sentences in refactored modules
    all_peac_sentences = []
    
    # 1. Get sentences from leaf modules (only base sections, not extends)
    refactored_files = [f for f in os.listdir(refactored_dir) if f.endswith('.yaml')]
    for filename in refactored_files:
        yaml_path = os.path.join(refactored_dir, filename)
        try:
            sentences = get_all_sentences_from_yaml(yaml_path)
            all_peac_sentences.extend(sentences)
        except Exception as e:
            print(f"Warning: Could not process refactored file {filename}: {e}")
    
    # 2. Get sentences from base modules (counted once each)
    base_modules, base_sentences, _ = collect_base_modules_and_sentences(refactored_dir)
    for module_path, sentences in base_sentences.items():
        all_peac_sentences.extend(sentences)
    
    total_peac_tokens = count_tokens(' '.join(all_peac_sentences))
    
    if total_orig_tokens == 0:
        return 0.0
    
    trr = ((total_orig_tokens - total_peac_tokens) / total_orig_tokens) * 100
    return trr


def calculate_reuse_efficiency(original_dir: str, refactored_dir: str) -> float:
    """
    Calculate Reuse Efficiency (RE).
    RE = Σ (T(m) × reuse(m)) / Σ T_orig × 100
    """
    # Count all sentences in original modules
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
    
    if total_orig_tokens == 0:
        return 0.0
    
    # Calculate reuse efficiency
    base_modules, base_sentences, reuse_count = collect_base_modules_and_sentences(refactored_dir)
    total_reuse_tokens = 0
    
    for module_path, sentences in base_sentences.items():
        try:
            module_tokens = count_tokens(' '.join(sentences))
            module_reuse = reuse_count.get(module_path, 0)
            total_reuse_tokens += module_tokens * module_reuse
        except Exception as e:
            print(f"Warning: Could not process base module {module_path}: {e}")
    
    re = (total_reuse_tokens / total_orig_tokens) * 100
    return re


def calculate_modularity_index(refactored_dir: str) -> float:
    """
    Calculate Modularity Index (MI).
    MI = |M| / |L| × d_avg
    where |M| = number of unique base modules,
          |L| = number of leaf prompts,
          d_avg = average number of base modules extended by each leaf
    """
    # Count base modules and leaf prompts
    base_modules, reuse_count = collect_base_modules(refactored_dir)
    num_base_modules = len(base_modules)
    
    # Count leaf prompts and their extends
    refactored_files = [f for f in os.listdir(refactored_dir) if f.endswith('.yaml')]
    num_leaf_prompts = len(refactored_files)
    
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
    
    if valid_leaves == 0:
        return 0.0
    
    d_avg = total_extends / valid_leaves
    
    if num_leaf_prompts == 0:
        return 0.0
    
    mi = (num_base_modules / num_leaf_prompts) * d_avg
    return mi