from rdflib import DCTERMS, Graph, Namespace, RDF, SKOS, XSD, RDFS, Literal as l, URIRef as u

g = None


def init_graph():
    global g
    g = Graph()

    g.bind("crm", crm_ns)
    g.bind("dcterms", DCTERMS)
    g.bind("lrm", lrmoo_ns)
    g.bind("sdt", sdt_ns)
    g.bind("skos", SKOS)
    g.bind("crmdig", crmdig_ns)
    g.bind("she_ns", sherlock_ns)
    g.bind("she", iremus_ns)
    g.bind("doremus", doremus_ns)
    g.bind("fabio", fabio_ns)


crm_ns = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
crmdig_ns = Namespace("http://www.ics.forth.gr/isl/CRMdig/")
iremus_ns = Namespace("http://data-iremus.huma-num.fr/id/")
lrmoo_ns = Namespace("http://www.cidoc-crm.org/lrmoo/")
sdt_ns = Namespace("http://data-iremus.huma-num.fr/datatypes/")
sherlock_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")
doremus_ns = Namespace("http://data.doremus.org/ontology#")
fabio_ns = Namespace("http://purl.org/spar/fabio#")


def save_graph(file):
    serialization = g.serialize(format="turtle", base="http://data-iremus.huma-num.fr/id/")
    with open(file, "w+") as f:
        f.write(serialization)


a = RDF.type


def crm(x):
    return crm_ns[x]


def crmdig(x):
    return crmdig_ns[x]


def lrm(x):
    return lrmoo_ns[x]


def she(x):
    return iremus_ns[x]


def she_ns(x):
    return sherlock_ns[x]


def dor(x):
    return doremus_ns[x]


def fab(x):
    return fabio_ns[x]


def t(s, p, o):
    g.add((s, p, o))
