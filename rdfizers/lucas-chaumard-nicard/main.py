import argparse
from datetime import datetime
import openpyxl
import pathlib
from pprint import pprint
import rdflib

from sherlockcachemanagement import Cache

parser = argparse.ArgumentParser()
parser.add_argument("--in_xlsx")
parser.add_argument("--out_ttl")
args = parser.parse_args()

wb = openpyxl.load_workbook(filename=pathlib.Path(args.in_xlsx))
ws = wb.active


def read(x):
    # if x.hyperlink:
    #     print(x.hyperlink.target)
    if type(x.value) == str:
        x = x.value.strip()
        if len(x) == 0:
            return None
        return x
    return x.value


def values(x): return list(map(lambda x: read(x), x))
def c_values(c): return values(list(ws.columns)[c])
def r_values(r): return values(list(ws.rows)[r])


def print_set_values_info(type, x):
    len0 = len(x)
    len1 = len(set(x))
    x = set(x)
    x = filter(lambda x: x is not None, x)
    x = list(sorted(x))
    print(f"{type} : {len0} -> {len1}")
    print(x)


data_cols = list(ws.iter_cols(min_col=2))

# print_set_values_info("périodiques", r_values(2))
# print("")
# print_set_values_info("nature_de_l’article", r_values(6))
# print(" ")
# print_set_values_info("oeuvre(s) de Webern concernée(s)", r_values(7))
print_set_values_info("", r_values(26))