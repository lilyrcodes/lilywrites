# /usr/bin/python3

import argparse
from pathlib import Path
from tempfile import TemporaryFile
from io import FileIO


def convert_dir(markdown_dir: Path, output_dir: Path, index_md_file: FileIO):
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--markdown_dir', type=Path, required=True)
    parser.add_argument('-o', '--output_dir', type=Path, required=True)
    args = parser.parse_args()
    with TemporaryFile(mode='w') as index_md_file:
        convert_dir(args.markdown_dir, args.output_dir, index_md_file)


if __name__ == '__main__':
    main()
