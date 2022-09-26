SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ssh-add

# GEN

cd $SCRIPT_DIR/../sherlock-github
./scripts/modality-tonality-mei.sh
./scripts/modality-tonality-analysis.sh
cd -

# LOCAL

declare -a arr=($HOME/Desktop/temp $HOME/Desktop/temp-prod $HOME/Desktop/temp-staging)
for TEMP in "${arr[@]}"
do
  rm -rf $TEMP/rdf-data/modality-tonality/
  mkdir -p $TEMP/rdf-data/modality-tonality/mei
  cp $SCRIPT_DIR/../sherlock-github/data/modality-tonality.ttl $TEMP/rdf-data/modality-tonality/
  cp $SCRIPT_DIR/../sherlock-github/out/ttl/modality-tonality/*.ttl $TEMP/rdf-data/modality-tonality/
  cp $SCRIPT_DIR/../sherlock-github/out/ttl/modality-tonality/mei/*.ttl $TEMP/rdf-data/modality-tonality/mei/
  cp $SCRIPT_DIR/fuseki.post.graph.modality-tonality.sh $TEMP/rdf-data/

  mkdir -p $TEMP/apache/public_html/files/modality-tonality/mei
  cp $SCRIPT_DIR/../sherlock-github/out/mei/modality-tonality/*.mei $TEMP/apache/public_html/files/modality-tonality/mei/
done

# PROD

scp $HOME/Desktop/temp-prod/apache/public_html/files/modality-tonality/mei/*.mei tbottini@data-iremus.huma-num.fr:sherlock/apache/public_html/files/modality-tonality/mei/
scp -r $HOME/Desktop/temp-prod/rdf-data/fuseki.post.graph.modality-tonality.sh tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/
scp -r $HOME/Desktop/temp-prod/rdf-data/modality-tonality/ tbottini@data-iremus.huma-num.fr:sherlock/rdf-data/
ssh tbottini@data-iremus.huma-num.fr "cd sherlock/rdf-data ; ./fuseki.post.graph.modality-tonality.sh"