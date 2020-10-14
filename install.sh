#!/usr/bin/env bash
# ----------------------------------------------------------------------------- 
# Name          :install.sh
# Description   :Build the package wheel and install to global python of the
#                system.
# Author        :Merlin Unterfinger <info@munterfinger.ch>
# Date          :2020-10-14
# Version       :0.1.0  
# Usage         :./install.sh
# Notes         :       
# Bash          :5.0.18
# =============================================================================

echo '*** Setting up local env ***'
poetry install

echo -e '\n*** Building wheel ***'
rm -rf dist && poetry build

echo -e "\n*** Installing globally ($(which python)) ***"
python3 -m pip install --upgrade dist/*

