SCRIPT=`realpath $0`
DIR=`dirname $SCRIPT`

scp $DIR/../../out/ttl/rar/personnes.ttl tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/rar

ssh tbottini@data-iremus.huma-num.fr "
cd sherlock/rdf-data/rar ;
curl -X POST --data-urlencode \"update=CLEAR GRAPH <http://data-iremus.huma-num.fr/graph/rar-personnes>\" http://localhost:3030/iremus/update
curl -I -X POST -H Content-Type:text/turtle -T personnes.ttl -G http://localhost:3030/iremus/data?graph=http://data-iremus.huma-num.fr/graph/rar-personnes
"