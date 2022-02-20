# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)
from __future__ import annotations

from abc import ABC, abstractmethod
from argparse import ArgumentParser
from itertools import chain
from os import mkdir
from pathlib import Path
from shutil import copy2, rmtree
from typing import Final, Iterable, List, Optional, TypeVar, Type

from dateutil.parser import isoparse
from jinja2 import FileSystemLoader, Environment
from sortedcontainers import SortedList

from destination import *
from misc import *


class Resource(ABC):
	"""
	A file that will be included in the built site.

	In WWW standards, the term “resource” means “anything that has a Web
	address” [1]. For the purposes of this program, all resources are files.

	[1]: <https://www.w3.org/TR/webarch/#def-resource>
	"""
	def __init__(self, src_dir: Path, relative_to_base: Path):
		"""
		src_dir — the base directory for this Resource before it’s
		built.

		relative_to_base — the path to this Resource, relative to its
		base.

		Example:
		If src_dir is “/foo/” and relative_to_base is “bar/baz.html”,
		then the source code for the Resource can be found at
		“/foo/bar/baz.html”. Once the site is built, the Resource would
		be located at:
		• file:///foo/bar/baz.html
		• ftp://example.org/bar/baz.html
		• http://example.org/bar/baz.html
		• https://example.org/bar/baz.html
		• etc.
		"""
		self.src_dir: Path = src_dir
		self.relative_to_base: Path = relative_to_base

	def __repr__(self) -> str:
		return f"{type(self).__name__}({repr(self.src_dir)}, {repr(self.relative_to_base)}"

	@abstractmethod
	def build(self, dest_dir: Path) -> Path:
		"""
		Builds this Resource and puts the result in dest_dir.
		"""
		return self.dest_file_path(dest_dir)

	def dest_file_path(self, dest_dir: Path) -> Path:
		return Path(dest_dir, self.relative_to_base)

	def source(self) -> Path:
		return Path(self.src_dir, self.relative_to_base)

	# Thanks, Michael0x2a <https://stackoverflow.com/users/646543/michael0x2a>.
	# <https://stackoverflow.com/a/44644576>
	@classmethod
	def all(
			cls: Type[T],
			src_dir: Path,
			*additional_args,
			ignored_suffix: Optional[str] = None
	) -> Iterable[T]:
		"""
		Yields every Resource in a directory.

		You’ll need to call this method on a concrete type (example:
		StaticResource). Each Resource yielded will have the type of the
		concrete type (example: StaticResource.all() yields
		StaticResources).

		If order matters, then classes should override this method and
		yield the Resources in the correct order.
		"""
		for file_path in files_in(src_dir):
			if (
					ignored_suffix is None
					or file_path.suffix != ignored_suffix
			):
				file_path = file_path.relative_to(src_dir)
				yield cls(src_dir, file_path, *additional_args)
T = TypeVar('T', bound=Resource)


class StaticResource(Resource):
	"""
	A Resource in the “static” folder.

	When StaticResources are built, they’re just copied to their
	destination.
	"""
	def build(self, dest_dir: Path) -> Path:
		copy2(self.source(), self.dest_file_path(dest_dir))
		return super().build(dest_dir)


class JinjaResource(Resource):
	"""
	A Resource that is a Jinja [1] template.

	When a JinjaResource is built, it is rendered as a Jinja template.

	[1]: <https://jinja.palletsprojects.com/>
	"""
	def __init__(
			self,
			src_dir: Path,
			relative_to_base: Path,
			env: Environment,
			jinja_variables: dict[str, object]
	):
		"""
		src_dir — see the Resource class.

		relative_to_base — see the Resource class.

		env — the jinja2.Environment [1] that will be used when this
		Resource is built.

		jinja_variables — variables made available to this Jinja
		template when it’s being rendered.

		[1]: <https://jinja.palletsprojects.com/en/3.0.x/api/#jinja2.Environment>
		"""
		super().__init__(src_dir, relative_to_base)
		self.env = env
		self.jinja_variables = jinja_variables

	def __repr__(self) -> str:
		return f"""{type(self).__name__}(
	{repr(self.src_dir)},
	{repr(self.relative_to_base)},
	{repr(self.env)},
	{repr(jinja_variables)}
)"""

	@classmethod
	def all(
			cls,
			src_dir: Path,
			*additional_args,
			ignored_suffix: Optional[str] = None
	) -> Iterable[JinjaResource]:
		"""
		See JinjaResource.__init__ for required positional arguments.
		"""
		NONPOSTS: Final[List[JinjaResource]] = []
		for resource in super().all(
				src_dir,
				*additional_args,
				ignored_suffix=ignored_suffix
		):
			if not resource.relative_to_base.name.startswith("_"):
				if resource.is_post():
					yield resource
				else:
					NONPOSTS.append(resource)
		for resource in NONPOSTS:
			yield resource

	def build(self, dest_dir: Path) -> Path:
		dest_file_path = self.dest_file_path(dest_dir)
		print(f"Building “{dest_file_path}”…")
		template = self.env.get_template(str(self.relative_to_base))
		module = template.make_module(self.jinja_variables)

		if self.is_post():
			post_info = PostInfo(
					str(self.relative_to_base),
					str(getattr(module, 'title', "ERROR: Missing title")),
					isoparse(getattr(module, 'completion_time', "1800"))
			)
			self.jinja_variables['posts'].add(post_info)

		write_out_text_file(str(module), dest_file_path)
		return super().build(dest_dir)

	def is_post(self) -> bool:
		"""Returns whether or not this Resource is a blog post."""
		return self.relative_to_base.parts[0] == 'posts'


if __name__ == "__main__":
	BASE_BUILD_DIR: Final = Path("build")
	STATIC_DIR: Final = Path("static")
	TEMPLATES_DIR = Path("templates")
	ENV: Final = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
	ENV.globals = { 'reversed':reversed }

	ARGUMENT_PARSER: Final = ArgumentParser(description="Builds Jason’s Web Site")
	ARGUMENT_PARSER.add_argument(
			'-d',
			'--double-validate',
			action='store_true',
			help=\
					"This flag causes the site to be "
					+ " validated both before and after "
					+ "it’s minified. Implies “--minify”."
	)
	ARGUMENT_PARSER.add_argument(
			'-H',
			'--host',
			default='localhost:8000',
			type=str,
			help=\
					"The hostname (and optionally port) "
					+ "used for the ftp and http(s) "
					+ "versions of the site. Make sure that"
					+ " an appropriate scheme is set using "
					+ "--scheme, or else this option will "
					+ "do nothing.",
			metavar="HOST[:PORT]"
	)
	ARGUMENT_PARSER.add_argument(
			'-m',
			'--minify',
			action='store_true',
			help=\
					"This flag causes the site to be "
					+ "minified after it’s built. After it"
					+ "gets minified, it will be validated."
	)
	ARGUMENT_PARSER.add_argument(
			'-s',
			'--scheme',
			action='append',
			help=\
					"Scheme to use for base URLs. Can be "
					+ "specified multiple times. Default: "
					+ "“file”.",
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
	mkdir(BASE_BUILD_DIR)
	for scheme in ARGS.schemes:
		print(f"---------------------- {scheme} ----------------------")
		dest_dir = Path(BASE_BUILD_DIR, scheme)
		mkdir(dest_dir)

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
				StaticResource.all(STATIC_DIR, ignored_suffix=".spdx-meta"),
				JinjaResource.all(TEMPLATES_DIR, ENV, jinja_variables, ignored_suffix=".spdx-meta")
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
