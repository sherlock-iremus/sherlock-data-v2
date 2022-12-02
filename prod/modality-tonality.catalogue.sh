SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "$SCRIPT_DIR"

scp "$SCRIPT_DIR/../out/ttl/modality-tonality/catalogue.ttl" tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/modality-tonality/

ssh tbottini@data-iremus.huma-num.fr "
cd sherlock/rdf-data/modality-tonality ;
curl -I -X POST -H Content-Type:text/turtle -T catalogue.ttl -G http://localhost:3030/iremus/data?graph=http://data-iremus.huma-num.fr/graph/catalogues
"