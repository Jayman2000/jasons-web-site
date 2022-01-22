#!/usr/bin/env bash
# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)

# NOTE: This script should be run inside the virtual environment created by pipenv.
# NOTE: This script assumes that the current working directory is the repo’s root.
cd minify-html-pr
bash ./prebuild.sh
cd python
python ./prepare.py js
maturin develop
