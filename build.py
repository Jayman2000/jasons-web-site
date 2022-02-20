# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)
from __future__ import annotations

from abc import ABC, abstractclassmethod, abstractmethod
from argparse import ArgumentParser
from datetime import datetime
from itertools import chain
from os import mkdir, makedirs
from pathlib import Path
from shutil import copy2, rmtree
from sys import exit, stderr
from typing import Final, Iterable, List, NamedTuple, Optional, Tuple, TypeVar, Type

from dateutil.parser import isoparse
from html5validator import Validator
from jinja2 import FileSystemLoader, Environment
from jinja2.environment import TemplateModule
from minify_html import minify as minify_html, minify_css
from sortedcontainers import SortedList


def eprint(msg: str) -> None:
	print(msg, file=stderr)


def encoding_for(file_path: Path) -> str:
	# MIME hint note: Unicode signatures hint that charset="utf-8"
	#
	# As The Unicode Standard says,
	# “Unicode Signature. An initial BOM may also serve as an implicit
	# marker to identify a file as containing Unicode text. For UTF-16, the
	# sequence FE 16 FF16 (or its byte-reversed counterpart, FF16 FE16) is
	# exceedingly rare at the outset of text files that use other character
	# encodings. The corresponding UTF-8 BOM sequence, EF16 BB16 BF16, is
	# also exceedingly rare.”
	# — <https://www.unicode.org/versions/Unicode14.0.0/ch02.pdf#G9354>
	#
	# Unfortunately, the validator often fails to parse CSS files with a BOM
	# (<https://github.com/validator/validator/issues/1302>).
	if file_path.suffix == ".css":
		return 'utf_8'
	else:
		return 'utf_8_sig'


def write_out_text_file(text: str, file_path: Path) -> None:
	"""Writes text to a file with appropriate MIME hinting."""

	# Create the file’s parent directory if it doesn’t exist already.
	makedirs(Path(*file_path.parts[:-1]), exist_ok=True)
	# MIME hint note: The “text” MIME type uses CRLF.
	#
	# The HTML Standard allows for multiple different kinds of
	# newlines (<https://html.spec.whatwg.org/multipage/syntax.html#newlines>),
	# but it also requires HTML documents to have a “text” MIME type
	# (<https://html.spec.whatwg.org/multipage/infrastructure.html#terminology>).
	#
	# MIME requires the “canonical form” of text to use CRLFs. It also
	# forbids the use of CRs and LFs unless they’re part of a CRLF
	# (<https://www.rfc-editor.org/rfc/rfc2046.html#section-4.1.1>).
	#
	# In other words, to be as compliant as possible, use CRLFs.
	with file_path.open(mode='wt', encoding=encoding_for(file_path), newline='\r\n') as file:
		file.write(text)


MINIFIED_SUFFIXES = (".html", ".css")
def minify(paths: Iterable[Path]) -> None:
	print("Minifying…")
	for path in paths:
		if path.suffix in MINIFIED_SUFFIXES:
			with path.open(mode='rt', encoding=encoding_for(path)) as file:
				code = file.read()
			if path.suffix == ".html":
				# See here for which options are needed for spec
				# compliance:
				# <https://docs.rs/minify-html/0.8.0/src/minify_html/cfg/mod.rs.html#40-47>
				code = minify_html(
						code,
						do_not_minify_doctype = True,
						ensure_spec_compliant_unquoted_attribute_values = True,
						keep_spaces_between_attributes = True,

						minify_css=True
				)
			elif path.suffix == ".css":
				# While minify_css() takes all of the same
				# options as minify(), I don’t think that any of
				# them do anything at the moment.
				code = minify_css(code)
			write_out_text_file(code, path)



VALIDATED_SUFFIXES = (".html", ".css")
VALIDATOR = Validator(vnu_args=['--also-check-css'])
def valid_or_exit(paths: List[Path], error_message: str) -> None:
	print("Validating…")
	to_validate = [path for path in paths if path.suffix in VALIDATED_SUFFIXES]
	exit_code = VALIDATOR.validate(to_validate)
	if exit_code != 0:
		eprint(error_message)
		exit(exit_code)




def files_in(directory: Path) -> Iterable[Path]:
	"""Yields every file that is a descendent of directory."""
	try:
		for subpath in directory.iterdir():
			if subpath.is_dir():
				for file_path in files_in(subpath):
					yield file_path
			else:
				yield subpath
	except FileNotFoundError:
		pass


