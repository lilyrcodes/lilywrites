from lilywrites.document import DocumentMetadata, get_documents
from feedgen.feed import FeedGenerator
from pathlib import Path
from typing import Optional
from io import FileIO


def write_index_file(
        index_md_file: FileIO,
        documents: [DocumentMetadata],
        title: str):
    lines: list[str] = ['---', f'title: {title}', '---']
    for doc in documents:
        line = (
            f'**[{doc.input_path.stem}]'
            f'(./{doc.output_path.name})**'
        )
        if doc.summary is not None:
            line = f'{line} - {doc.summary}  '
        else:
            line = f'{line}  '
        lines.append(line)
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
        if doc.summary is not None:
            entry.description(doc.summary)
        if doc.pub_date is not None:
            entry.pubDate(doc.pub_date)
        entry.link(href=url)
    fg.rss_file(str(output_dir / 'rss.xml'))


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
