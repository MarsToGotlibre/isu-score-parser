from flask import Flask, render_template, send_from_directory
import os
import json
from pathlib import Path

app = Flask(__name__)
CONFIG = {}

@app.route('/')
def index():
    target_pdf = Path(CONFIG["PDF_PATH"]).name

    pages_dict={}       
    for filename in sorted(Path(CONFIG['EVENT_DIR']).glob("*.json")):

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # verification via metadata
                
        except Exception as e:
            print(f"Erreur lecture {filename}: {e}")
        if data.get("meta", {}).get("sourcefile") == target_pdf:
            p_num = data.get('meta', {}).get('page', 1)
            if p_num not in pages_dict:
                pages_dict[p_num] = []
            pages_dict[p_num].append(prepare_table_layout(data))


    sorted_pages = []
    for p in sorted(pages_dict.keys()):
        # Sorts table on this page
        tables_of_this_page = sorted(
            pages_dict[p], 
            key=lambda x: x.get('meta', {}).get('table_index', 0)
        )
        sorted_pages.append(tables_of_this_page)    
    return render_template('index.html', tables=sorted_pages, pdf_url="/pdf_file")

@app.route('/pdf_file')
def serve_pdf():
    return send_from_directory(os.path.dirname(CONFIG["PDF_PATH"]), 
                               os.path.basename(CONFIG["PDF_PATH"]))

def prepare_table_layout(table):
    # 1. Determines how many judges (ex: J1 to J9)
    # We look for the first element to count
    judges_list = []
    if table['results']['technical_elements']:
        first_el_judges = table['results']['technical_elements'][0]['judges']
        judges_list = [j for j in first_el_judges.keys() if first_el_judges[j] is not None]
    
    # 2. Verification of optional columns
    has_bonus = any(el.get('bonus') for el in table['results']['technical_elements'])
    has_deduction = any(el.get('element_deduction') for el in table['results']['technical_elements'])
    
    # 3. Total Colsplan
    # Base (5) : #, Element, Info, Base, GOE
    # + Juges
    # + Bonus (1 si présent)
    # + Deduction (1 si présent)
    # + Score+Ref. (2)
    total_columns = 5 + len(judges_list) + (1 if has_bonus else 0) + (1 if has_deduction else 0) + 2
    
    # We add this to a new entry of the dictionnary
    table['layout'] = {
        'judges_list': judges_list,
        'has_bonus': has_bonus,
        'has_deduction': has_deduction,
        'total_columns': total_columns
    }
    return table


def run_server(event_dir, pdf_path, port):
    CONFIG["EVENT_DIR"] = event_dir
    CONFIG["PDF_PATH"] = pdf_path
    app.run(debug=True, port=port)