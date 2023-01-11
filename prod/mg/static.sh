SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

scp "$SCRIPT_DIR/../data/mercure-galant.ttl" tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/mercure-galant/

ssh tbottini@data-iremus.huma-num.fr "
cd sherlock/rdf-data/mercure-galant ;
curl -I -X POST -H Content-Type:text/turtle -T mercure-galant.ttl -G http://localhost:3030/iremus/data?graph=http://data-iremus.huma-num.fr/graph/mergure-galant
"