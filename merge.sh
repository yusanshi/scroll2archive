#!/bin/bash

# https://unix.stackexchange.com/questions/368415/merge-pdf-files-and-automatically-create-a-table-of-contents-with-each-file-as-a

# usage:
# in output directory
# ../merge..sh 1.pdf 2.pdf 3.pdf

out_file="combined.pdf"
out_ocr_file="combined-ocr.pdf"
bookmarks_file="/tmp/bookmarks.txt"
bookmarks_fmt="BookmarkBegin
BookmarkTitle: %s
BookmarkLevel: 1
BookmarkPageNumber: %d
"

rm -f "$bookmarks_file" "$out_file" "$out_ocr_file"

files=("$@")
page_counter=1

# Generate bookmarks file.
for f in "${files[@]}"; do
    title="${f%.*}"
    printf "$bookmarks_fmt" "$title" "$page_counter" >> "$bookmarks_file"
    num_pages="$(pdftk "$f" dump_data | grep NumberOfPages | awk '{print $2}')"
    page_counter=$((page_counter + num_pages))
done

# Combine PDFs and embed the generated bookmarks file.
pdftk "${files[@]}" cat output - | \
    pdftk - update_info "$bookmarks_file" output "$out_file"

# https://github.com/ocrmypdf/OCRmyPDF/issues/715
ocrmypdf -l eng+chi_sim "$out_file" "$out_ocr_file"
