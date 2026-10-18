# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandoc>=2.4",
# ]
# ///

# /usr/bin/python3

import argparse
from pathlib import Path
from tempfile import NamedTemporaryFile
from io import FileIO


def convert_file(input_path: Path, output_path: Path):
    pass


def extract_metadata_date(input_path: Path) -> str:
    pass


def write_index_file(
        index_md_file: FileIO,
        date_map: dict[Path, str],
        output_dir: Path):
    pass


def convert_dir(markdown_dir: Path, output_dir: Path, index_md_file: FileIO):
    date_map: dict[Path, str] = {}
    for dirpath, dirnames, filenames in markdown_dir.walk():
        for fname in filenames:
            output_fname = fname.lower().replace(
                ' ', '_').replace('.md', '.html')
            input_path = dirpath / fname
            convert_file(input_path, output_dir / output_fname)
            date_map[input_path] = extract_metadata_date(input_path)
    write_index_file(index_md_file, date_map, output_dir)
    convert_file(Path(index_md_file.name), output_dir / 'index.html')


def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--markdown_dir', type=Path, required=True)
    parser.add_argument('-o', '--output_dir', type=Path, required=True)
    args = parser.parse_args()
    if not args.markdown_dir.is_dir():
        raise FileNotFoundError(f"Markdown directory {
                                str(args.markdown_dir)} not found.")
    if not args.output_dir.is_dir():
        args.output_dir.mkdir()
    return args


def main():
    args = parse_and_validate_args()
    with NamedTemporaryFile(mode='rw') as index_md_file:
        convert_dir(args.markdown_dir, args.output_dir, index_md_file)


if __name__ == '__main__':
    main()
