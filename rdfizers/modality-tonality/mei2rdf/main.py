import argparse
from asyncio.format_helpers import _format_callback
import chardet
from lxml import etree
from pathlib import PurePath

from sherlockcachemanagement import Cache
from sherlock_xml import idize
from mei_beats import get_beats_data
from mei_sherlockizer import rdfize

parser = argparse.ArgumentParser()
parser.add_argument("--input_mei_file")
parser.add_argument("--cache")
parser.add_argument("--output_mei_folder")
parser.add_argument("--output_ttl_folder")
args = parser.parse_args()
filename = PurePath(args.input_mei_file).name

cache = Cache(args.cache)

uuid = cache.get_uuid([filename], True)

with open(args.input_mei_file, "rb") as f:
    f_content = f.read()
    input_mei_file_encoding = chardet.detect(f_content)
    input_mei_file_doc = etree.fromstring(f_content)
    idized_input_mei_file_doc = idize(input_mei_file_doc)
    with open(PurePath(args.output_mei_folder, uuid + ".mei"), "wb") as f2:
        etree.ElementTree(idized_input_mei_file_doc).write(
            f2,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        )

    beats_data = get_beats_data(idized_input_mei_file_doc)

    rdfize(
        "http://data-iremus.huma-num.fr/graph/mei",
        idized_input_mei_file_doc,
        uuid,
        beats_data["score_beats"],
        beats_data["elements"],
        PurePath(args.output_ttl_folder, uuid + ".ttl")
    )

cache.bye()
