from rdflib import DCTERMS, Graph, Namespace, RDF, SKOS, XSD, RDFS, Literal as l, URIRef as u
from uuid import UUID
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

def opth(concept, thesaurus_id):
    return u(f"https://opentheso.huma-num.fr/opentheso/?idc={concept}&idt={thesaurus_id}")

def t(s, p, o):
    g.add((s, p, o))

def triples(s, p, o):
    return g.triples((s, p, o))

equipe_mercure_galant_uri = she("684b4c1a-be76-474c-810e-0f5984b47921")
indexation_estampe_analytical_project_uri = she("756aa164-0cde-46ac-bc3a-a0ea83a08e2d")
estampe_e55_uri = she("1317e1ac-50c8-4b97-9eac-c4d902b7da10")
identifiant_mercure_e55_uri = she("92c258a0-1e34-437f-9686-e24322b95305")
identifiant_iiif_e55_uri = she("19073c4a-0ef7-4ac4-a51a-e0810a596773")
cote_bnf_e55_uri = she("15c5867f-f612-4a00-b9f3-17b57e566b8c")
document_gallica_e55_uri = she("e73699b0-9638-4a9a-bfdd-ed1715416f02")
titre_sur_l_image_e55_uri = she("01a07474-f2b9-4afd-bb05-80842ecfb527")
titre_descriptif_forge_e55_uri = she("58fb99dd-1ffb-4e00-a16f-ef6898902301")
titre_peritexte_e55_uri = she("ded9ea93-b400-4550-9aa8-e5aac1d627a0")
thematique_e55_uri = she("f2d9b792-2cfd-4265-a2c5-e0a69ce01536")
revers_medaille_e55_uri = she("226e7258-2b03-4f46-8815-8415095287fb")
avers_medaille_e55_uri = she("74773744-7d22-41f5-b504-61486e1f5057")
invenit_e55_uri = she("4d57ac14-247f-4b0e-90ca-0397b6051b8b")
sculpsit_e55_uri = she("f39eb497-5559-486c-b5ce-6a607f615773")
technique_de_gravure_e55_uri = she("f8914e8f-c1f1-4e1b-90e6-591bcb75ea95")
type_representation_e55_uri = she("0205f283-a73a-47e3-81bf-d0c67501fc22")
personne_associee_e55_uri = she("909049a0-99c3-49a8-b9d6-c4c3517859fb")
lieu_associe_e55_uri = she("413f7969-406b-4be6-a042-09a800197e8f")
lien_gallica_e55_uri = she("f4262bac-f72c-40e2-aa51-ae352da5a35c")
e55_note_bibliographique = she("bffeb363-05ee-449c-a666-bb16eafde48c")

def is_valid_uuid(value):
    try:
        UUID(str(value))
        return True
    except ValueError:
        return False