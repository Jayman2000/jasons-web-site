#!/bin/bash
# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)

rm -r WWW
mkdir WWW
pipenv run python -m build_tool --minify --scheme http --host localhost:2015
cp -r build/jasons-web-site/http WWW/root
cp Caddyfile WWW/

cd WWW
caddy run
