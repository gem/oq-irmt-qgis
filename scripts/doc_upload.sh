USER=docs
HOST=$USER@docs.openquake.org
HOST_PATH="~/oq-irmt-qgis/$VERSION"
if ["$GEM_QGIS_DOCS" != ""]; then
    # path of ssh key must be referred to oq-irmt-qgis root
    SSH_KEY="-i ../$GEM_QGIS_DOCS"
fi
ssh $SSH_KEY $HOST 'mkdir -p ' $HOST_PATH
scp $SSH_KEY -r ../svir/help/build/html/* $HOST:$HOST_PATH
