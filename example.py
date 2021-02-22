# ;encoding=utf-8
# Example file to redact Social Security Numbers from the
# text layer of a PDF and to demonstrate metadata filtering.

import re
from datetime import datetime

import pdf_redactor

## Set options.

options = pdf_redactor.RedactorOptions()

options.metadata_filters = {
    # Perform some field filtering --- turn the Title into uppercase.
    "Title": [lambda value: value.upper()],

    # Set some values, overriding any value present in the PDF.
    "Producer": [lambda value: "My Name"],
    "CreationDate": [lambda value: datetime.utcnow()],

    # Clear all other fields.
    "DEFAULT": [lambda value: None]
}

# Clear any XMP metadata, if present.
options.xmp_filters = [lambda xml: None]

# Redact things that look like social security numbers, replacing the
# text with X's.
options.content_filters = [
    # First convert all dash-like characters to dashes.
    (
        # re.compile(u"[−–—~‐]"),
        # lambda m : "-"
        re.compile(u"LibreOffice"),
        lambda m: "(REDACTED)"
    ),
    # Content filter that runs on the text comment annotation body.
    (
        re.compile(r"comment!"),
        lambda m: "annotation?"
    )
]

# add to the options
searchlist = ['PDF', 'SSN', 'LibreOffice']

for word in searchlist:
    options.content_filters.append((re.compile(word), lambda m: "(REDACTED)"))

# Filter the link target URI.
options.link_filters = [
    lambda href, annotation: "https://www.google.com"
]

# Perform the redaction using PDF on standard input and writing to standard output.
pdf_redactor.redactor(options)
