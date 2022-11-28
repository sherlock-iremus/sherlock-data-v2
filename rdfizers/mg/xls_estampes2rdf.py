from sherlockcachemanagement import Cache
import argparse
import sys
import os
from pprint import pprint
from slugify import slugify
import requests
import yaml
import json
import re 

# Regex

pattern_article = re.compile("MG-[0-9]{4}-[0-9]{2}[a-zA-Z]?_?([0-9]{3})?")
pattern_livraison = re.compile("[0-9]{4}-[0-9]{2}[a-zA-Z]?")
pattern_lieu_opentheso = re.compile("^[0-9]{1,6}$")

# Helpers
sys.path.append(os.path.abspath(os.path.join('rdfizers/', '')))
from helpers_rdf import *
sys.path.append(os.path.abspath(os.path.join('python_packages/helpers_excel', '')))
from helpers_excel import *
sys.path.append(os.path.abspath(os.path.join('directus/', '')))
from helpers_api import graphql_query

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--ttl")
parser.add_argument("--xlsx")
parser.add_argument("--opentheso_id") # opth Thesaurus id ?
parser.add_argument("--cache")
parser.add_argument("--cache_tei") 
args = parser.parse_args()

# Caches
cache = Cache(args.cache)
if args.cache_tei:
    cache_tei = Cache(args.cache_tei)

# Initialisation du graphe
init_graph()

print("Récupération des personnes via l'API directus...")

personnes_directus = graphql_query("""
query {
  personnes(limit: -1) {
    id
  } 
}""")

print("Récupération des lieux via l'API directus...")

lieux_directus = graphql_query("""
query {
  lieux(limit: -1) {
    id
    opentheso_id
  } 
}""")

def make_E13(path, subject, predicate, object): # - global + return E13 uri
    e13 = she(cache.get_uuid(path, True))
    t(e13, a, crm("E13_Attribute_Assignement"))
    t(e13, crm("P14_carried_out_by"), equipe_mercure_galant_uri)
    t(e13, crm("P140_assigned_attribute_to"), subject)
    t(e13, crm("P141_assigned"), object)
    t(e13, crm("P177_assigned_property_of_type"), predicate)

    return e13

#######################################################################################################
# Traitement des estampes
#######################################################################################################


rows = get_xlsx_rows_as_dicts(args.xlsx)

concepts_used = []
personnes_used = []
lieux_used = []

