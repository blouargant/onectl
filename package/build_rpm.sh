#/bin/sh
SUBCOMPONENT=$1


RELEASENOTE=./releasenote.txt
FULLVERSION=`grep "VERSION :" $RELEASENOTE | head -n1 | sed -e "s/VERSION ://" | sed -e "s/ //g"`
VERSION=`echo $FULLVERSION | sed -e "s/-.*//"`
RELEASE=`echo $FULLVERSION | sed -e "s/.*-//"`
COMPONENT=onectl
PLUGINCOMPONENT=onectl-plugins
DISTRIB=rhel6
ARCH=noarch
TMP_PATH=__tmp__/$COMPONENT-$VERSION
TMP_PATH_PLUGIN=__tmp__/$PLUGINCOMPONENT-$VERSION
#TMP_PATH_CORE=$TMP_PATH/$COMPONENT
#TMP_PATH_PLUGINS=$TMP_PATH/$PLUGINCOMPONENT
OUTPUT=$PWD/__tmp__
ONECTL_SPEC=$COMPONENT.spec
PLUGINS_SPEC=$(ls package/ | grep "^plugin-.*.spec$")
echo "$PLUGINS_SPEC"

GREEN="\\033[1;32m"
RED="\\033[1;31m"
NORMAL="\\033[0;39m"
BLUE="\\033[1;34m"


rm -rf __tmp__
mkdir -p $TMP_PATH
mkdir -p $TMP_PATH_PLUGIN

#core package
install -m644 $RELEASENOTE $TMP_PATH/releasenote-$COMPONENT-$VERSION.txt
cp -a onectl/sources $TMP_PATH/onectl
install -m744 ./onectl/bash/onectl.bash $TMP_PATH/
install -m744 ./onectl/bash/one_completition.sh $TMP_PATH/
install -m744 ./onectl/conf/onectl.conf $TMP_PATH/
install -m644 ./onectl/initd/onectld $TMP_PATH/

cp ./package/onectl.spec __tmp__/$ONECTL_SPEC
for PLG in $PLUGINS_SPEC; do
	cp ./package/$PLG __tmp__/
done

# plugins package
cp -a onectl-plugins/ $TMP_PATH_PLUGIN/plugins
cp -a onectl-plugins/ $TMP_PATH/onectl/plugins
# docs
cp -a ./docs/ $TMP_PATH/docs

find $TMP_PATH | grep "\.svn" | xargs -i -t rm -rf {} 1>/dev/null 2>&1
find $TMP_PATH_PLUGIN | grep "\.svn" | xargs -i -t rm -rf {} 1>/dev/null 2>&1

cd __tmp__
tar cvzf $COMPONENT-$VERSION.tgz $COMPONENT-$VERSION
tar cvzf $PLUGINCOMPONENT-$VERSION.tgz $PLUGINCOMPONENT-$VERSION
cd ..

if [ -z "$SUBCOMPONENT" ]; then
	echo "Building all RPMS"
	# onectl package
	sh ./package/rpm_builder.sh -n $COMPONENT -d $DISTRIB -a $ARCH -t $COMPONENT-$VERSION.tgz  -s $ONECTL_SPEC -v $VERSION -o $OUTPUT -r $RELEASE
	# plugins' package
	for PLG in $PLUGINS_SPEC; do
		echo "Buildding $PLG"
		sh ./package/rpm_builder.sh -n $PLUGINCOMPONENT -d $DISTRIB -a $ARCH -t $PLUGINCOMPONENT-$VERSION.tgz  -s $PLG -v $VERSION -o $OUTPUT -r $RELEASE
	done
else
	if [ "$SUBCOMPONENT" == "core" ]; then
		sh ./package/rpm_builder.sh -n $COMPONENT -d $DISTRIB -a $ARCH -t $COMPONENT-$VERSION.tgz  -s $ONECTL_SPEC -v $VERSION -o $OUTPUT -r $RELEASE
	else
		sh ./package/rpm_builder.sh -n $PLUGINCOMPONENT -d $DISTRIB -a $ARCH -t $PLUGINCOMPONENT-$VERSION.tgz  -s plugin-$SUBCOMPONENT.spec -v $VERSION -o $OUTPUT -r $RELEASE
	fi
fi

mkdir -p ./RPMS
mv -f $OUTPUT/*.rpm ./RPMS/
mkdir -p ./SRPMS
mv -f $OUTPUT/rpmbuild/SRPMS/*.src.rpm ./SRPMS/
rm -rf $OUTPUT
cp $RELEASENOTE RPMS/releasenote-$COMPONENT-$VERSION.txt

CONTENT=`ls RPMS/ | grep "$VERSION"`

echo ""
echo -e "$BLUE----------------------------------------------------------------------------------------$NORMAL"
echo -e "$RED                Packages are available in RPMS directory:" "$NORMAL"
echo -e "$GREEN${CONTENT// /$'\n'}"  "$NORMAL"
echo -e "$BLUE----------------------------------------------------------------------------------------$NORMAL"
echo ""
