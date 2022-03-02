# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)
from __future__ import annotations

from argparse import ArgumentParser
from itertools import chain
from os import makedirs
from pathlib import Path
from shutil import rmtree
from typing import Final

from jinja2 import FileSystemLoader, Environment
from sortedcontainers import SortedList

from .destination import *
from .misc import *
from .resource import *


BASE_BUILD_DIR: Final = Path("build")
BASE_SOURCE_DIR: Final = Path("src")

ARGUMENT_PARSER: Final = ArgumentParser(description="Builds Jason’s Web Site")
ARGUMENT_PARSER.add_argument(
		'site_slugs',
		nargs='*',
		default=('jasons-web-site',),
		help=\
				"The name of the site to build. Look in the "
				+ "“sites” folder for valid names. Default: "
				+ "“jasons-web-site”.",
		metavar="SITE_SLUG"
)
ARGUMENT_PARSER.add_argument(
		'-d',
		'--double-validate',
		action='store_true',
		help=\
				"This flag causes the site to be validated both"
				+ "before and after it’s minified. Implies "
				+ "“--minify”."
)
ARGUMENT_PARSER.add_argument(
		'-H',
		'--host',
		default='localhost:8000',
		type=str,
		help=\
				"The hostname (and optionally port) used for "
				+ "the ftp and http(s) versions of the site. "
				+ "Make sure that an appropriate scheme is set "
				+ "using --scheme, or else this option will do "
				+ "nothing.",
		metavar="HOST[:PORT]"
)
ARGUMENT_PARSER.add_argument(
		'-m',
		'--minify',
		action='store_true',
		help=\
				"This flag causes the site to be minified after"
				+ " it’s built. After it gets minified, it will"
				+ " be validated."
)
ARGUMENT_PARSER.add_argument(
		'-s',
		'--scheme',
		action='append',
		help=\
				"Scheme to use for base URLs. Can be specified "
				+ "multiple times. Default: “file”.",
		metavar="SCHEME",
		dest='schemes'
)
ARGS: Final = ARGUMENT_PARSER.parse_args()
ARGS.minify = ARGS.minify or ARGS.double_validate
if ARGS.schemes is None:
	ARGS.schemes = ("file",)

try:
	rmtree(BASE_BUILD_DIR)
except FileNotFoundError:
	pass


def build_site(site_slug: str,) -> None:
	print(f"======================== {site_slug} ========================")

	static_dir = Path(BASE_SOURCE_DIR, site_slug, "static")
	templates_dir = Path(BASE_SOURCE_DIR, site_slug, "templates")

	if not static_dir.is_dir() and not templates_dir.is_dir():
		raise ValueError(
				f"ERROR: neither “{static_dir}” nor "
				+ f"“{templates_dir}” exist. Is “{site_slug}” a"
				+ " valid site slug? Is the current working "
				+ "directory the root of the repo?"
		)

	env = Environment(loader=FileSystemLoader(templates_dir))
	env.globals = { 'reversed':reversed }

	for scheme in ARGS.schemes:
		print(f"---------------------- {scheme} ----------------------")
		dest_dir = Path(BASE_BUILD_DIR, site_slug, scheme)
		makedirs(dest_dir)

		destination: Destination
		if scheme in ("ftp", "http", "https"):
			destination = HTTPStyleDestination(scheme, ARGS.host)
		elif scheme == "file":
			destination = GenericDestination(
					"file",
					# as_uri() seems to always leave out the
					# final slash, but for base URLs the
					# final slash is necessary to indicate
					# that the last component is a
					# directory.
					dest_dir.absolute().as_uri()[5:] + "/"
			)
		else:
			eprint(f"WARNING: The scheme “{scheme}” is not supported. Omitting base URL…")
			destination = UnknownDestination(scheme)
		jinja_variables = {
				'destination':destination,
				'posts':SortedList()
		}

		built_resources = []
		for resource in chain(
				StaticResource.all(static_dir, ignored_suffix=".spdx-meta"),
				JinjaResource.all(templates_dir, env, jinja_variables, ignored_suffix=".spdx-meta")
		):
			built_resources.append(resource.build(dest_dir))

		if not ARGS.minify or ARGS.double_validate:
			valid_or_exit(
					built_resources,
					"ERROR: Files weren’t minified (yet), but at least one of them is still invalid."
			)
		if ARGS.minify:
			minify(built_resources)
			valid_or_exit(
					built_resources,
					"ERROR: Something was invalid after it was minified."
			)

for site_slug in ARGS.site_slugs:
	build_site(site_slug)
