import datetime
import pandoc
from dataclasses import dataclass
from pathlib import Path
from pandoc.types import MetaValue, Pandoc, Text
from tempfile import NamedTemporaryFile
from typing import Optional, Self


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
        output_fname = _get_output_fname(input_path)
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


def _get_output_fname(input_path: Path) -> str:
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
