To run Dedoc on CUDA with Docker use files from `docker_gpu` directory 
([CUDA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) 
should be installed on your machine):

1. Set `on_gpu` to `True` in `config.py`
2. Run application:
```shell
cd docker_gpu
docker-compose up --build
```

You can change index of CUDA device at `docker-compose.yml`:
```
NVIDIA_VISIBLE_DEVICES: 0
NVIDIA_VISIBLE_DEVICES: 0, 3
NVIDIA_VISIBLE_DEVICES: all
```
