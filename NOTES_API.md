# POST /13

P141 peut être de trois types :
1) Un littéral.
2) Une URL.
3) Une nouvelle entité qu'il va falloit créer, et donc décrire a minima dans le payload (le service lui affectera en plus dcterms:creator & dcterms:created, en lien avec le P14 et le dcterms:created de la E13).

Exemple avec une Entité analytique :

    …
    "P140": […],
    "P141": {
        "rdf:type": [
            <http://…/E28_Conceptual_Object>
        ],
        "crm:P2_has_type": [
            <http://data-iremus.huma-num.fr/id/<UUID du E55 Entité Analytique>>
        ]
    },
    "P177": …,
    …

# Scénario d'indexation d'un nouveau fragment d'image

3 appels d'API :

1) Création du sous E36 (POST /E36/fragment). Ne génère par d'E13, mais met des dcterms:creator/created sur le fragment.
2) Récupération de l'URL du sous E36 et création du E42 via une E13 avec P141 entité (POST /E13 avec P141 de type Entité).
3) Récupération de l'URL du sous E36 et création d'une E13 pour l'indexation (POST /E13 avec P141 de type URL).

Pour la création du E42 :

    {
        "rdf:type": [
            <http://…/E42_Identifier>
        ],
        "crm:P2_has_type": [
            <http://data-iremus.huma-num.fr/id/<UUID du E55 « Identifiant IIIF »>>
        ],
        "crm:P190_has_symbolic_content": "http://iiif…"
    }

# Création de fragment

POST /E90/fragment

{
    "parent": <http://data-iremus.huma-num.fr/id/79822e2c-5350-4f14-92b3-bc78f17fda09>,
    "crm:P2_has_type": [<>, <>…]
}

Le rdf:type du parent est recherché dans la base, et réutilisé sur l'enfant.
