# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandoc>=2.4",
# ]
# ///

# /usr/bin/python3

import argparse
import pandoc
from collections import defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from pandoc.types import MetaValue, Pandoc, Text
from io import FileIO


def convert_file(input_path: Path, output_path: Path):
    pass


def extract_metadata_date(input_path: Path) -> str:
    doc: Pandoc = pandoc.read(input_path.read_text())
    meta: dict[Text, MetaValue] = doc[0][0]
    date = meta['date'][0]
    return pandoc.write(date).strip()


def write_index_file(
        index_md_file: FileIO,
        date_map: dict[str, [Path]],
        output_dir: Path,
        title: str):
    paths: list[Path] = [path for date in sorted(
        date_map) for path in date_map[date]]
    lines: list[str] = ['---', f'title: {title}', '---']
    for path in paths:
        lines.append(f'* [{path.stem}]({get_output_fname(path.name)})')
    for line in lines:
        print(line)
    pass


def get_output_fname(input_fname: str) -> str:
    return input_fname.lower().replace(' ', '_').replace('.md', '.html')


def convert_dir(markdown_dir: Path, output_dir: Path, index_md_file: FileIO, title: str):
    date_map: dict[str, Path] = defaultdict(list)
    for dirpath, dirnames, filenames in markdown_dir.walk():
        for fname in filenames:
            output_fname = get_output_fname(fname)
            input_path = dirpath / fname
            convert_file(input_path, output_dir / output_fname)
            date_map[extract_metadata_date(input_path)].append(input_path)
    write_index_file(index_md_file, date_map, output_dir, title)
    convert_file(Path(index_md_file.name), output_dir / 'index.html')


def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--markdown_dir', type=Path, required=True)
    parser.add_argument('-o', '--output_dir', type=Path, required=True)
    parser.add_argument('-t', '--title', type=str,
                        required=False, default="Home")
    args = parser.parse_args()
    if not args.markdown_dir.is_dir():
        raise FileNotFoundError(f"Markdown directory {
                                str(args.markdown_dir)} not found.")
    if not args.output_dir.is_dir():
        args.output_dir.mkdir()
    return args


def main():
    args = parse_and_validate_args()
    with NamedTemporaryFile(mode='w') as index_md_file:
        convert_dir(args.markdown_dir, args.output_dir,
                    index_md_file, args.title)


if __name__ == '__main__':
    main()
