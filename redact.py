import re
from datetime import datetime
from pathlib import Path
from re import Pattern
from typing import List

import fitz
import spacy as spacy
from fitz.fitz import Page, Rect

import pdf_redactor

NLP = spacy.load("en_core_web_sm", exclude=["parser"])  # Speeds up loading
NLP.enable_pipe("senter")

SECTIONS = [
    {"sectionType": "PersonalDetails", "bbox": [0.0, 39.2677917480469, 612.0, 111.941596984863],
     "pageIndex": 0,
     "text": "Aaron A. Augustine  (704) 996-5466  aaaron29@vt.edu\nPermanent Address:  18205 Mainsail Pointe Drive  Cornelius, NC 28031\nSchool Address:  700 Barringer Drive  Blacksburg, VA, 24060"
     },
    {"sectionType": "Summary", "bbox": [0.0, 118.547088623047, 612.0, 155.509033203125], "pageIndex": 0,
     "text": "Objective\nTo obtain a Summer 2020 internship with a dynamic, innovative engineering company to gain practical  knowledge of the technical and business components of their engineering practices."
     },
    {"sectionType": "Education", "bbox": [0.0, 174.976089477539, 612.0, 225.479766845703], "pageIndex": 0,
     "text": "Education\nMajor: Bachelor of Science, Mechanical Engineering, expected May 2021  Minor: Green Engineering  Virginia Polytechnic Institute and State University (Virginia Tech), Blacksburg, VA"
     },
    {"sectionType": "WorkExperience", "bbox": [0.0, 232.023818969727, 612.0, 361.827789306641], "pageIndex": 0,
     "text": "Internships\nHypercar Development - Intern  Interned with Hypercar Development from May 2017 to August 2017. Hypercar Development specializes in  active and dual function aerodynamics, upgraded turbo systems, and performance software for McLaren Automotive cars.  Responsibilities included CAD modeling, modification, and assembly of various components.\nCummins Power Generation \u00e2\u20ac\u201c Product Design Engineer Intern  Interned with Cummins Power Generation from May 2018 to August 2018. Cummins Power Generation provides  home, commercial, and mobile Generator Sets with integrated control solutions. Responsibilities included design FMEAs,  C&E selection matrices, concept generation, and calculation of various applied mechanics for a positive head fuel system.  and prototyping and validation for an oil make-up system."
     },
    {"sectionType": "Skills/Interests/Languages", "bbox": [0.0, 380.935119628906, 612.0, 529.979187011719],
     "pageIndex": 0,
     "text": "Related Skills\nPrototyping Experience with 3-D printing and CNC mills with an understanding of the operation and limitations of various  machines such as CNC axis limitations.\nComputer Aided Design  Proficient in SOLIDWORKS and Autodesk CAD Programs, including finite element analysis.\nBasic Coding Basic coding knowledge of MATLAB, BMW Standard Tools, LabVIEW, and Arduino Sketches.\nMechanical Design  In-depth experience with mechanical design including structural mechanics, material and manufacturing process  selection, and mechanical drawing/CAD conversion."
     },
    {"sectionType": "Achievements", "bbox": [0.0, 549.738647460938, 612.0, 682.391479492188], "pageIndex": 0,
     "text": "Notable Achievements\nPresident of Theta Chi Fraternity, Eta Lambda Chapter (December 2017-August 2018)  Responsibilities included maintenance of alumni and university relations, oversight of executive officers, and  responsibility for all fraternity actions, events, and endeavors.\nVice President of Theta Chi Fraternity, Eta Lambda Chapter (September 2017-December 2017)  Responsibilities included oversight and responsibility for all bylaws, judicial board cases, and non-executive  officers.\nExchange Student with University of Technology, Sydney (February 2019-June 2019)\nStudied Mechanical Engineering at the University of Technology, to gain experience with international engineers  while taking accredited courses."
     },
    {"sectionType": "Referees", "bbox": [0.0, 689.281372070312, 612.0, 751.294372558594], "pageIndex": 0,
     "text": "References\nStephany Aldana, Team Member/Mentor, Cummins Power Generation: stephany.aldana@cummins.com  Bob Montero, Manager, Cummins Power Generation: bob.j.montero@cummins.com  Thad Norman, Hypercar Development: (980) 395-4161  Mike Irwin, Alumni Chairman, Theta Chi Fraternity: (804) 337-2644"
     }
]


def split_input_text(input_str: str):
    doc = NLP(input_str)
    sentences = [sent for sent in doc.sents]
    # print("Split sentences:")
    # for s in sentences:
    #     print(s)
    return sentences


def mark_word(page: Page, text):
    """Underline each word that contains 'text'.
    """
    found = 0
    col = (1, 0, 0)  # black color

    wlist = page.get_text_words()  # make the word list

    for w in wlist:  # scan through all words on page
        if text in w[4]:  # w[4] is the word's string
            found += 1  # count
            r = fitz.Rect(w[:4])  # make rect from word bbox
            page.draw_rect(r, col, fill=col, width=1, dashes=None, overlay=True, morph=None, fill_opacity=0.5)
    return found


