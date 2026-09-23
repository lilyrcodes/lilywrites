#!/bin/bash

if ! command -v pandoc >/dev/null 2>&1
then
    echo "pandoc could not be found. Please check your PATH or install pandoc."
    exit 1
fi

if [ "$#" -ne 1 ]; then
    echo "Please specify the input directory"
    exit 1
fi

input_dir="${1}"
index_file="$(mktemp)"
trap "rm -f ${index_file}" EXIT
echo "${index_file}"

for path in $input_dir/*.md ; do
	echo $path
	fname="$(basename "${path}")"
	echo "$fname"
	title="${fname%.*}"
	echo $title
	lower_title="${title,,}"
	echo "${lower_title}"
	output_fname="${lower_title// /_}.html"
	echo "${output_fname}"
	echo "* [${title}](./${output_fname})" >> "${index_file}"
	pandoc -s -f markdown -t html5 -o "${output_fname}" --css style.css -B header.txt --metadata title="${title}" "${path}"
done

cat "${index_file}"
pandoc -s -f markdown -t html5 -o "index.html" --css style.css --metadata title="Lily Writes (Smut) For Fun" "${index_file}"
