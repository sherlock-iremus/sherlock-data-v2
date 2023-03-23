SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

scp "$SCRIPT_DIR/../../ns/sherlock.ns.ttl" tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/sherlock

ssh tbottini@data-iremus.huma-num.fr "
cd sherlock/rdf-data/sherlock ;
curl -I -X POST -H Content-Type:text/turtle -T sherlock.ns.ttl -G http://localhost:3030/iremus/data?graph=http://data-iremus.huma-num.fr/graph/sherlock
"