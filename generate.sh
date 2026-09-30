#!/bin/bash

CMD="${0}"

function stderr() {
    >&2 echo $@
}

function usage() {
    stderr "Usage: ${CMD} <path_to_markdown_dir> <title_of_index_page>"
    stderr ""
    stderr "Generates a static html site from a directory of markdown files."
    stderr ""
    stderr "path_to_markdown_dir: the path to the directory containing the markdown files to convert."
    stderr "title_of_index_page: the title to use for the auto-generated index page."
}

function convert() {
    local path="${1}"
    local index_file="${2}"
    stderr "Converting ${path}"
    local fname="$(basename "${path}")"
    local title="${fname%.*}"
    stderr "Extracted title ${title}"
    local lower_title="${title,,}"
    local output_fname="${lower_title// /_}.html"
    stderr "Writing html to ${output_fname}"
    echo "* [${title}](./${output_fname})" >> "${index_file}"
    pandoc -s -f markdown -t html5 -o "${output_fname}" --css style.css -B header.txt --metadata title="${title}" "${path}"
}

if ! command -v pandoc >/dev/null 2>&1
then
    stderr "pandoc could not be found. Please check your PATH or install pandoc."
    exit 1
fi

if [ "$#" -ne 2 ]; then
    usage
    exit 1
fi

input_dir="${1}"
index_title="${2}"
index_file="$(mktemp)"
trap "rm -f ${index_file}" EXIT
stderr "${index_file}"

for path in $input_dir/*.md ; do
    convert "${path}" "${index_file}"
done

stderr ""
stderr "Generated index markdown file:"
>&2 cat "${index_file}"
stderr ""

pandoc -s -f markdown -t html5 -o "index.html" --css style.css --metadata title="${index_title}" "${index_file}"
