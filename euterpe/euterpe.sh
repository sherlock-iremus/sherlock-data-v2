# python3 euterpe.py\
#     --step taxonomies\
#     --xlsx_data ./sources/euterpe/euterpe_data.xlsx\
#     --xlsx_taxonomies ./sources/euterpe/euterpe_taxonomies.xlsx\
#     --cache ./caches/euterpe.yaml\
#     --skos_dir ./out/ttl/euterpe/skos
# exa -lHa ./out/ttl/euterpe/skos

python3 euterpe.py\
    --xlsx_data ../sources/euterpe/euterpe_data.xlsx\
    --xlsx_taxonomies ../sources/euterpe/euterpe_taxonomies.xlsx\
    --cache ../caches/euterpe.yaml\
    --skos_dir ../out/ttl/euterpe/skos\
    --directus_secret ../directus/secret.yaml