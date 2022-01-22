# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)
from pathlib import Path
from shutil import copytree, rmtree
from sys import exit, stderr

from html5validator import Validator
from minify_html import minify, minify_css


BUILD_DIR = Path("build")
def built_html_and_css(base_dir=BUILD_DIR):
	for subpath in base_dir.iterdir():
		if subpath.is_dir():
			for file_path in built_html_and_css(subpath):
				yield file_path
		elif subpath.suffix in (".html", ".css"):
			yield subpath


VALIDATED_SUFFIXES = (".html", ".css")
VALIDATOR = Validator(vnu_args=['--also-check-css'])
def valid_or_exit(error_message):
	exit_code = VALIDATOR.validate(list(built_html_and_css()))
	if exit_code != 0:
		print(error_message, file=stderr)
		exit(exit_code)


def ignored_files(_src, names):
	return [name for name in names if name.endswith(".spdx-meta")]


try:
	rmtree(BUILD_DIR)
except FileNotFoundError:
	pass
copytree(Path("static"), BUILD_DIR, ignore=ignored_files)
valid_or_exit("ERROR: The built site was invalid before it was even minified.")
for path in built_html_and_css():
	with path.open(mode='rt') as file:
		code = file.read()
	if path.suffix == ".html":
		# See here for which options are needed for spec compliance:
		# <https://docs.rs/minify-html/0.8.0/src/minify_html/cfg/mod.rs.html#40-47>
		code = minify(
				code,
				do_not_minify_doctype = True,
				ensure_spec_compliant_unquoted_attribute_values = True,
				keep_spaces_between_attributes = True,

				minify_css=True
		)
	elif path.suffix == ".css":
		# While minify_css() takes all of the same options as minify(),
		# I don’t think that any of them do anything, at the moment.
		code = minify_css(code)

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
	# Unfortunately, the validator often fails to parse CSS files with a
	# BOM (<https://github.com/validator/validator/issues/1302>).
	if path.suffix == ".css":
		output_encoding = 'utf_8'
	else:
		output_encoding = 'utf_8_sig'
	# MIME hint note: The “text” MIME type uses CRLF.
	#
	# The HTML Standard allows for multiple different kinds of newlines
	# (<https://html.spec.whatwg.org/multipage/syntax.html#newlines>), but
	# it also requires HTML documents to have a “text” MIME type
	# (<https://html.spec.whatwg.org/multipage/infrastructure.html#terminology>).
	#
	# MIME requires the “canonical form” of text to use CRLFs. It also
	# forbids the use of CRs and LFs unless they’re part of a CRLF
	# (<https://www.rfc-editor.org/rfc/rfc2046.html#section-4.1.1>).
	#
	# In other words, to be as compliant as possible, use CRLFs.
	with path.open(mode='wt', encoding=output_encoding, newline='\r\n') as file:
		file.write(code)
valid_or_exit("ERROR: html-minify generated invalid HTML or CSS.")
