from lxml import etree
from rdflib import DCTERMS, RDF, RDFS, Graph, Literal as l, Namespace, URIRef as u, XSD
import sys

mei_ns = {"tei": "http://www.music-encoding.org/ns/mei"}
xml_ns = {"xml": "http://www.w3.org/XML/1998/namespace"}


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return None


def isinteger(value):
    try:
        int(value)
        return True
    except ValueError:
        return None


base = Namespace("http://data-iremus.huma-num.fr/id/")
crm_ns = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
crmdig_ns = Namespace("http://www.ics.forth.gr/isl/CRMdig/")
sherlock_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")
sherlockmei_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlockmei#")


def rdfize(graph, root, score_uuid, score_beats, elements_beats_data, output_ttl_file):
    g = Graph()
    g.bind("crm", crm_ns)
    g.bind("crmdig", crmdig_ns)
    g.bind("dcterms", DCTERMS)
    g.bind("sherlockmei", sherlockmei_ns)

    score_iri = u(score_uuid)

    g.add((score_iri, RDF.type, crmdig_ns["D1_Digital_Object"]))
    g.add((score_iri, RDF.type, crm_ns["E31_Document"]))
    g.add((score_iri, crm_ns["P2_has_type"], u(
        "bf9dce29-8123-4e8e-b24d-0c7f134bbc8e")))  # Partition MEI
    g.add((score_iri, DCTERMS["format"], l("application/vnd.mei+xml")))

    for measureNumber, beats in score_beats.items():
        for beat in beats:
            score_beat_iri = u(f"{score_uuid}-beat-{measureNumber}-{beat}")
            g.add((score_beat_iri, sherlockmei_ns["in_score"], score_iri))
            g.add((score_iri, crm_ns["P106_is_composed_of"], score_beat_iri))
            g.add((score_beat_iri, RDF.type, crmdig_ns["D35_Area"]))
            # the IRI of the concept: "MEI score offset"
            g.add((score_beat_iri, crm_ns["P2_has_type"], u(
                "90a2ae1e-0fbc-4357-ac8a-b4b3f2a06e86")))
            g.add(
                (score_beat_iri, sherlock_ns["has_document_context"], score_iri))

    for k, v in elements_beats_data.items():
        element_id = u(score_uuid + "_" + k)

        g.add((element_id, sherlockmei_ns["duration_beats"], l(
            v["duration_beats"], datatype=XSD.float)))
        g.add((element_id, sherlockmei_ns["from_beat"], l(
            v["from_beat"], datatype=XSD.float)))
        g.add((element_id, sherlockmei_ns["measure_number"], l(
            v["measure_number"], datatype=XSD.integer)))
        g.add((element_id, sherlockmei_ns["to_beat"], l(
            v["to_beat"], datatype=XSD.float)))

        if "beats" in v:
            for beat in v["beats"]:
                # Link the current note to the current score beat
                score_beat_iri = u(
                    f"{score_uuid}-beat-{v['measure_number']}-{beat}")
                g.add(
                    (element_id, sherlockmei_ns["contains_beat"], score_beat_iri))
                g.add((score_beat_iri, crm_ns["P2_has_type"], u(
                    "90a2ae1e-0fbc-4357-ac8a-b4b3f2a06e86")))
                g.add(
                    (score_beat_iri, sherlock_ns["has_document_context"], score_iri))

                # Create an annotation anchor for each beat which occurs within the note duration
                element_beat_anchor_iri = u(
                    f"{score_uuid}-{k}-{v['measure_number']}-{beat}")
                g.add(
                    (element_id, sherlockmei_ns["has_beat_anchor"], element_beat_anchor_iri))
                g.add((element_beat_anchor_iri, crm_ns['P2_has_type'], u(
                    "689e148d-a97d-45b4-898d-c395a24884df")))  # the IRI of the concept: "Note offset anchor"
                g.add((element_beat_anchor_iri,
                      sherlock_ns["has_document_context"], score_iri))

    # We census everything which has a xml:id
    for e in root.xpath("//*"):
        xmlida = "{" + xml_ns["xml"] + "}id"
        if xmlida in e.attrib:
            element_id = u(score_uuid + "_" + e.attrib[xmlida])

            g.add((element_id, sherlockmei_ns["in_score"], score_iri))

            g.add((element_id, RDF.type, crmdig_ns["D35_Area"]))

            if e.text and e.text.strip() and e.text.strip() != "None":
                g.add((element_id, sherlockmei_ns["text"], l(e.text.strip())))

            g.add((element_id, sherlockmei_ns["element"], l(
                etree.QName(e.tag).localname)))
            for a in e.attrib:
                if a != xmlida:
                    o = None
                    if isinteger(e.attrib[a]):
                        o = l(int(e.attrib[a]), datatype=XSD.integer)
                    elif isfloat(e.attrib[a]):
                        o = l(float(e.attrib[a]), datatype=XSD.float)
                    else:
                        o = l(e.attrib[a])
                    g.add((element_id, sherlockmei_ns[a], o))

            if etree.QName(e.tag).localname == "note":
                g.add((element_id, crm_ns["P2_has_type"],
                      base["d2a536eb-4a95-484f-b13d-f597ac8ea2fd"]))
                g.add(
                    (element_id, sherlock_ns["has_document_context"], score_iri))

            # xml:id E42
            e42_id = u(score_uuid + "_" + e.attrib[xmlida] + "_E42")
            g.add((element_id, crm_ns["P1_is_identified_by"], e42_id))
            g.add((e42_id, RDF.type, crm_ns["E42_Identifier"]))
            g.add((e42_id, crm_ns["P190_has_symbolic_content"], l(e.attrib[xmlida])))
            g.add((e42_id, crm_ns['P2_has_type'], u(
                "db425957-e8bc-41d7-8a6b-d1b935cfe48d")))  # xml:id

            # P106 parent element
            if e.getparent() is not None:
                parent_element_id = score_uuid + \
                    "_" + e.getparent().attrib[xmlida]
                g.add((u(parent_element_id),
                      crm_ns["P106_is_composed_of"], u(element_id)))
            else:
                g.add(
                    (score_iri, crm_ns["P106_is_composed_of"], u(element_id)))

    # That's all folks
    serialization = g.serialize(
        format='turtle', base="http://data-iremus.huma-num.fr/id/")
    with open(output_ttl_file, "w+") as f:
        f.write(serialization)
