#!/usr/bin/env bash
# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)

echo "NOTE: This script assumes that the current working directory is the repo’s root."
# I’m using python -m pipenv because (I think) that there’s a chance that
# pipenv will be available as a module, but not be in PATH.
python -m pipenv install
python -m pipenv run ./init-venv-helper.sh
