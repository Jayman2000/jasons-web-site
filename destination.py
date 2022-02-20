# SPDX-FileNotice: 🅭🄍1.0 This file is dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
# SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)
from abc import ABC, abstractmethod
from typing import Final, Optional


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


__all__ = (
		"Destination",
		"GenericDestination",
		"HTTPStyleDestination",
		"UnknownDestination"
)
