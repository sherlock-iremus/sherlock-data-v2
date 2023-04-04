# SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SCRIPT_DIR=$(pwd)/$(dirname "$0")
echo $SCRIPT_DIR

trap "exit" INT

file_name () {
	filename=$(basename "$1")
	extension="${filename##*.}"
	filename="${filename%.*}"

	echo $filename
}

rm -rf $TEI_LIVRAISONS
mkdir -p $TEI_LIVRAISONS
rm -rf $TEI_ARTICLES
mkdir -p $TEI_ARTICLES
rm -rf $JSON_ARTICLES
mkdir -p $JSON_ARTICLES

for f in $(ls $MGGHXML/*.xml)
do
  livraison_id=$(file_name $f)
  echo ""
  echo LIVRAISON $livraison_id
  cp $f $TEI_LIVRAISONS
  
  # FRAGMENTATION DES FICHIERS TEI
  java -jar ./Saxon-HE/12/Java/saxon-he-12.1.jar -s:$f -xsl:"$SCRIPT_DIR"/fragment.xslt -o:$TEI_ARTICLES/TOKILL.xml
  rm $TEI_ARTICLES/TOKILL.xml

  # FORMATAGE DES FRAGMENTS TEI
  for f in $(ls $TEI_ARTICLES/$livraison_id*)
  do
    article_id=$(file_name $f)

    mv $f $f.temp0
    xmllint --noblanks $f.temp0 > $f.temp1
    tr -d "\n\r" < $f.temp1 > $f.temp2
    tr -s " " < $f.temp2 > $f
    rm $f.temp0
    rm $f.temp1
    rm $f.temp2

    # JSONISATION DES FRAGMENTS TEI
    echo "    $(file_name $f) [TEI] -> $article_id [JSON]"
    python3 "$SCRIPT_DIR"/xml2json.py $f $JSON_ARTICLES/$article_id.json
  done
done