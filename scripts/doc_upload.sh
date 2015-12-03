USER=docs
HOST=$USER@docs.openquake.org
HOST_PATH="~/oq-irmt-qgis/$VERSION"
ssh $HOST 'mkdir -p ' $HOST_PATH
scp -r ../svir/help/build/html/* $HOST:$HOST_PATH
