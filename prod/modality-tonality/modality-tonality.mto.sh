SCRIPT=`realpath $0`
DIR=`dirname $SCRIPT`

ssh tbottini@data-iremus.huma-num.fr "mkdir -p sherlock/rdf-data/modality-tonality/historicalModels"
scp $DIR/../../in/modal-tonal-ontology/historicalModels/*.owl tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/modality-tonality/historicalModels
scp $DIR/../../in/modal-tonal-ontology/historicalModels/*.rdf tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/modality-tonality/historicalModels

ssh tbottini@data-iremus.huma-num.fr "
cd sherlock/rdf-data/modality-tonality/historicalModels ;
for f in *.*
do
    curl -I -X POST -H Content-Type:application/rdf+xml -T \$f -G http://localhost:3030/iremus/data?graph=http://data-iremus.huma-num.fr/graph/modality-tonality-ontology
done
"