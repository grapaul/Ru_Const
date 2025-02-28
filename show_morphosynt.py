import json
import io
import pathlib
import argparse
import os.path
import re
from ast import literal_eval
from nltk.tree import *
import svgling


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='sentence2json')
    parser.add_argument('--dir_in', type=str, default='Input/main', help='file with search results')
    parser.add_argument('--outdir', type=str, default='Output', help='dir with result file')
    parser.add_argument('--exnum', type=str, default='26688_10', help='example number')

    args = parser.parse_args()
    parsed_path = args.dir_in
    out_dir = args.outdir
    out_file = args.exnum

    svg_file = str(out_file + ".svg")
    filename_t = os.path.join(out_dir, svg_file)
    filename_h = os.path.join(out_dir, str(out_file + ".html"))


    result_json = []

    directory_in = os.path.join(os.getcwd(), parsed_path)

    for file in os.listdir(directory_in): 
        fi = os.path.join(directory_in, file)
        with io.open(fi, "r", encoding='utf-8') as f2:
            data = json.load(f2)
    
        for i in data:
            if i['id'] == out_file:
                result_json.append(i)
                break
    if len(result_json) > 0:
        br = result_json[0]['sentence_tree']
        punc = '''!()«»–-—{};:'",<>./?@#$%^&*_~'''
        for ele in punc:
        	br = br.replace(ele, "")
        tree = Tree.fromstring(br, brackets='[]')
        print(tree)
        

    tree = str(tree)
    for l in tree.split('\n'):
        lnew = '<pre>' + l + '</pre>'
        tree = tree.replace(l, lnew, 1)


    def correct_brackets(ti):
        tr = re.sub(' +', ' ', ti.replace('[','(').replace(']',')'))
        tr = str(tr.split(' ')).replace('[\'','(\'').replace('\']','\')').replace(')\', \')', '))')
        tr = tr.replace(', \'\'', '').replace('\'\', ', '')
        pat1 = r"(\')(\(+)"
        pat2 = r"(\)+)(\')"
        tr = re.sub(pat1, r"\2\1", tr)
        tr = re.sub(pat2, r"\2\1", tr)
        tr = literal_eval(tr)
        return tr


    tsv = svgling.draw_tree(correct_brackets(br))
    print(tsv)
    fsvg = tsv.get_svg().saveas(filename_t)


    all_tok = ''
    for t in result_json[0]['tokens']:
        all_tok = all_tok + '<p>' + t['lemma'] + '\t' + '; '.join(t['tagsets'][0]) + '</p>'

    html_template = """<html>
    <head>
    <title>{0}</title>
    </head>
    <body>
    <h2>{1}</h2>
    <h3>Скобочное представление</h3>
    <p>{2}</p>
    <h3>Структура</h3>
    <div style="background-color:powderblue;font-size:1vw">
    {3}
    </div>
    <img
    src={4} />

    <h3>Словоформы</h3>
    <p>{5}</p>
    </body>
    </html>
    """.format(out_file, out_file, br, tree, svg_file, all_tok)


    f = open(filename_h, 'w')
    f.write(html_template)

