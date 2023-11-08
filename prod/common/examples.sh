#!/bin/bash
SCRIPT_DIR="$(cd -P "$(dirname "$0")" && pwd)"

scp "$SCRIPT_DIR/../../data/"examples.ttl tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/sherlock

ssh tbottini@data-iremus.huma-num.fr "
cd sherlock/rdf-data/sherlock ;
curl -I -X POST -H Content-Type:text/turtle -T examples.ttl -G http://localhost:3030/iremus/data?graph=http://data-iremus.huma-num.fr/graph/examples
"