import argparse
import pandas as pd
# noinspection PyCompatibility
import urllib.parse
# noinspection PyCompatibility
import urllib.request
import os


lore_url = 'https://vectorization.computer/AJAX/get_src.php'
out_dir = os.environ["LORE_ORIG_PATH"]


def main():
    """
    The input file can be obtained from LORE repository online by running the query:
        SELECT id, application, benchmark, file, line, function, version FROM loops
    at https://vectorization.computer/query.html

    (valid as of Aug 2018)
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", help="Path to CSV file obtained from LORE query.")
    args = parser.parse_args()
    input_file = args.file_name

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    x = pd.read_csv(input_file)
    x.rename({'function': 'func'}, axis='columns', inplace=True)

    rows = x.to_dict(orient='records')

    for row in rows:
        fname = out_dir + 'lore_' + row['id'] + '_' + str(row['line']) + '.c'

        if os.path.isfile(fname):
            print('Skipping ' + fname.split('/')[-1] + ' (already exists)')
            continue
        else:
            print('Downloading ' + fname.split('/')[-1])

        data = urllib.parse.urlencode(row)

        res = urllib.request.urlopen(lore_url + '?' + data)
        code = res.read()

        if len(code) > 1:
            with open(fname, 'w') as fout:
                fout.write(code.decode('utf-8'))
        else:
            print('\t(Empty file)')


if __name__ == "__main__":
    main()
