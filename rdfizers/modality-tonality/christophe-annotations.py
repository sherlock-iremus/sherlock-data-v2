import argparse
import rdflib
import yaml

parser = argparse.ArgumentParser()
parser.add_argument("--owl")
args = parser.parse_args()

g = rdflib.Graph()
g.parse(args.owl, format='xml')

for s, p, o in g:
    print(s, p, o)
