import argparse
from datetime import datetime
import json
import openpyxl
import pathlib
from pprint import pprint

from sherlockcachemanagement import Cache

parser = argparse.ArgumentParser()
parser.add_argument("--in_xlsx")
args = parser.parse_args()

wb = openpyxl.load_workbook(filename=pathlib.Path(args.in_xlsx))
ws = wb.active

data = []

for c in list(ws.iter_cols(min_col=2, values_only=True)):
    datum = {
        "1 date de parution de l'article": datetime(int(c[0][6:10]), int(c[0][3:5]), int(c[0][0:2])).isoformat()[:10],
        "2 adresse": c[1],
        "3 notes": c[2],
        "4 périodique": c[3],
        "5 type de presse": c[4],
        "6 N° de page": c[5],
        "7 Dans": c[6],
        "8 nature_de_l’article": c[8],
        "9 oeuvre(s) de Webern concernée(s)": c[9],
        "10 n° d'opus correspondant (déduit)": c[10],
        "11 Lieu de la représentation": c[11],
        "12 organisateur (mentionné dans l'article)": c[12],
        "13 organisateur (déduit)": c[13],
        "14 signature de l'auteur": c[15],
        "15 identité de l'auteur (déduite)": c[16],
        "16 Qualité": c[17],
        "17 avis positif": c[19],
        "18 mention d'une réaction positive du public": c[20],
        "19 avis négatif": c[22],
        "20 mention d'une réaction négative du public": c[23],
        "21 avis ambigu": c[25],
        "22 mention d'une réaction ambigüe du public": c[26],
        "23 mention de l'interprète/des interprètes": c[28],
        "24 mention de l'interprète/des interprètes - positive": c[29],
        "25 mention de l'interprète/des interprètes - négative": c[30],
        "26 mention de l'interprète/des interprètes - ambigüe": c[31],
        "27 évocation d'un caractère \"nouveau\"": c[33],
        "28 évocation d'un caractère \"confus\"": c[34],
        "29 champ lexical du mystique / du divin": c[35],
        "30 champ lexical du corps ou de l'animal": c[36],
        "31 emploi de vocabulaire technique": c[37],
        "32 Mention de la brieveté de l'oeuvre": c[39],
        "33 mention de la seconde école de Vienne ": c[41],
        "34 mention d'Arnold Schoenberg": c[42],
        "35 mention d'Alban Berg": c[43],
        "36 mention de l'atonalité": c[44],
        "37 association faite entre Webern et l'Allemagne": c[46],
        "38 mention de la nationalité autrichienne de Webern": c[47],
        "39 avis négatif (simplifié)": c[50],
        "40 mention d'une réaction négative du public (simplifié)": c[51],
        "41 mention interprète positive (simplifié)": c[52],
        "42 évocation d'un caractère \"nouveau\" (simplifié)": c[53],
        "43 évocation d'un caractère \"confus\" (simplifié)": c[54],
        "44 mention de la 2EV (simplifié) ": c[55],
        "45 mention ationalité Webern (simplifié)": c[56]
    }
    data.append(datum)

with open("out.json", "w", encoding='utf-8') as jsonfile:
    json.dump(data, jsonfile, ensure_ascii=False)