class Destination(ABC):
	"""Represents a possible location of the site."""
	def __init__(self, scheme: str):
		"""
		scheme — a URL scheme [1].

		[1]: <https://www.w3.org/TR/webarch/#URI-scheme>
		"""
		self.scheme = scheme

	@abstractmethod
	def base_url(self) -> Optional[str]:
		"""
		URL to include in a <base> element [1].

		[1]: <https://html.spec.whatwg.org/dev/semantics.html#the-base-element>
		"""
		...

	def csp_self_source(self) -> str:
		"""
		Returns CSP source to be used instead of 'self'.

		Sometimes, when I’m writing a Content Security Policy [1], I
		want to use the 'self' source [2]. Unfortunately, 'self' doesn’t
		work for all URL schemes [3]. This method should return the
		closest thing to 'self' that will actually work for this
		BaseURL’s scheme.

		[1]: <https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP>
		[2]: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/Sources#self>
		[3]: <https://www.w3.org/TR/webarch/#URI-scheme>
		"""
		return self.scheme + ":"


class GenericDestination(Destination):
	"""Use this if your Destination isn’t an HTTPStyleDestination or an UnknownDestination."""
	def __init__(self, scheme: str, part_after_colon:str):
		"""
		scheme — a URL scheme [1].

		part_after_colon — make sure that this ends with a slash.

		Example: In the URL “file:///foo/” the scheme is “file” and the
		part_after_colon is “///foo/”.

		[1]: <https://www.w3.org/TR/webarch/#URI-scheme>
		"""
		super().__init__(scheme)
		self.part_after_colon = part_after_colon

	def base_url(self) -> str:
		return f"{self.scheme}:{self.part_after_colon}"


# In CSP, 'self' means “from the same origin” [1]. Unfortunately, with most
# schemes, it’s impossible to create a same origin URL [2].
#
# [1]: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/Sources#sources>
# [2]: <https://url.spec.whatwg.org/#origin>
SCHEMES_WHERE_SELF_WORKS: Final = ("ftp", "http", "https", "ws", "wss")
class HTTPStyleDestination(Destination):
	"""A base URL that looks something like this “http://<domain>/”."""
	def __init__(self, scheme: str, host_and_maybe_port: str):
		"""
		scheme — The URL scheme [1]. Should be all lower case.

		host_and_maybe_port — the part that goes between the “://” and
		the “/”. Examples: “example.com”, “example.org:50”, “0.0.0.0”
		and “127.0.0.1:70”.

		[1]: <https://www.w3.org/TR/webarch/#URI-scheme>
		"""
		super().__init__(scheme)
		self.host_and_maybe_port = host_and_maybe_port

	def base_url(self) -> str:
		return f"{self.scheme}://{self.host_and_maybe_port}/"

	def csp_self_source(self) -> str:
		if self.scheme in SCHEMES_WHERE_SELF_WORKS:
			# The single quotes are required:
			# <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/Sources#sources>
			return "'self'"
		else:
			return super().csp_self_source()


class UnknownDestination(Destination):
	"""
	A Destination which isn’t full known.

	Use this for unsupported schemes [1].

	[1]: <https://www.w3.org/TR/webarch/#URI-scheme>
	"""
	def base_url(self) -> None:
		return None


class PostInfo(NamedTuple):
	relative_url: str
	title: str
	completion_time: datetime

	# This is the only one needed for SortedList in this case. See:
	# <http://www.grantjenks.com/docs/sortedcontainers/introduction.html#caveats>
	def __lt__(self, other: PostInfo) -> bool:
		return self.completion_time < other.completion_time


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
		return self.destination(dest_dir)

	def destination(self, dest_dir: Path) -> Path:
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
		copy2(self.source(), self.destination(dest_dir))
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
		destination = self.destination(dest_dir)
		print(f"Building “{destination}”…")
		template = self.env.get_template(str(self.relative_to_base))
		module = template.make_module(self.jinja_variables)

		if self.is_post():
			post_info = PostInfo(
					str(self.relative_to_base),
					str(getattr(module, 'title', "ERROR: Missing title")),
					isoparse(getattr(module, 'completion_time', "1800"))
			)
			self.jinja_variables['posts'].add(post_info)

		write_out_text_file(str(module), destination)
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
