# SPDX-FileNotice: 🅭🄍1.0 This file was dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)
from pathlib import Path
from shutil import copytree, rmtree
from sys import version_info
# Final was added in Python 3.8[1], but 3.7 is still supported[2].
#
# 1. <https://docs.python.org/3/library/typing.html#typing.Final>
# 2. <https://devguide.python.org/#status-of-python-branches>
if version_info.major >= 3 and version_info.minor >= 8:
	from typing import Final
else:
	# Union[T] == T
	# See <https://docs.python.org/3/library/typing.html#typing.Union>
	from typing import Union as Final

from html5validator.validator import Validator


BUILD_DIR: Final[Path] = Path("build")
try:
	rmtree(BUILD_DIR)
except FileNotFoundError:
	pass
copytree(Path("static"), BUILD_DIR)

VALIDATOR: Final[Validator] = Validator()
VALIDATOR.validate([file for file in BUILD_DIR.glob("**")])
