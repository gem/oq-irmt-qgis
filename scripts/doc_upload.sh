EXPERIMENTAL=$(grep 'experimental=' ../svir/metadata.txt | cut -d '=' -f 2)
echo EXPERIMENTAL=$EXPERIMENTAL
if [ $EXPERIMENTAL = "True" ]
then
    BUILD=latest
else
    BUILD=LTS
fi
echo BUILD=$BUILD

VERSION="v$(grep 'version=' ../svir/metadata.txt | cut -d '=' -f 2)"
echo VERSION=$VERSION

USER=docs
HOST=$USER@docs.gem.lan
BASE_PATH="~/oq-irmt-qgis"
HOST_PATH="$BASE_PATH/$VERSION"
# If user is ptormene don't need other keys
#if ["$GEM_QGIS_DOCS" != ""]; then
#    # path of ssh key must be referred to oq-irmt-qgis root
#    SSH_KEY="-i ../$GEM_QGIS_DOCS"
#fi
ssh $SSH_KEY $HOST 'mkdir -p ' $HOST_PATH
scp $SSH_KEY -r ../svir/help/build/html/* $HOST:$HOST_PATH

ssh $SSH_KEY $HOST "bash -cx 'cd ${BASE_PATH}; ln -snf \"$VERSION\" $BUILD'"
