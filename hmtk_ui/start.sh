if [ -d /Applications/QGIS.app/ ]; then
    echo "Mac OS X detected"
    export LD_LIBRARY_PATH=/Applications/QGIS.app/Contents/MacOS/lib/
    export QGIS_PREFIX_PATH=/Applications/QGIS.app/Contents/MacOS/
    export PYTHONPATH=${PYTHONPATH}:/Library/Frameworks/GDAL.framework/Versions/1.9/Python/2.7/site-packages/
    export PYTHONPATH=$PYTHONPATH:/Applications/QGIS.app/Contents/Resources/python/
else
    echo "GNU/Linux detected"
    export QGIS_PREFIX_PATH=/usr/
    export PYTHONPATH=${QGIS_PREFIX_PATH}/share/qgis/python:${PYTHONPATH}
fi

export PYTHONPATH=$PYTHONPATH:~/.qgis/python/plugins/

python `dirname $0`/main.py




