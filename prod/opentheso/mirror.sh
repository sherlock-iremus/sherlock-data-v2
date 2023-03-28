SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for th in 391 317
do
    curl "https://opentheso.huma-num.fr/opentheso/api/all/theso?id=th$th&format=turtle" --output "$SCRIPT_DIR/../../caches/opentheso/th$th.ttl"
    scp "$SCRIPT_DIR/../../caches/opentheso/th$th.ttl" tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/opentheso/
    ssh tbottini@data-iremus.huma-num.fr "
    cd sherlock/rdf-data/opentheso ;
    curl -I -X POST -H Content-Type:text/turtle -T th$th.ttl -G http://localhost:3030/iremus/data?graph=http://data-iremus.huma-num.fr/graph/opentheso
    "
done