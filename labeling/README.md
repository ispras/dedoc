# Label data for dedoc classifiers

To run labeling API, use the following command (from the project root):
```shell
docker-compose -f labeling/docker-compose.yml up --build
```

Or you can run API from `labeling` directory:
```shell
cd labeling
docker-compose up --build
```

By default, API is available on `localhost:1232`.

To run tests, use the following command (from the project root):
```shell
test="true" docker-compose -f labeling/docker-compose.yml up --build --exit-code-from test
```
