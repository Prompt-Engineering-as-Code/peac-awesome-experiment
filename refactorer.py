from common import add_extends, get_on_section_type, open_sentences, parse_row, remove_query_section, remove_sentence_from_section, replace_section, save_yaml
from peac import PromptYaml

def update_peac_module(py: PromptYaml, section: str, sentence: str, extends: list[str], file):
    if len(extends) > 0:
        # print(f"Updating {file} : {section} - {sentence} with extends {extends}")
        if section != "query":
            sentences = get_on_section_type(py, section)
            new_sentences = remove_sentence_from_section(sentence, sentences)
            replace_section(py, section, new_sentences)
            if len(py.parsed_data['prompt'][section]['base']) != len(sentences) - 1: 
                raise ValueError(f"Sentence not removed properly : {len(py.parsed_data['prompt'][section])} != {len(sentences) - 1}")
        else: 
            print(f"Check {file} - removing query section")
            remove_query_section(py)

        add_extends(py, extends)
        save_yaml(py, file)



if __name__ == '__main__': 
    sentences = open_sentences()
    sentences = sentences[sentences['cluster_id'].notna()]
    rows = [parse_row(row) for _, row in sentences.iterrows()]
    print('Parsed', len(rows), 'rows.')

    rows_to_modify = [r for r in rows if len(r['extends']) > 0]
    print('Rows to modify', len(rows_to_modify))
    for r in rows_to_modify: 
        # print(f"Parsing {r['file']}")
        py = PromptYaml(r['file'])
        update_peac_module(py, r['section'], r['sentence'], r['extends'], r['file'])