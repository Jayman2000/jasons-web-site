<!--
SPDX-FileNotice: 🅭🄍1.0 This file was dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2021)
-->

# Jason’s Web Site

This repo holds what will eventually become my Web site.

## Building

### Prerequisites

- [Python](https://www.python.org/) 3.8+
- [Pipenv](https://pipenv.pypa.io/en/latest/) 2022.1.8

It’s possible that other versions (especially newer versions) work, but they
haven’t been tested.

### Build and validate

1. Change directory to the root of this repo.
2. Run `pipenv install`
3. Run `pipenv run python build.py`

At the moment, the only thing this will do is copy the files from the `static`
folder to the `build` folder, and validate them. If any of the files are
invalid, then it will warn that they’re invalid.

## Hints for contributors

- You should build the site at least once before using [pre-commit].
- You can use [pre-commit] to automatically check your contributions.
Follow [these instructions](https://pre-commit.com/#quick-start) to get started
(skip the part about creating a `.pre-commit-config.yaml` file).
- Every file should declare its own copying information. See the comment at the
top of `COPYING.md` for an example.
- Use tabs for indentation. The only exception to this rule is in YAML files
because [YAML requires spaces for
indentation.](https://yaml.org/spec/1.2.2/#61-indentation-spaces) In YAML
files, use 4 spaces for indentation.

## Copying

See [COPYING.md](./COPYING.md).

[pre-commit]: https://pre-commit.com/
