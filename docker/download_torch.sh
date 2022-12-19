#!/bin/bash -e
# download secure pytorch 1.11.0 (>o<)
git clone https://timon.intra.ispras.ru/mirrors/pytorch.git
cd pytorch/
git checkout 1911a637404fcc10e15c3d3889b1401cbc763564
git submodule sync
git submodule update --init --recursive --jobs 0