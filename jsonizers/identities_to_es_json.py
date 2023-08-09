from pprint import pprint
import requests
import json
import urllib
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--json")
args = parser.parse_args()


print("[WARN] : This is a WIP script, and only user data are indexed")
print("[WARN] : This is a WIP script, request should be retrieved from sherlock-sparql-queries repository")

print("[INFO] : Fetching all users uri")

fetch_users_query = """

PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
select ?user
where {
 	graph ?g {
		?user rdf:type crm:E21_Person.
    	?user crm:P1_is_identified_by ?identifier.
    	?identifier rdf:type crm:E42_Identifier.
    	?identifier crm:P2_has_type <http://data-iremus.huma-num.fr/id/d7ef2583-ff31-4913-9ed3-bc3a1c664b21>.
    	?identifier crm:P190_has_symbolic_content ?orcid	
  	}
}

"""

r = requests.get("http://data-iremus.huma-num.fr/sparql?query=" + urllib.parse.quote((fetch_users_query)))
result = json.loads(r.text)


print("[INFO] : Fetching all user's identities")

elasticsearch_list = []
for i in result["results"]["bindings"]:
    fetch_identity_query = f"""

  
    PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT *
    WHERE {{
    GRAPH ?g {{
        {{
        VALUES ?p {{ crm:P1_is_identified_by crm:P102_has_title dcterms:title rdfs:label skos:prefLabel skos:altLabel crm:P190_has_symbolic_content }}
        <{i["user"]["value"]}> ?p ?label .
        FILTER(isLiteral(?label)) .
        }}
        
    UNION
    {{
    VALUES ?p {{ crm:P1_is_identified_by crm:P102_has_title }}
    <{i["user"]["value"]}> ?p ?r .
    GRAPH ?r_types__g {{
        VALUES ?r_type {{ crm:E35_Title crm:E41_Appellation crm:E42_Identifier }}
        ?r rdf:type ?r_type .
        ?r crm:P190_has_symbolic_content ?label .
    }}
    OPTIONAL {{
        GRAPH ?r_types_types__graph {{
        ?r crm:P2_has_type ?r_type_type .
        GRAPH ?r_types_types_label_graph {{
            ?r_type_type crm:P1_is_identified_by ?r_type_type__label .
        }}
        }}
    }}
    }}

        
    UNION {{
    GRAPH ?e32_e55__g {{
        ?e32 crm:P71_lists <{i["user"]["value"]}> .
    }}
    OPTIONAL {{
        GRAPH ?e32__g {{
        ?e32 crm:P1_is_identified_by ?e32__label .
        }}
    }}
    }}
        
    UNION {{
    VALUES ?p {{ crm:P2_has_type rdf:type }}
    <{i["user"]["value"]}> ?p ?r .
    OPTIONAL {{
        GRAPH ?r_types__g {{
        VALUES ?r_type {{ crm:E55_Type }} .
        ?r rdf:type ?r_type .
        ?r crm:P1_is_identified_by ?label .
        ?type_e32 crm:P71_lists ?r .
        FILTER(isLiteral(?label)) .
        OPTIONAL {{
            GRAPH ?type_e32__g {{
            ?type_e32 crm:P1_is_identified_by ?type_e32__label .
            }}
        }}
        }}
    }}
    }}

        
    UNION {{
        SELECT (COUNT(?r_out) AS ?c_out) ?lr
        WHERE {{ GRAPH ?g_out {{ <{i["user"]["value"]}> ?p_out ?r_out }} }}
        GROUP BY ?c_out ?lr
    }}
    UNION {{
        SELECT (COUNT(*) AS ?c_in) ?lr
        WHERE {{ GRAPH ?g_in {{ ?r_in ?p_in <{i["user"]["value"]}> }} }}
        GROUP BY ?c_in ?lr
    }}
    }}
    }}
    """
    r = requests.get("http://data-iremus.huma-num.fr/sparql?query=" + urllib.parse.quote((fetch_identity_query)))
    
    result = json.loads(r.text)
    
    elasticsearch_list.append({
        "index": {
            "_index": "customer",
            "_id": i["user"]["value"]
        },
    })

    elasticsearch_list.append({
        "identity": result["results"]["bindings"]
    })

# Writing elasticsearch formatted json
with open(args.json, "w+") as f:
    for element in elasticsearch_list: 
        element_json = json.dumps(element, indent=None)
        f.write(element_json)
        f.write("\n")