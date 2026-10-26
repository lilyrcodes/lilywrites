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
        output_fname = get_output_fname(input_path)
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

    def convert(self, use_template: bool = True, link_rss_feed: bool = False):
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
            pdoc = pandoc.read(file=str(self.input_path), format='markdown')
            pandoc.write(pdoc, file=str(self.output_path),
                         format='html5', options=pandoc_options)
        finally:
            if rss_body:
                rss_body.close()
            if rss_head:
                rss_head.close()


def write_index_file(
        index_md_file: FileIO,
        documents: [DocumentMetadata],
        title: str):
    lines: list[str] = ['---', f'title: {title}', '---']
    for doc in documents:
        lines.append(
            f'* [{doc.input_path.stem}]'
            f'(./{doc.output_path.name})')
    index_md_file.write('\n'.join(lines))
    index_md_file.flush()


def write_rss_feed(
        documents: [DocumentMetadata],
        output_dir: Path,
        title: str,
        rss_url_root: str):
    fg = FeedGenerator()
    fg.title(title)
    fg.link(href=f'{rss_url_root}/rss.xml', rel='self')
    fg.description(title)
    for doc in documents:
        entry = fg.add_entry()
        url = f'{rss_url_root}/{doc.output_path.name}'
        entry.id(url)
        if doc.title is not None:
            entry.title(doc.title)
        if doc.pub_date is not None:
            entry.pubDate(doc.pub_date)
        entry.link(href=url)
    fg.rss_file(str(output_dir / 'rss.xml'))


def get_output_fname(input_path: Path) -> str:
    return input_path.name.lower().replace(' ', '_').replace('.md', '.html')


def get_documents(markdown_dir: Path, output_dir: Path) -> [DocumentMetadata]:
    documents: [DocumentMetadata] = []
    for dirpath, dirnames, filenames in markdown_dir.walk():
        for fname in filenames:
            if not fname.endswith('.md'):
                continue
            input_path = dirpath / fname
            documents.append(
                DocumentMetadata.CreateFromPaths(input_path, output_dir))
    return sorted(documents, key=lambda d: d.pub_date)


def convert_dir(
        markdown_dir: Path,
        output_dir: Path,
        index_md_file: FileIO,
        title: str,
        rss_url_root: Optional[str]):
    documents = get_documents(markdown_dir, output_dir)
    for doc in documents:
        doc.convert()
    write_index_file(index_md_file, documents, title)
    index_md_path = Path(index_md_file.name)
    index_doc = DocumentMetadata(
        input_path=index_md_path,
        output_path=output_dir / 'index.html',
        title=title,
        pub_date=None,
        summary=None)
    index_doc.convert(use_template=False, link_rss_feed=bool(rss_url_root))
    if rss_url_root:
        write_rss_feed(
            documents, output_dir, title, rss_url_root)


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
                    index_md_file, args.title, args.rss_url_root)
    copy_stylesheet(args.output_dir)


if __name__ == '__main__':
    main()
