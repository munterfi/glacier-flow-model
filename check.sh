#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Name          :checks.sh
# Description   :Script for running all package (pytest, coverage, mypy and
#                flake8) checks.
# Author        :Merlin Unterfinger <info@munterfinger.ch>
# Date          :2020-10-14
# Version       :0.1.0
# Usage         :./checks.sh
# Notes         :
# Bash          :5.0.18
# =============================================================================

echo '*** pytest: Tests and coverage ***'
poetry run pytest --cov=glacier_flow_model

echo -e '\n*** mypy: Static type checks ***'
poetry run mypy .

echo -e '\n*** flake8: Code linting ***'
poetry run flake8 glacier_flow_model tests --count

echo -e '\n*** Building documentation ***'
cd docs && poetry run make html && cd ..