for row in rows:
    if row["ID estampe"] is not None:
        id = row["ID estampe"]

        #region E36: Estampe
        estampe = she(cache.get_uuid(["estampes", id, "E36", "uuid"], True))
        t(estampe, a, crm("E36_Visual_Item"))
        t(corpus_estampes_uri, crm("P106_is_composed_of"), estampe)
        t(estampe, crm("P2_has_type"), estampe_e55_uri)
        #endregion

        #region E42: Identifiant Mercure Galant de l'estampe
        E42_uuid = she(cache.get_uuid(["estampes", id, "E42", "uuid"], True))
        t(E42_uuid, a, crm("E42_Identifier"))
        t(E42_uuid, crm("P2_has_type"), identifiant_mercure_e55_uri)
        t(E42_uuid, crm("P190_has_symbolic_content"), l(id))
        t(estampe, crm("P1_is_identified_by"), E42_uuid)
        #endregion

        #region E42: Identifiant IIIF de l'estampe
        E42_iiif = she(cache.get_uuid(["estampes", id, "E42_IIIF", "uuid"], True))
        t(E42_iiif, a, crm("E42_Identifier"))
        t(E42_iiif, crm("P2_has_type"), identifiant_iiif_e55_uri)
        t(E42_iiif, crm("P190_has_symbolic_content"), u(f"https://ceres.huma-num.fr/iiif/3/mercure-galant-estampes--{id.replace(' ', '%20')}/full/max/0/default.jpg"))
        t(estampe, crm("P1_is_identified_by"), E42_iiif)
        #endregion
        
        #region E42: Provenance cliché (identifiant BnF)
        if row["Provenance cliché"]:
            E42_provenance = she(cache.get_uuid(["estampes", id, "E42_provenance", "uuid"], True))
            t(E42_provenance, a, crm("E42_Identifier"))
            t(E42_provenance, crm("P2_has_type"), identifiant_bnf_e55_uri)
            t(E42_provenance, crm("P190_has_symbolic_content"), l(row["Provenance cliché"]))
            t(estampe, crm("P1_is_identified_by"), E42_provenance)
        #endregion
        
        #region F2: Rattachement à la livraison ou à l'article OBVIL
        if row["ID article OBVIL"]:
            match = pattern_article.search(row["ID article OBVIL"])
            if match:
                try:
                    id_article = match.group(0)[3:]
                    id_livraison = pattern_livraison.search(id_article).group(0)
                    article_F2_original = she(cache_tei.get_uuid(["Corpus", "Livraisons", id_livraison, "Expression originale", "Articles", id_article, "F2"]))
                    t(article_F2_original, crm("P106_is_composed_of"), estampe)
                except:
                    print(id_article)
            else:
                try:
                    id_livraison = pattern_livraison.search(row["ID estampe"]).group(0)
                    livraison_F2_TEI = she(cache_tei.get_uuid(["Corpus", "Livraisons", id_livraison, "Expression TEI", "F2"]))
                    t(livraison_F2_TEI, crm("P106_is_composed_of"), estampe)
                except: 
                    print(id_livraison)
        #endregion

        #region F2: Article annexe à la gravure
        if row["ID OBVIL article lié"]:
            try: 
                match = pattern_article.search(row["ID article OBVIL"])
                if match:
                    id_article = match.group(0)[3:]
                    id_livraison = pattern_livraison.search(id_article).group(0)
                    article_F2_TEI = she(cache_tei.get_uuid(["Corpus", "Livraisons", id_livraison, "Expression TEI", "Articles", id_article, "F2"]))
                    e13 = make_E13(["estampes", id, "E36", "seeAlso", "E13"], estampe, RDFS.seeAlso, article_F2_TEI)
                    if row["Commentaire ID article lié OBVIL"]:
                        t(e13, crm("P3_has_note"), l(row["Commentaire ID article lié OBVIL"]))
            except:
                print(id_article)
        #endregion
        
        #region seeAlso: Lien vers le texte en ligne
        if row["Lien vers le texte [ou l'image] en ligne"]:
            liens = row["Lien vers le texte [ou l'image] en ligne"].split(";")
            for lien in liens:
                lien = lien.strip()
                if lien == "" or lien == " ":
                    continue
                if lien.startswith("https://gallica.bnf.fr/"):
                    lien = u(lien)
                    t(lien, crm("P2_has_type"), document_gallica_e55_uri)
                    make_E13(["estampes", id, "E36", "lien vers le texte en ligne", lien, "E13"], estampe, RDFS.seeAlso, lien)
                else:
                    make_E13(["estampes", id, "E36", "note sur le texte en ligne", lien, "E13"], estampe, RDFS.seeAlso, l(lien))
        #endregion
        
        #region E13: Titre sur l'image
        if row["Titre sur l'image"]:
            titre = row["Titre sur l'image"].replace("[", "").replace("]", "").replace("*", "")
            make_E13(["estampes", id, "E36", "titre sur l'image"], estampe, titre_sur_l_image_e55_uri, l(titre))
        #endregion
        
        #region E13: Titre descriptif/forgé 
        if row["[titre descriptif forgé]* (Avec Maj - accentuées]"]:
            titre = row["[titre descriptif forgé]* (Avec Maj - accentuées]"].replace("[", "").replace("]", "").replace("*", "")
            make_E13(["estampes", id, "E36", "titre forgé"], estampe, titre_descriptif_forge_e55_uri, l(titre))
        #endregion
        
        #region E13: Titre dans le péritexte
        if row["[Titre dans le péritexte: Avis, article…]"]:
            titre = row["[Titre dans le péritexte: Avis, article…]"].replace("[", "").replace("]", "").replace("*", "")
            make_E13(["estampes", id, "E36", "titre péritexte"], estampe, she(titre_peritexte_e55_uri), l(titre))
        #endregion
        
        #region E13: Lieux associés
        if row["Lieux/Etats associés"]:
            lieux = row["Lieux/Etats associés"]
            for lieu_label in lieux.split(";"):
                lieu = lieu_label.lstrip().split(' ')[0]
                if (lieu == ''):
                    continue
                match = pattern_lieu_opentheso.search(lieu)
                # Transformer ID opentheso en uuid directus
                if (match):
                    lieu = next((x["id"] for x in lieux_directus["data"]["lieux"] if x["opentheso_id"] == int(match.group(0))), None)
                if (not lieu):
                    print(f"Aucun lieu trouvé dans Directus pour : {lieu_label}")
                    continue
                make_E13(["collection", id, "E36", "lieux associés", lieu], estampe, lieu_associe_e55_uri, she(lieu))
                lieux_used.append(lieu)
        #endregion
        
        #region E13-P138: Lieux représentés
        if row["Lieux représentés"]:
            lieux = row["Lieux représentés"]
            for lieu_label in lieux.split(";"):
                # Les lieux sont indexés de la manière suivante : <id> <label> ; <id> <label>
                lieu = lieu_label.lstrip().split(' ')[0]
                if (lieu == ''):
                    continue
                match = pattern_lieu_opentheso.search(lieu)
                # Transformer ID opentheso en uuid directus
                if (match):
                    lieu = next((x["id"] for x in lieux_directus["data"]["lieux"] if x["opentheso_id"] == int(lieu)), None)
                if (not lieu):
                    print(f"Aucun lieu trouvé dans Directus pour : {lieu_label}")
                    continue
                # Zone de l'image comportant la représentation du lieu (E13)
                estampe_zone_img = she(cache.get_uuid(["estampes", id, "E36", "lieux", lieu, "zone de l'objet (E36)", "uuid"], True))
                t(estampe_zone_img, a, crm("E36_Visual_Item"))
                t(estampe_zone_img, she_ns("is_fragment_of"), estampe)
                make_E13(["estampes", id, "E36", "lieux", lieu, "zone de l'objet (E36)", "E13"], estampe, crm("P106_is_composed_of"), estampe_zone_img)
                make_E13(["estampes", id, "E36", "lieux", lieu, "zone de l'objet (E36)", "lieu représenté"], estampe_zone_img, crm("P138_represents"), she(lieu))
                lieux_used.append(lieu)
        #endregion
        
        #region E13: Thématique de la gravure
        if row["Thématique [Avec Maj et au pl.]"]:
            thématiques = row["Thématique [Avec Maj et au pl.]"].split(";")
            for thématique in thématiques:
                thématique = thématique.strip().replace("’", "'")
                if thématique == "" or thématique == " ":
                    continue
                thématique_uri = opth(slugify(thématique), args.opentheso_id)
                concepts_used.append(thématique_uri)
                make_E13(["collection", id, "E36", "thématique", thématique, "E13"], estampe, thematique_e55_uri, thématique_uri)
        #endregion
        
        #region E13-P138: Objet représenté
        if row["Objets représentés"]:
            objets = row["Objets représentés"].split(";")
            for objet in objets:
                objet = objet.strip().replace("’", "'")
                if objet == "" or objet == " ":
                    continue

                # Zone de l'image représentant l'objet (E13)
                estampe_zone_img = she(
                    cache.get_uuid(["estampes", id, "E36", "objets", objet, "zone de l'objet (E36)", "uuid"], True))
                t(estampe_zone_img, a, crm("E36_Visual_Item"))
                t(estampe_zone_img, she_ns("is_fragment_of"), estampe)
                make_E13(["estampes", id, "E36", "objets", objet, "zone de l'objet (E36)", "E13"], estampe, crm("P106_is_composed_of"), estampe_zone_img)
                objet_uri = opth(slugify(objet), args.opentheso_id)
                concepts_used.append(objet_uri)
                make_E13(["estampes", id, "E36", "objets", objet, "zone de l'objet (E36)", "représentation de l'objet (E13)"], estampe_zone_img, crm("P138_represents"), objet_uri)

                # Si l'objet est une médaille et comporte une inscription
                if objet == "médaille" and row["Médailles: avers"] or row["Médailles: revers"]:
                    if row["Médailles: avers"]:
                        médaille_zone_inscrip = she(cache.get_uuid(
                            ["collection", id, "E36", "objets", objet, "zone de l'objet (E36)", "zone d'inscription (médaille)",
                             "avers", "uuid"], True))
                        t(médaille_zone_inscrip, a, crm("E36_Visual_Item"))
                        t(médaille_zone_inscrip, she_ns("is_fragment_of"), estampe)
                        make_E13(["collection", id, "E36", "objets", objet, "zone de l'objet (E36)",
                                  "zone d'inscription (médaille)", "avers", "E13"], estampe_zone_img, crm("P106_is_composed_of"), médaille_zone_inscrip)
                        médaille_inscrip = she(
                            cache.get_uuid(
                                ["collection", id, "E36", "objets", objet, "zone de l'objet (E36)", "zone d'inscription (médaille)",
                                 "avers", "inscription", "uuid"], True))
                        t(médaille_inscrip, a, crm("E33_Linguistic_Object"))
                        make_E13(["collection", id, "E36", "objets", objet, "zone de l'objet (E36)", "zone d'inscription (médaille)",
                                  "avers", "inscription", "E13"], médaille_zone_inscrip, crm("P165_incorporates"), médaille_inscrip)
                        t(e13, she_ns("sheP_position_du_texte_par_rapport_à_la_médaille"), inscription_avers_medaille_e55_uri)
                        # Contenu de l'inscription
                        make_E13(["collection", id, "E36", "objets", objet, "zone de l'objet (E36)",
                                  "inscription",
                                  "avers", "inscription", "contenu (E13)"], médaille_inscrip, crm("P190_has_symbolic_content"), l(row["Médailles: avers"]))

                    # Si la médaille comporte une inscription sur son revers (E13)
                    if row["Médailles: revers"]:
                        médaille_zone_inscrip = she(cache.get_uuid(
                            ["collection", id, "E36", "objets", objet, "zone de l'objet (E36)", "zone d'inscription (médaille)",
                             "revers", "uuid"], True))
                        t(médaille_zone_inscrip, a, crm("E36_Visual_Item"))
                        t(médaille_zone_inscrip, she_ns("is_fragment_of"), estampe)
                        make_E13(["collection", id, "E36", "objets", objet, "zone de l'objet (E36)",
                                  "zone d'inscription (médaille)", "revers", "E13"], estampe_zone_img, crm("P106_is_composed_of"), médaille_zone_inscrip)
                        médaille_inscrip = she(cache.get_uuid(
                            ["collection", id, "E36", "objets", objet, "zone de l'objet (E36)", "zone d'inscription (médaille)",
                             "revers", "inscription", "uuid"], True))
                        t(médaille_inscrip, a, crm("E33_Linguistic_Object"))
                        make_E13(["collection", id, "E36", "objets", objet, "zone de l'objet (E36)", "zone d'inscription (médaille)",
                                  "revers", "inscription", "E13"], médaille_zone_inscrip, crm("P165_incorporates"), médaille_inscrip)
                        t(e13, she_ns("sheP_position_du_texte_par_rapport_à_la_médaille"), inscription_revers_medaille_e55_uri)
                        # Contenu de l'inscription
                        make_E13(["collection", id, "E36", "objets", objet, "zone de l'objet (E36)", "zone d'inscription (médaille)",
                                  "revers", "inscription", "contenu (E13)"], médaille_inscrip, crm("P190_has_symbolic_content"), l(row["Médailles: revers"]))
        #endregion
        
        #region E13-P138: Personnes représentées
        if row["Personnes représentées"]:
            personnes = row["Personnes représentées"].split(";")
            for personne in personnes:
                personne = personne.strip().replace("’", "'")
                if personne == "" or personne == " ":
                    continue
                personnes_used.append(personne)
                make_E13(["collection", id, "E36", "personnes", personne, "zone de l'objet (E36)", "personne représentée"], estampe_zone_img, crm("P138_represents"), she(personne))
        #endregion
        
        #region E13: Personnes associées
        if row["Personnes associées"]:
            personnes = row["Personnes associées"].split(";")
            for personne in personnes:
                personne = personne.strip().replace("’", "'")
                if personne == "" or personne == " ":
                    continue
                personnes_used.append(personne)
                make_E13(["collection", id, "E36", "personnes associées", personne], estampe, personne_associee_e55_uri, she(personne))
        #endregion
        
        #region E12: Production de l'estampe
        if row["Inventeur (du sujet) ['Invenit' ou 'Pinxit' ou 'Delineavit']"] or row[
                "Graveur ['Sculpsit' ou 'Incidit' ou 'fecit']"]:
            estampe_E12 = she(cache.get_uuid(["estampes", id, "E36", "E12", "uuid"], True))
            t(estampe_E12, a, crm("E12_Production"))
            t(estampe_E12, crm("P108_has_produced"), estampe)
        #endregion
        
        #region sous-E12: Invenit (concepteur de l'estampe)
        if row["Inventeur (du sujet) ['Invenit' ou 'Pinxit' ou 'Delineavit']"]:
            estampe_invenit = she(cache.get_uuid(["estampes", id, "E36", "E12", "invenit", "uuid"], True))
            t(estampe_invenit, a, crm("E12_Production"))
            t(estampe_invenit, crm("P2_has_type"), invenit_e55_uri)
            t(estampe_E12, crm("P9_consists_of"), estampe_invenit)

            # Lien entre conception de l'estampe et concepteur (E13)
            estampe_invenit_auteur = she(cache.get_uuid(["estampes", id, "E36", "E12", "invenit", "auteur"], True))
            t(estampe_invenit_auteur, a, crm("E21_Person"))
            t(estampe_invenit_auteur, RDFS.label,
              l(row["Inventeur (du sujet) ['Invenit' ou 'Pinxit' ou 'Delineavit']"]))
            make_E13(["estampes", id, "E36", "E12", "invenit", "E13"], estampe_invenit, crm("P14_carried_out_by"), estampe_invenit_auteur)
        #endregion
        
        #region sous-E12: Sculpsit (graveur de l'estampe)
        if row["Graveur ['Sculpsit' ou 'Incidit' ou 'fecit']"]:
            estampe_sculpsit = she(cache.get_uuid(["estampes", id, "E36", "E12", "sculpsit", "uuid"], True))
            t(estampe_sculpsit, a, crm("E12_Production"))
            t(estampe_sculpsit, crm("P2_has_type"), sculpsit_e55_uri)
            t(estampe_E12, crm("P9_consists_of"), estampe_sculpsit)

            # Lien entre la gravure de l'estampe et son graveur (E13)
            estampe_sculpsit_auteur = she(cache.get_uuid(["estampes", id, "E36", "E12", "sculpsit", "auteur"], True))
            t(estampe_sculpsit_auteur, a, crm("E21_Person"))
            t(estampe_sculpsit_auteur, RDFS.label, l(row["Graveur ['Sculpsit' ou 'Incidit' ou 'fecit']"]))
            make_E13(["estampes", id, "E36", "E12", "sculpsit", "E13"], estampe_sculpsit, crm("P14_carried_out_by"), estampe_sculpsit_auteur)
        #endregion
        
        #region E13: Type de représentation
        if row["Types de représentation"]:
            types = row["Types de représentation"].split(";")
            for x in types:
                if x == "" or x == " ":
                    continue
                type_uri = opth(slugify(x.strip().replace("’", "'")), args.opentheso_id)
                concepts_used.append(type_uri)
                make_E13(["estampes", id, "E36", "types de représentation", x], estampe, type_representation_e55_uri, type_uri)
        #endregion
  
        #region E13: Technique de gravure
        if row["Technique de la gravure"]:
            techniques = row["Technique de la gravure"].split(",")
            for x in techniques:
                if x == "" or x == " ":
                    continue
                technique_uri = opth(slugify(x.strip().replace("’", "'")), args.opentheso_id)
                concepts_used.append(technique_uri)
                make_E13(["estampes", id, "E36", "technique de la gravure", x], estampe, technique_de_gravure_e55_uri, technique_uri)
        #endregion
        
        #region E13: Format
        if row["Format (H x L en cm)"]:
            format = row["Format (H x L en cm)"].split("x")
            hauteur_uri = she(cache.get_uuid(["estampes", id, "E36", "E54 hauteur", "uuid"], True))
            t(hauteur_uri, a, crm("E54_Dimension"))
            t(hauteur_uri, crm("P2_has_type"), u("http://vocab.getty.edu/page/aat/300055644"))
            t(hauteur_uri, crm("P90_has_value"), l(format[0].strip().replace("’", "'")))
            t(hauteur_uri, crm("P91_has_unit"), l("cm"))
            make_E13(["estampes", id, "E36", "hauteur", "E13", "uuid"], estampe, crm("P43_has_dimension"), hauteur_uri)
            largeur_uri = she(cache.get_uuid(["estampes", id, "E36", "E54 largeur", "uuid"], True))
            t(largeur_uri, a, crm("E54_Dimension"))
            t(largeur_uri, crm("P2_has_type"), u("http://vocab.getty.edu/page/aat/300055647"))
            t(largeur_uri, crm("P90_has_value"), l(format[1].replace("cm", "").strip().replace("’", "'")))
            t(largeur_uri, crm("P91_has_unit"), l("cm"))
            make_E13(["estampes", id, "E36", "hauteur", "E13", "uuid"], estampe, crm("P43_has_dimension"), hauteur_uri)
        #endregion
        
        #region E13-P70: Bibliographie relative à l'estampe
        if row["BIBLIO [y compris liens] relative à la gravure et aux artistes"]:
            biblio = she(cache.get_uuid(["estampes", id, "E36", "bibliographie", "uuid"], True))
            t(biblio, a, crm("E31_Document"))
            t(biblio, RDFS.label, l(row["BIBLIO [y compris liens] relative à la gravure et aux artistes"]))
            make_E13(["estampes", id, "E36", "bibliographie", "E13"], estampe, crm("P70_documents"), biblio)
        #endregion

