# Build inside Docker

## Build the container

From the root folder:

```bash
$ docker build --build-arg uid=$(id -u) --rm=true -t qgis-builder -f docker/Dockerfile .
```
On our Jenkins system `--build-arg` must be `--build-arg uid=107`

## Run the build

From the root folder:

```bash
$ docker run -t -i -v $(pwd):/io --rm qgis-builder package VERSION=X.YY
```
