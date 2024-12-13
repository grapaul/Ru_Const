import json
import io
import pathlib
import argparse
import os.path


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='sentence2json')
	parser.add_argument('--dir_in', type=str, default='Input/main', help='file with search results')
	parser.add_argument('--outdir', type=str, default='Output', help='dir with result file')
	parser.add_argument('--exnum', type=str, default='26688_10', help='example number')

	args = parser.parse_args()
	parsed_path = args.dir_in
	out_dir = args.outdir
	out_file = args.exnum

	filename = os.path.join(out_dir, str(out_file + ".json"))

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

	with open(filename, mode = 'w') as fp:
		json.dump(result_json, fp, indent=4)