###########################################################################################################
# Tests concordance indexation
###########################################################################################################

print("Test de concordance des indexations...")

# VOCABULAIRE

print("Récupération du vocabulaire d'indexation via l'API opentheso...")
r = requests.get(f"https://opentheso.huma-num.fr/opentheso/api/all/theso?id={args.opentheso_id}&format=jsonld", stream=True)
skos_data = json.loads(r.text)
concept_uris_list = [concept["@id"] for concept in skos_data]

for concept in concepts_used:
    if (str(concept) not in concept_uris_list):
        print(f"Le concept {concept} ne fait pas partie du vocabulaire.")

# PERSONNES

for personne_uuid in personnes_used:
    if (not next((x for x in personnes_directus["data"]["personnes"] if x["id"] == personne_uuid), None)):
        print(f"L'uuid {personne_uuid} n'existe pas. Regénérer cache personnes ?")

# LIEUX

for lieu_uuid in lieux_used:
    if (not next((x for x in lieux_directus["data"]["lieux"] if x["id"] == lieu_uuid), None)):
        print(f"L'uuid {lieu_uuid} n'existe pas. Regénérer cache lieux ?")

###########################################################################################################
# Création du graphe et du cache
###########################################################################################################

cache.bye()
save_graph(args.ttl)

# TODO ROADBLOACKED INSTITUTIONS : en attente de la saisie des institutions dans directus (stagiaire printemps 2023) 
# TODO AUTRES LIENS EXTERNES : que fait-on de cette colonne fourre-tout ? P3 ?
# TODO ID ARTICLE LIÉ : ne sont pas dans le cache tei.
# TODO sherlock data constants