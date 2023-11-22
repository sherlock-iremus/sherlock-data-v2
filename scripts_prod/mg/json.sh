SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ARTICLES_DIR=/home/tbottini/sherlock/apache/public_html/files/mercure-galant/articles
ssh tbottini@data-iremus.huma-num.fr "mkdir -p $ARTICLES_DIR"
for f in $SCRIPT_DIR/../../out/files/mg/json/articles/*
do
    scp $f tbottini@data-iremus.huma-num.fr:$ARTICLES_DIR/
done