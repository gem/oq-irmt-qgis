#!/bin/bash

if [ "$GEM_SET_DEBUG" == "true" ]; then
	set -x
fi
set -e

if [ "$version" == "" ]; then
	echo "Error: please provide a version tag" >&2
    exit 1
fi

# publish
if [ "$publish" == "true" ]; then
    cat <<EOF > .osgeo_credentials
    export OSGEO_QGIS_USERNAME='theuser'
    export OSGEO_QGIS_PASSWORD='thepassword'
EOF

	docker run --rm -v $(pwd):/io --rm qgis-builder upload_plugin NEW_VERSION=${version}
    cd svir
    # push tags to github
    make tag_push
    # copy docs
    HTDOCS=/var/www/docs.openquake.org/oq-irmt-qgis                                                                                                             
    DEST=${HTDOCS}/${version}
    mkdir $DEST
    cp -R help/build/html/* $DEST
    #ln -sf $DEST ${HTDOCS}/stable
    
else
	docker run --rm -v $(pwd):/io --rm qgis-builder package NEW_VERSION=${version}
fi
