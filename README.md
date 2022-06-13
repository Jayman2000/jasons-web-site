<!--
SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2021–2022)
-->

# [Jason’s Web Site](https://jasonyundt.website/)

## Building

### Prerequisites

- A [Java](http://oracle.com/java/) 8 Runtime Environment
- [Cargo](https://doc.rust-lang.org/cargo/index.html)*
- [`env` (GNU coreutils)](https://www.gnu.org/software/coreutils/)*
- [GNU Bash](https://www.gnu.org/software/bash/)*
- [Go](https://golang.org/)*
- [npm](https://www.npmjs.com/)*
- [Python](https://www.python.org/) 3.8+
- [Pipenv](https://pipenv.pypa.io/en/latest/)
- [`rustc`](https://doc.rust-lang.org/rustc/index.html)

It’s possible that alternatives (like [PyPy](https://www.pypy.org/) or
[FreeBSD](https://www.freebsd.org/)’s `env`) will work, but they haven’t been
tested.

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
1. Run `pipenv run python -m build_tool`

The built site will be placed in the `build` folder.

After this has been done once, you just have to run
`pipenv run python -m build_tool` again to rebuild the site.

You can run `pipenv run python -m build_tool jasons-forge` to build the static
portion of Jason’s Software Forge’s site.

## Hints for contributors

- Every file should declare its own copying information. See the comment at the
top of `COPYING.md` for an example.
- Use tabs for indentation. The only exception to this rule is in YAML files
because [YAML requires spaces for
indentation.](https://yaml.org/spec/1.2.2/#61-indentation-spaces) In YAML
files, use 4 spaces for indentation.
- The `templates` folders contains [Jinja templates](https://jinja.palletsprojects.com/en/3.0.x/).
- Pass `build.py` the `--help` flag. You may find some of its options useful
(like `--scheme`).

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

There’s a few [pre-commit] hook failures that I’m OK with:

- Some [Markdown](https://daringfireball.net/projects/markdown/) files fail one
of pre-commit’s hooks, but only because one line is too long. I’m OK with that
line being too long.
- `SPDX-FileContributor` dates must end in the current year (see the comment at
the top of the file as an example). Sometimes though, it’s correct for them not
to (example: a file copied from another project).

When I run into an error that I’m OK with, I [skip the failing hooks](https://pre-commit.com/#temporarily-disabling-hooks)
for that commit.

## Copying

See [COPYING.md](./COPYING.md).

[Git hook]: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
[pre-commit]: https://pre-commit.com/
[problem]: https://github.com/pre-commit/pre-commit/issues/2178#issuecomment-1002163763