def get_blocks_within_rect(page: Page, rect: Rect, highlight_words=True):
    """
    Get words that are within and intersect with a given rect
    See https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/textbox-extraction
    """
    words = page.getText("words")  # list of words on page

    # Draw rect around area to be redacted
    page.draw_rect(rect, (0, 1, 0), fill=(0, 1, 0), width=1, dashes=None, overlay=True, morph=None, fill_opacity=0.5)
    words_in_rect = [w for w in words if fitz.Rect(w[:4]).intersects(rect)]
    if highlight_words:
        # Draw redact boxes around blocks to be redacted
        color = (1, 0, 0)  # RED
        for word in words_in_rect:
            r = fitz.Rect(word[:4])
            page.addRedactAnnot(r)
    # Split into blocks, note we didnt use getText("blocks") as this is less sensative to words near boundary of box
    blocks = {}
    for word in words_in_rect:
        block_id = word[5]
        if blocks.get(block_id) is None:
            blocks[block_id] = [word[4]]
        else:
            blocks[block_id].append(word[4])

    print(f"blocks_in_rect = {blocks}")
    return [" ".join(block) for block in blocks.values()]


def make_regex_from_words(words):
    """ Used with get_blocks_within_rect() to make a regex to match only the tokens inside a rect"""
    # [romt)]
    return re.compile(r".\s*".join([w[4].strip() for w in words if w[4] not in [" ", "\n", "\t"]]), re.DOTALL)


def make_regex_from_block(block_text: str):
    """ Used with get_blocks_within_rect() to make a regex to match only the tokens inside a rect"""
    if block_text.replace("\n", "").strip != "":
        return re.compile(block_text, re.DOTALL)
    else:
        return None


def clean_block_text(block_text: str):
    # Clean lots of new lines, replace with match for any whitespace, and escape original words
    cleaned_text = re.split(r"\s+", block_text)
    cleaned_text = r"\s+".join(re.escape(s) for s in cleaned_text)
    return cleaned_text


def generate_regex_from_rect(page: Page, rect: Rect) -> List[Pattern]:
    raw_blocks_in_text = get_blocks_within_rect(page, rect)

    # TODO Clean up blocks here
    sentences = []
    for block in raw_blocks_in_text:
        sentences.extend(split_input_text(block))

    sentences = [clean_block_text(sentence.text) for sentence in sentences]
    rect_regexes = []
    for sentence in sentences:
        sen_regex = make_regex_from_block(sentence)
        if sen_regex is not None:
            rect_regexes.append(sen_regex)
    print(f"regexes =")
    for rect_regex in rect_regexes:
        print(rect_regex)
    return rect_regexes


def print_match(m: re.Match):
    s = m.group(0)
    len_chars_without_spaces = len(re.sub(r"\s+", "", s))
    print(f"Replacing {s} at span {m.span()}")
    print(f"len of group: {len(m.group())}")
    print(fr"len of words without spaces: {len_chars_without_spaces}")
    return r""


def redact_with_regex(in_file: Path, out_file: Path, regexes: List[Pattern]):
    # Set options.
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
    content_filters_from_regex = [(regex, lambda m: print_match(m)) for regex in regexes]
    options.content_filters = [
        # Then do an actual SSL regex.
        # See https://github.com/opendata/SSN-Redaction for why this regex is complicated.
        # (
        # 	re.compile(r"(?<!\d)(?!666|000|9\d{2})([OoIli0-9]{3})([\s-]?)(?!00)([OoIli0-9]{2})\2(?!0{4})([OoIli0-9]{4})(?!\d)"),
        # 	lambda m : "XXX-XX-XXXX"
        # ),

        # Content filter that runs on the text comment annotation body.
        # (
        #     re.compile(r"comment!"),
        #     lambda m: "annotation?"
        # )  # ,
    ]
    options.content_filters.extend(content_filters_from_regex)

    # Filter the link target URI.
    options.link_filters = [
        lambda href, annotation: ""
    ]

    options.input_stream = in_file
    options.output_stream = out_file

    # Perform the redaction using PDF on standard input and writing to standard output.
    pdf_redactor.redactor(options)


if __name__ == '__main__':
    # THE SEARCH STRING LIST
    searchlist = ['Marcus', 'Hibell', 'Lorem', 'Hampden-Sydney', 'College', 'loves']
    # redact('Lorem.pdf', searchlist)

    # WORKING VERSION FOR A SINGLE WORD
    input_file = list(Path("./in").glob("*.pdf"))[0]
    marked_file = Path(f"./out/{input_file.stem}_marked.pdf")
    output_file = Path(f"./out/{input_file.stem}_redacted.pdf")
    redact_text = "References"
    fdoc = fitz.open(str(input_file))

    print(f"underlining words containing '{redact_text}' in document '{fdoc.name}'")
    redact_section = SECTIONS[0]
    print(f"Redacting text from {redact_section['sectionType']}")
    print(f"bbox : {redact_section['bbox']}")
    regexes = []
    for pg in fdoc:  # scan through the pages
        if pg.number == redact_section["pageIndex"]:
            redact_rect = Rect(*redact_section["bbox"])
            regexes.extend(generate_regex_from_rect(page=pg, rect=redact_rect))

    fdoc.save(str(marked_file))
    print(f"Saved marked file to {output_file}")
    # for pg in fdoc:  # scan through the pages
    #     if pg.number == redact_section["pageIndex"]:
    #         # fitz.utils.apply_redactions(pg, images=2)
    #         # pg.apply_redactions(True)
    #
    #         redact_rect = Rect(*redact_section["bbox"])
    #         regexes.extend(generate_regex_from_rect(page=pg, rect=redact_rect))
    # fitz.utils.scrub(fdoc, redact_images=2)
    # fdoc.save(str(output_file))

    redact_with_regex(marked_file, output_file, regexes=regexes)
