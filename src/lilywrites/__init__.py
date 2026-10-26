import argparse
from pathlib import Path
from lilywrites.generate import convert_dir
from tempfile import NamedTemporaryFile


def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--markdown_dir', type=Path, required=True)
    parser.add_argument('-o', '--output_dir', type=Path, required=True)
    parser.add_argument('-t', '--title', type=str,
                        required=False, default="Home")
    parser.add_argument('-u', '--rss_url_root', type=str, required=False)
    args = parser.parse_args()
    if not args.markdown_dir.is_dir():
        raise FileNotFoundError(f"Markdown directory {
                                str(args.markdown_dir)} not found.")
    if not args.output_dir.is_dir():
        args.output_dir.mkdir()
    return args


def copy_stylesheet(output_dir: Path):
    Path('resources/style.css').copy_into(output_dir)


def main() -> None:
    args = parse_and_validate_args()
    with NamedTemporaryFile(mode='w') as index_md_file:
        convert_dir(args.markdown_dir, args.output_dir,
                    index_md_file, args.title, args.rss_url_root)
    copy_stylesheet(args.output_dir)
