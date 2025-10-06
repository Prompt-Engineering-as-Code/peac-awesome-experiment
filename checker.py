

from common import check_existence, check_sentence_in_section, get_on_section_type, get_sentence_index, open_sentences, parse_row, split_extend
from peac import PromptYaml


def check_all_extends():
    sentences = open_sentences()
    extends = []
    extends_section = sentences[sentences['extend_section'].notna()]['extend_section']
    for index, row in extends_section.items():
        extends = list(set(extends + split_extend(row)))



    print(f"[+] Check for {len(extends)} extends")
    for extend in extends:
        if not check_existence(extend):
            print(f"[-] does not exist: {extend}")

def check_all_sentences():
    not_found = 0
    sentences = open_sentences()
    rows = [parse_row(row) for _, row in sentences.iterrows()]
    for r in rows: 
        file = r['file']
        section = r['section']
        sentence = r['sentence']
        py = PromptYaml(file)
        section_rules = get_on_section_type(py, section)

        if not check_sentence_in_section(sentence, section_rules):
            raise ValueError(f"{file} - Sentence not found in {section} rules: {sentence}")
            not_found += 1

    print(f"Not found {not_found} sentences in total.")

def get_index_all_sentences():
    sentences = open_sentences()
    rows = [parse_row(row) for _, row in sentences.iterrows()]
    for r in rows: 
        file = r['file']
        section = r['section']
        sentence = r['sentence']
        py = PromptYaml(file)
        section_rules = get_on_section_type(py, section)

        index = get_sentence_index(sentence, section_rules)
        if index == -1:
            raise ValueError(f"{file} - Sentence not found in {section} rules: {sentence}")
        else:
            print(f"Found at index {index}: {sentence}")


if __name__ == "__main__":
    # check_all_extends()
    # check_all_sentences()
    get_index_all_sentences()