 # Périodes
 python3 ../directus/opentheso2directus/opentheso2directus.py \
    --skos_jsonld_file ../temp/opentheso/icono/501.json \
    --skos_jsonld_api "https://opentheso.huma-num.fr/opentheso/api/all/theso?id=th501&format=jsonld" \
    --directus_secret ../secret.catalogue.yaml \
    --directus_url http://bases-iremus.huma-num.fr/directus-catalogue \
    --directus_collection thesaurus_periodes
