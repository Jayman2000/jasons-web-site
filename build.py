# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)
from argparse import ArgumentParser
from pathlib import Path
from shutil import copytree, rmtree
from sys import exit, stderr

from html5validator import Validator
from minify_html import minify, minify_css
from staticjinja import Site


ARGUMENT_PARSER = ArgumentParser(description="Builds Jason’s Web Site")
# An absolute path is needed for the base URL. Otherwise, BASE_BUILD_DIR could
# be relative.
BASE_BUILD_DIR = Path("build").absolute()
VALIDATED_SUFFIXES = (".html", ".css")
VALIDATOR = Validator(vnu_args=['--also-check-css'])


def dest_dir(scheme):
	return Path(BASE_BUILD_DIR, scheme)


def files_in(directory, allow_suffixes):
	for subpath in directory.iterdir():
		if subpath.is_dir():
			for file_path in built_html_and_css(subpath):
				yield file_path
		elif subpath.suffix in allow_suffixes:
			yield subpath


def built_html_and_css(scheme):
	return files_in(dest_dir(scheme), (".html", ".css"))


def ignored_files(_src, names):
	return [name for name in names if name.endswith(".spdx-meta")]


def valid_or_exit(scheme, error_message):
	exit_code = VALIDATOR.validate(list(built_html_and_css(scheme)))
	if exit_code != 0:
		print(error_message, file=stderr)
		exit(exit_code)


def copy_static(scheme):
	copytree(Path("static"), dest_dir(scheme), ignore=ignored_files)


def render_templates(scheme, host_and_maybe_port=None):
	# In CSP, 'self' means “from the same origin” [1]. Unfortunately, origin
	# is implementation defined for the file URI scheme [2]. The next best
	# thing is to just use the scheme itself instead of 'self'.
	#
	# [1]: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/Sources#sources>
	# [2]: <https://url.spec.whatwg.org/#origin>
	if scheme == 'http' or scheme == 'https':
		base_url = f"{scheme}://{host_and_maybe_port}/"
		csp_self_source = "'self'"
	else:
		if scheme == 'file':
			base_url = dest_dir(scheme).as_uri() + "/"
		else:
			print(f"WARNING: Base URI isn’t implemented for the “{scheme}” scheme.", file=stderr)
			base_url = None
		csp_self_source = scheme + ":"
	site = Site.make_site(
			searchpath=Path("templates"),
			outpath=dest_dir(scheme),
			# as_uri() seems to always leave out the final slash,
			# but for base URLs the final slash is necessary to
			# indicate that the last component is a directory.
			env_globals={
				'base_url':base_url,
				'csp_self_source':csp_self_source
			}
	)
	site.render()
	if not ARGS.minify or ARGS.double_validate:
		valid_or_exit(scheme, "ERROR: The built site is invalid, and it wasn’t minified.")


def minify_build(scheme):
	for path in built_html_and_css(scheme):
		with path.open(mode='rt') as file:
			code = file.read()
		if path.suffix == ".html":
			# See here for which options are needed for spec
			# compliance:
			# <https://docs.rs/minify-html/0.8.0/src/minify_html/cfg/mod.rs.html#40-47>
			code = minify(
					code,
					do_not_minify_doctype = True,
					ensure_spec_compliant_unquoted_attribute_values = True,
					keep_spaces_between_attributes = True,

					minify_css=True
			)
		elif path.suffix == ".css":
			# While minify_css() takes all of the same options as
			# minify(), I don’t think that any of them do anything,
			# at the moment.
			code = minify_css(code)

		# MIME hint note: Unicode signatures hint that charset="utf-8"
		#
		# As The Unicode Standard says,
		# “Unicode Signature. An initial BOM may also serve as an
		# implicit marker to identify a file as containing Unicode
		# text. For UTF-16, the sequence FE 16 FF16 (or its byte-
		# reversed counterpart, FF16 FE16) is exceedingly rare at the
		# outset of text files that use other character encodings. The
		# corresponding UTF-8 BOM sequence, EF16 BB16 BF16, is also
		# exceedingly rare.”
		# — <https://www.unicode.org/versions/Unicode14.0.0/ch02.pdf#G9354>
		#
		# Unfortunately, the validator often fails to parse CSS files
		# with a BOM
		# (<https://github.com/validator/validator/issues/1302>).
		if path.suffix == ".css":
			output_encoding = 'utf_8'
		else:
			output_encoding = 'utf_8_sig'
		# MIME hint note: The “text” MIME type uses CRLF.
		#
		# The HTML Standard allows for multiple different kinds of
		# newlines (<https://html.spec.whatwg.org/multipage/syntax.html#newlines>),
		# but it also requires HTML documents to have a “text” MIME
		# type
		# (<https://html.spec.whatwg.org/multipage/infrastructure.html#terminology>).
		#
		# MIME requires the “canonical form” of text to use CRLFs. It
		# also forbids the use of CRs and LFs unless they’re part of a
		# CRLF
		# (<https://www.rfc-editor.org/rfc/rfc2046.html#section-4.1.1>).
		#
		# In other words, to be as compliant as possible, use CRLFs.
		with path.open(mode='wt', encoding=output_encoding, newline='\r\n') as file:
			file.write(code)
	valid_or_exit(scheme, "ERROR: html-minify generated invalid HTML or CSS.")


ARGUMENT_PARSER.add_argument(
		'-d',
		'--double-validate',
		action='store_true',
		help=\
				"This flag causes the site to be validated "
				+ "both before and after it’s minified. "
				+ "Implies “--minify”."
)
ARGUMENT_PARSER.add_argument(
		'-H',
		'--host',
		default='localhost:8000',
		type=str,
		help=\
				"The hostname (and optionally port) used for "
				+ "the http(s) version of the site. Make sure "
				+ "that an appropriate scheme is set using "
				+ "--scheme, or else this option will do "
				+ "nothing.",
		metavar="HOST[:PORT]"
)
ARGUMENT_PARSER.add_argument(
		'-m',
		'--minify',
		action='store_true',
		help=\
				"This flag causes the site to be minified "
				+ "after it’s built. After it gets minified, "
				+ "it will be validated."
)
ARGUMENT_PARSER.add_argument(
		'-s',
		'--scheme',
		action='append',
		help=\
				"Scheme to use for base URLs. Can be  specified"
				+ " multiple times. Default: “file”.",
		metavar="SCHEME",
		dest='schemes'
)
ARGS = ARGUMENT_PARSER.parse_args()
ARGS.minify = ARGS.minify or ARGS.double_validate
if ARGS.schemes is None:
	ARGS.schemes = ("file",)

try:
	rmtree(BASE_BUILD_DIR)
except FileNotFoundError:
	pass

for scheme in ARGS.schemes:
	copy_static(scheme)
	render_templates(scheme, host_and_maybe_port=ARGS.host)
	if ARGS.minify:
		minify_build(scheme)
