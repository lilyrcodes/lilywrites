Tools to convert a directory of markdown files into a static website.

# Requirements

* [uv](https://docs.astral.sh/uv/)
* [pandoc](https://pandoc.org/)

# Running

The following command will generate static html files and a css file in
`$output_dir`. It will generate one file for each markdown file in
`$input_dir`, as well as an index file with links to each page. If provided
with the `-u` argument, it will also generate an `rss.xml` file.

The contents of `$output_dir` can then be hosted as a static site.

```bash
uv run src/generate.py \
    -i $input_dir \
    -o $output_dir \
    -t 'Title to appear on index page' \
    -u 'optional url used for rss feed generation'
```

# Input structure

`$input_dir` is expected to be a directory containing markdown files.

If present, this script will use
[Frontmatter metadata](https://www.markdownlang.com/advanced/frontmatter.html)
from those files to extract title, publication date, etc. If no metadata is
present, it will use the document's filename as a title, and all other metadata
will be considered missing.

# Limitations

* Currently doesn't support nested folders, as it only outputs to a flat directory
* Does not account for name collisions when converting input filenames (outputs
  are all snake_case and lowercase)
