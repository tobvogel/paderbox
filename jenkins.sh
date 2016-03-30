#!/usr/bin/env bash

renice -n 20 $$

# set a prefix for each cmd
green='\033[0;32m'
NC='\033[0m' # No Color
trap 'echo -e "${green}$ $BASH_COMMAND ${NC}"' DEBUG

# Force Exit 0
trap 'exit 0' EXIT SIGINT SIGTERM EXIT

# Set Paths
CUDA_PATH=/usr/local/cuda
LD_LIBRARY_PATH=$CUDA_PATH/lib64:${LD_LIBRARY_PATH}
PATH=$CUDA_PATH/bin:$PATH
export PATH
export LD_LIBRARY_PATH
source activate py35

# enable matlab tests
TEST_MATLAB=true
export TEST_MATLAB

# Refresh toolbox
pip uninstall --quiet --yes nt
pip install  --quiet --user -e .

# Update chainer
pip uninstall --quiet --yes chainer
pip install --quiet --user -e  ./chainer/

# Unittets
nosetests --with-xunit --with-coverage --cover-package=nt --processes=-1
# Use as many prosesses as you have cores: --processes=-1

# Export coverage
python -m coverage xml --include=nt*

# Pylint tests
pylint --rcfile=pylint.cfg -f parseable nt > pylint.txt
# --files-output=y is a bad option, because it produces hundreds of files

# Build documentation
make --directory=doc/source/auto_reference/ clean
make --directory=doc/source/auto_reference/
make --directory=doc clean
make --directory=doc html

# Store pip packages
pip freeze > pip.txt

# Uninstall packages
pip uninstall --quiet --yes chainer
pip uninstall --quiet --yes nt
