import sys
import fitz
from fitz.utils import getColor

import os
import pkg_resources
import re
import subprocess
import tempfile

import pdf_redactor


def mark_word(page, text):
    """Underline each word that contains 'text'.
    """
    found = 0
    col = (0, 0, 0)  # black color

    wlist = page.getTextWords()  # make the word list
    for w in wlist:  # scan through all words on page
        if text in w[4]:  # w[4] is the word's string
            found += 1  # count
            r = fitz.Rect(w[:4])  # make rect from word bbox
            # page.addRectAnnot(r)       # Rectangle
            page.drawRect(r, col, fill=col, width=1, dashes=None, roundCap=True, overlay=True, morph=None)
            #Replace word so it cant be searched for  - not working as I thought!
            #page.insertText(r[0:2], 'xxx',fontsize=11)

    return found


def redact(fname, searchlist):
    """Lets Redact the pdf
    """
    #fname = sys.argv[1]  # filename

    doc = fitz.open(fname)

    doc.setMetadata({})    # clear metadata
    doc._delXmlMetadata()  # clear any XML metadata

    new_doc = False  # indicator if anything found at all

    for page in doc:  # scan through the pages

        for word in searchlist:
            print(f"Redacting word {word} in document {doc.name}")
            found = mark_word(page, word)  # mark the page's words
            if found:  # if anything found ...
                new_doc = True
                print("found '%s' %i times on page %i" % (word, found, page.number + 1))

    if new_doc:
        doc.save("marked-" + str(doc.name).split('/')[-1])


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
        "DEFAULT": [lambda value: None],
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
            lambda m: "X"
        ),

        # Then do an actual SSL regex.
        # See https://github.com/opendata/SSN-Redaction for why this regex is complicated.
        # (
        # 	re.compile(r"(?<!\d)(?!666|000|9\d{2})([OoIli0-9]{3})([\s-]?)(?!00)([OoIli0-9]{2})\2(?!0{4})([OoIli0-9]{4})(?!\d)"),
        # 	lambda m : "XXX-XX-XXXX"
        # ),

        # Content filter that runs on the text comment annotation body.
        (
            re.compile(r"comment!"),
            lambda m: "annotation?"
        )#,
    ]

    # Filter the link target URI.
    options.link_filters = [
        lambda href, annotation: "https://www.google.com"
    ]

    # Perform the redaction using PDF on standard input and writing to standard output.
    pdf_redactor.redactor(options)






# THE SEARCH STRING LIST
# searchlist = ['Marcus', 'Hibell', 'Lorem', 'Hampden-Sydney', 'College', 'loves']
# redact('Lorem.pdf',searchlist)









# WORKING VERSION FOR A SINGLE WORD
# fname = sys.argv[1]                    # filename
# text = sys.argv[2]                     # search string
# doc = fitz.open(fname)

# print("underlining words containing '%s' in document '%s'" % (text, doc.name))

# new_doc = False                        # indicator if anything found at all

# for page in doc:                       # scan through the pages
#     found = mark_word(page, text)      # mark the page's words
#     if found:                          # if anything found ...
#         new_doc = True
#         print("found '%s' %i times on page %i" % (text, found, page.number + 1))

# if new_doc:
#     doc.save("marked-" + str(doc.name).split('/')[-1])