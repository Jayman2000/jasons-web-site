# SPDX-FileNotice: 🅭🄍1.0 This file was dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)
from pathlib import Path
from shutil import copytree, rmtree
from sys import exit, stderr, version_info
from typing import Final, Iterable

from html5validator.validator import Validator
from minify_html import minify


BUILD_DIR: Final[Path] = Path("build")
def all_built_files(base_dir: Path = BUILD_DIR) -> Iterable[Path]:
	for subpath in base_dir.iterdir():
		if subpath.is_file():
			yield subpath
		else:
			for file_path in all_built_files(subpath):
				yield file_path


VALIDATOR: Final[Validator] = Validator()
def valid_or_exit(error_message: str) -> None:
	exit_code: int = VALIDATOR.validate(list(all_built_files()))
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
	with path.open(mode='r') as file:
		code: str = file.read()
	# See here for which options are needed for spec compliance:
	# <https://docs.rs/minify-html/0.8.0/src/minify_html/cfg/mod.rs.html#40-47>
	code = minify(
			code,
			do_not_minify_doctype = True,
			ensure_spec_compliant_unquoted_attribute_values = True,
			keep_spaces_between_attributes = True
	)
	with path.open(mode='w') as file:
		file.write(code)
valid_or_exit("ERROR: html-minify generated invalid HTML.")
