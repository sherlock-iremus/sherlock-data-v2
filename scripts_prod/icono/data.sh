SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

scp "$SCRIPT_DIR/../../data/icono.ttl" tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/icono/

ssh tbottini@data-iremus.huma-num.fr "
cd sherlock/rdf-data/icono ;
curl -I -X POST -H Content-Type:text/turtle -T icono.ttl -G http://localhost:3030/iremus/data?graph=http://data-iremus.huma-num.fr/graph/sherlock-data
"