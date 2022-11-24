SCRIPTS_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBAPPS=$SCRIPTS_DIR/../../../cra-apps
cd $WEBAPPS/sherlock-client
npm install
rm -rf $WEBAPPS/sherlock-client/build
rm -rf $WEBAPPS/sherlock-client/sherlock
npm run build
cp $WEBAPPS/sherlock-client//public/.htaccess $WEBAPPS/sherlock-client/build
mv $WEBAPPS/sherlock-client/build $WEBAPPS/sherlock-client/sherlock
cd -

scp -r $WEBAPPS/sherlock-client/sherlock tbottini@cchum-kvm-data-iremus.in2p3.fr:sherlock/apache/public_html/
