<!--
SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2021)
-->

# Jason’s Web Site

This repo holds what will eventually become my Web site.

## Building

### Prerequisites

- [Cargo](https://doc.rust-lang.org/cargo/index.html)* 1.57.0
- [`env` (GNU coreutils)](https://www.gnu.org/software/coreutils/)* 9.0
- [GNU Bash](https://www.gnu.org/software/bash/)*, version 5.1.16
- [Python](https://www.python.org/) 3.8+
- [Pipenv](https://pipenv.pypa.io/en/latest/) 2022.1.8
- A [Java](http://oracle.com/java/) 8 Runtime Environment

It’s possible that other versions (especially newer versions) and alternatives
(like [PyPy](https://www.pypy.org/) or [FreeBSD](https://www.freebsd.org/)’s
`env`) work, but they haven’t been tested.

_*In general, I want this project and its build system to be platform neutral,
but some of these aren’t platform neutral. The only reason these are
dependencies is to build [`minify-html`](https://crates.io/crates/minify-html)
with [a specific patch](https://github.com/wilsonzlin/minify-html/pull/67)._

### Build and validate

1. Open a Bash terminal.
1. Change directory to the root of this repo.
1. Make sure that the submodule is ready. To do so, run:
	```bash
	git submodule update --init --recursive
	```
1. Run `./init-venv.sh`
1. Run `pipenv run python build.py`

After this has been done once, you just have to run
`pipenv run python build.py` again to rebuild the site.

## Hints for contributors

- Every file should declare its own copying information. See the comment at the
top of `COPYING.md` for an example.
- Use tabs for indentation. The only exception to this rule is in YAML files
because [YAML requires spaces for
indentation.](https://yaml.org/spec/1.2.2/#61-indentation-spaces) In YAML
files, use 4 spaces for indentation.

## pre-commit

You can use [pre-commit] to automatically check your contributions. One of the
hooks that this repo uses is [Beautysh](https://github.com/lovesegfault/beautysh).
Beautysh uses [the poetry packaging tool](https://python-poetry.org/).
Unfortunately, it’s a bit of a hassle to get hooks that use poetry to work at
the moment due to [one or more upstream bugs][problem]. To get pre-commit to
work with this repo, here’s what you need to do. Hopefully this process will
become simpler overtime.

<!-- TODO: Can the pre-commit config be set up to automate the initial build? -->
1. Build the site if you haven’t done so at least once already.
1. Open a Bash terminal.
1. Make sure that [pre-commit] is installed.
	1. Run `pre-commit --version`
	1. If it gives you an error, follow [these instructions](https://pre-commit.com/#installation).
1. `cd` to the root of this repo.
1. Install the hook that’s affected by [this problem][problem]. To do so, run
	```bash
	SETUPTOOLS_USE_DISTUTILS=stdlib pre-commit install-hooks -c .pre-commit-config-problematic.yaml
	```
1. Install [pre-commit] as a [Git hook]. To do so, run
	```bash
	pre-commit install
	```

At this point, whenever you run `git commit`, [pre-commit] will run a series of
tests for the files that you modified.

Some [Markdown](https://daringfireball.net/projects/markdown/) files fail one
of pre-commit’s hooks, but only because one line is too long. I’m OK with that
line being too long, so I [skip that
hook](https://pre-commit.com/#temporarily-disabling-hooks) when I update those
files.

## Copying

See [COPYING.md](./COPYING.md).

[Git hook]: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
[pre-commit]: https://pre-commit.com/
[problem]: https://github.com/pre-commit/pre-commit/issues/2178#issuecomment-1002163763
