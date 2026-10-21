# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "feedgen>=1.0.0",
#     "pandoc>=2.4",
# ]
# ///

# /usr/bin/python3

import argparse
import datetime
import pandoc
from collections import defaultdict
from dataclasses import dataclass
from feedgen.feed import FeedGenerator
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Self
from pandoc.types import MetaValue, Pandoc, Text
from io import FileIO


@dataclass
class DocumentMetadata:
    input_path: Path
    output_path: Path
    title: str
    pub_date: Optional[datetime.datetime]
    summary: Optional[str]

    @classmethod
    def CreateFromPaths(cls, input_path: Path, output_dir: Path) -> Self:
        doc: Pandoc = pandoc.read(input_path.read_text())
        meta: dict[Text, MetaValue] = doc[0][0]
        output_fname = get_output_fname(input_path.name)
        pub_date_str: Optional[str] = None
        if 'date' in meta:
            pub_date_str = pandoc.write(meta['date'][0]).strip()
        pub_date: Optional[datetime.datetime] = None
        if pub_date_str is not None:
            d = datetime.date.fromisoformat(pub_date_str)
            pub_date = datetime.datetime(
                d.year, d.month, d.day, 0, 0, 0, 0, datetime.timezone.utc)
        title: str = ''
        if 'title' in meta:
            title = pandoc.write(meta['title'][0]).strip()
        else:
            title = input_path.stem
        summary: Optional[str] = None
        if 'summary' in meta:
            summary = pandoc.write(meta['summary'][0]).strip()
        return DocumentMetadata(
            input_path=input_path,
            output_path=output_dir / output_fname,
            title=title,
            pub_date=pub_date,
            summary=summary)


def convert_file(
        doc: DocumentMetadata,
        use_template: bool = True,
        link_rss_feed: bool = False):
    pandoc_options = [
        '-s',
        '--css',
        'style.css',
    ]
    if use_template:
        pandoc_options += [
            '--template',
            'resources/template.html',
        ]
    rss_head: Optional[NamedTemporaryFile] = None
    rss_body: Optional[NamedTemporaryFile] = None
    try:
        if link_rss_feed:
            rss_head = NamedTemporaryFile(mode='w')
            rss_head.write(
                '<link rel="alternate" '
                'type="application/rss+xml" '
                'title="RSS Feed" '
                'href="rss.xml">\n')
            rss_body = NamedTemporaryFile(mode='w')
            rss_body.write(
                '<div id="rsslink">'
                '<a href="rss.xml" '
                'title="View RSS Feed" '
                'aria-label="View RSS Feed">'
                '🛜</a></div> \n')
            rss_head.flush()
            rss_body.flush()
            pandoc_options += [
                '--include-in-header',
                rss_head.name,
                '--include-after-body',
                rss_body.name,
            ]
        doc = pandoc.read(file=str(doc.input_path), format='markdown')
        pandoc.write(doc, file=str(doc.output_path),
                     format='html5', options=pandoc_options)
    finally:
        if rss_body:
            rss_body.close()
        if rss_head:
            rss_head.close()


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
        lines.append(f'* [{path.stem}](./{get_output_fname(path.name)})')
    index_md_file.write('\n'.join(lines))
    index_md_file.flush()


def write_rss_feed(
        markdown_dir: Path,
        output_dir: Path,
        title: str,
        rss_url_root: str):
    date_map = get_date_map(markdown_dir)
    fg = FeedGenerator()
    fg.title(title)
    fg.link(href=f'{rss_url_root}/rss.xml', rel='self')
    fg.description(title)
    for date in sorted(date_map.keys()):
        for path in date_map[date]:
            entry = fg.add_entry()
            d = datetime.date.fromisoformat(date)
            dt = datetime.datetime(
                d.year, d.month, d.day, 0, 0, 0, 0, datetime.timezone.utc)
            url = f'{rss_url_root}/{get_output_fname(path.name)}'
            entry.id(url)
            entry.title(path.stem)
            entry.pubdate(dt)
            entry.link(href=url)
    fg.rss_file(str(output_dir / 'rss.xml'))


def get_output_fname(input_fname: str) -> str:
    return input_fname.lower().replace(' ', '_').replace('.md', '.html')


def get_date_map(markdown_dir: Path) -> dict[str, [Path]]:
    date_map: dict[str, [Path]] = defaultdict(list)
    for dirpath, dirnames, filenames in markdown_dir.walk():
        for fname in filenames:
            input_path = dirpath / fname
            date_map[extract_metadata_date(input_path)].append(input_path)
    return date_map


def convert_dir(
        markdown_dir: Path,
        output_dir: Path,
        index_md_file: FileIO,
        title: str,
        link_rss_feed: bool):
    date_map = get_date_map(markdown_dir)
    for dirpath, dirnames, filenames in markdown_dir.walk():
        for fname in filenames:
            input_path = dirpath / fname
            doc = DocumentMetadata.CreateFromPaths(input_path, output_dir)
            convert_file(doc)
    write_index_file(index_md_file, date_map, output_dir, title)
    convert_file(Path(index_md_file.name),
                 output_dir / 'index.html',
                 use_template=False, link_rss_feed=link_rss_feed)


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


def main():
    args = parse_and_validate_args()
    with NamedTemporaryFile(mode='w') as index_md_file:
        convert_dir(args.markdown_dir, args.output_dir,
                    index_md_file, args.title, bool(args.rss_url_root))
    copy_stylesheet(args.output_dir)
    if args.rss_url_root:
        write_rss_feed(args.markdown_dir, args.output_dir,
                       args.title, args.rss_url_root)


if __name__ == '__main__':
    main()
