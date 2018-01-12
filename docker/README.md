# Build inside Docker

## Build the container

From the root folder:

```bash
$ docker build --rm=true -t qgis-builder -f docker/Dockerfile .
```

## Run the build

From the root folder:

```bash
$ docker run -t -i -v $(pwd):/io --rm qgis-builder
```
