# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)
from pathlib import Path
from shutil import copytree, rmtree
from sys import exit, stderr, version_info

from html5validator import Validator
from minify_html import minify


BUILD_DIR = Path("build")
def all_built_files(base_dir=BUILD_DIR):
	for subpath in base_dir.iterdir():
		if subpath.is_file():
			yield subpath
		else:
			for file_path in all_built_files(subpath):
				yield file_path


VALIDATOR = Validator()
def valid_or_exit(error_message):
	exit_code = VALIDATOR.validate([BUILD_DIR])
	if exit_code != 0:
		print(error_message, file=stderr)
		exit(exit_code)


try:
	rmtree(BUILD_DIR)
except FileNotFoundError:
	pass
copytree(Path("static"), BUILD_DIR)
valid_or_exit("ERROR: The built HTML was invalid before it was even minified.")
for path in all_built_files():
	with path.open(mode='rt') as file:
		code = file.read()
	# See here for which options are needed for spec compliance:
	# <https://docs.rs/minify-html/0.8.0/src/minify_html/cfg/mod.rs.html#40-47>
	code = minify(
			code,
			do_not_minify_doctype = True,
			ensure_spec_compliant_unquoted_attribute_values = True,
			keep_spaces_between_attributes = True
	)
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
	with path.open(mode='wt', newline='\r\n') as file:
		file.write(code)
valid_or_exit("ERROR: html-minify generated invalid HTML.")
