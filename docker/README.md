# Build inside Docker

## Build the container

From the root folder:

```bash
$ docker build --build-arg uid=$(id -u) --rm=true -t qgis-builder -f Dockerfile .
```
On our Jenkins system `--build-arg` must be `--build-arg uid=107`

## Run the build

From the root folder:

```bash
$ docker run -e OSGEO_QGIS_USERNAME=<username> -e OSGEO_QGIS_PASSWORD=<password> -e GEM_QGIS_DOCS=<key path> -t -i -v $(pwd):/io --rm qgis-builder release NEW_VERSION=vX.Y.Z
```
