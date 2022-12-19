#!/bin/bash -e
# build secure pytorch 1.11.0 (>o<) without CUDA
pip3.8 install cmake --upgrade
bash Miniconda3-py38_4.12.0-Linux-x86_64.sh -b -p ~/miniconda3
~/miniconda3/bin/conda create --name pytorch-build python=3.8
~/miniconda3/bin/conda activate pytorch-build
~/miniconda3/bin/conda install astunparse numpy ninja pyyaml mkl mkl-include setuptools cmake cffi typing_extensions future six requests dataclasses

export CMAKE_PREFIX_PATH="$HOME/miniconda3/envs/pytorch-build"

sudo apt-get install libomp-dev
export USE_CUDA=0 USE_CUDNN=0 USE_MKLDNN=1

cd pytorch/
python3.8 setup.py install
