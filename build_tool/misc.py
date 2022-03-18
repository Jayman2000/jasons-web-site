# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)
from __future__ import annotations

from datetime import datetime
from minify_html import minify as minify_html, minify_css
from os import makedirs
from pathlib import Path, PosixPath
from sys import stderr
from typing import Final, Iterable, List, NamedTuple

from html5validator import Validator


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


MINIFIED_SUFFIXES: Final = (".html", ".css")
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


class PostInfo(NamedTuple):
	relative_url: str
	title: str
	completion_time: datetime

	# This is the only one needed for SortedList in this case. See:
	# <http://www.grantjenks.com/docs/sortedcontainers/introduction.html#caveats>
	def __lt__(self, other: PostInfo) -> bool:
		return self.completion_time < other.completion_time


# In CSP, 'self' means “from the same origin” [1]. Unfortunately, with most
# schemes, it’s impossible to create a same origin URL [2].
#
# [1]: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/Sources#sources>
# [2]: <https://url.spec.whatwg.org/#origin>
SCHEMES_WHERE_SELF_WORKS: Final = ("ftp", "http", "https", "ws", "wss")
def csp_self_source(scheme: str) -> str:
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
	if scheme in SCHEMES_WHERE_SELF_WORKS:
		# The single quotes are required:
		# <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/Sources#sources>
		return "'self'"
	else:
		return scheme + ":"


def generate_relative_url(current_resource_path: str, desired_path: str) -> str:
	"""
	Returns a URL to a particular resource that’s relative to the current one.

	current_resource_path — The path of the current resource.
	desired_path — The path that the current resource is trying to access.

	Both of those paths must be relative to the root of the site. In other
	words, they must be relative to the directory that the site’s homepage
	is in. Neither of those paths should use “.” (current directory) or “..”
	(parent directory).

	As an example, consider the following directory:

	.
	├── index.html
	├── main.css
	└── posts
		├── example.css
		└── example.html

	1 directory, 4 files

	generate_relative_url("index.html", "main.css") -> "main.css"
	generate_relative_url("index.html", "posts/example.html") -> "posts/example.html"

	generate_relative_url("posts/example.html", "index.html") -> "../index.html"
	generate_relative_url("posts/example.html", "posts/example.css") -> "example.css"
	"""
	CRP: Final[PosixPath] = PosixPath("/", current_resource_path)
	DP: Final[PosixPath] = PosixPath("/", desired_path)

	if CRP == DP:  # If a page is linking to itself…
		return DP.parts[-1]  # then return the page’s filename.
	else:
		last_common_part: int = 0
		try:
			while CRP.parts[last_common_part] == DP.parts[last_common_part]:
				last_common_part += 1
		except IndexError:
			pass

		parts_after_lcp: int = len(CRP.parts) - 1 - last_common_part
		retrun_value_parts: List[str] = [".."] * parts_after_lcp
		retrun_value_parts += DP.parts[last_common_part:]

		return str(PosixPath(*retrun_value_parts))


__all__ = (
		"eprint",
		"encoding_for",
		"write_out_text_file",
		"minify",
		"valid_or_exit",
		"files_in",
		"PostInfo",
		"csp_self_source",
		"generate_relative_url"
)
