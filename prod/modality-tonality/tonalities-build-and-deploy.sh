SCRIPTS_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBAPPS=$SCRIPTS_DIR/../../../cra-apps
cd $WEBAPPS/sherlock-tonalities
npm install
rm -rf ./build
rm -rf ./tonalities
npm run build
mv $WEBAPPS/sherlock-tonalities/build $WEBAPPS/sherlock-tonalities/tonalities
cd -

scp -r $WEBAPPS/sherlock-tonalities/tonalities tbottini@cchum-kvm-data-iremus.in2p3.fr:sherlock/apache/public_html/
