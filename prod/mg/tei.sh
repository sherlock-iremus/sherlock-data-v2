SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ARTICLES_DIR=/home/tbottini/sherlock/apache/public_html/files/mercure-galant/articles
LIVRAISONS_DIR=/home/tbottini/sherlock/apache/public_html/files/mercure-galant/livraisons
ssh tbottini@data-iremus.huma-num.fr "mkdir -p $ARTICLES_DIR"
for f in $SCRIPT_DIR/../../out/files/mg/mei/articles/*
do
    scp $f tbottini@data-iremus.huma-num.fr:$ARTICLES_DIR/
done
for f in $SCRIPT_DIR/../../out/files/mg/tei/livraisons/*.tei
do
    scp $f tbottini@data-iremus.huma-num.fr:$LIVRAISONS_DIR/
done