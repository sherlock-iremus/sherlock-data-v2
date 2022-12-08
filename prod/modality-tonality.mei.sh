SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

scp "$SCRIPT_DIR/../out/files/modality-tonality/mei/"*.mei tbottini@data-iremus.huma-num.fr:sherlock/apache/public_html/files/modality-tonality/mei/

ssh tbottini@data-iremus.huma-num.fr "mkdir -p sherlock/rdf-data/modality-tonality/mei"
scp "$SCRIPT_DIR/../out/ttl/modality-tonality/mei/"*.ttl tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/modality-tonality/mei

ssh tbottini@data-iremus.huma-num.fr "
cd sherlock/rdf-data/modality-tonality/mei ;
for meifile in *.ttl
do
    curl -I -X POST -H Content-Type:text/turtle -T \$meifile -G http://localhost:3030/iremus/data?graph=http://data-iremus.huma-num.fr/graph/mei
done
"