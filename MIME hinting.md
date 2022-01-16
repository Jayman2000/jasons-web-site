<!--
SPDX-FileNotice: 🅭🄍1.0 This file was dedicated to the public domain using the CC0 1.0 Universal Public Domain Dedication <https://creativecommons.org/publicdomain/zero/1.0/>.
SPDX-FileContributor: Jason Yundt <swagfortress@gmail.com> (2022)

Creative Commons’s best practices for attribution
(<https://wiki.creativecommons.org/wiki/Best_practices_for_attribution>):
SPDX-FileNotice: The “HTML Standard” (<
-->

# What is MIME Hinting and Why Does This Repo MIME hint?

This repo goes out of its way to MIME hint. To understand MIME hinting, you
must consider the problem that it’s trying to solve. Ultimately, a Web site is
a collection of files. Once those files are created, they must be given URLs. I
want my site to be available under many different protocols, so eventually,
each file will have multiple URLs each with a different [scheme].

According to [the HTML Standard](https://html.spec.whatwg.org/multipage/),

>“This specification uses the term **document** to refer to any use of HTML,
>ranging from short static documents to long essays or reports with rich
>multimedia, as well as to fully-fledged interactive applications. The term is
>used to refer both to [`Document`](https://html.spec.whatwg.org/multipage/dom.html#document)
>objects and their descendant DOM trees, and to serialized byte streams using
>[the HTML syntax] or [the XML syntax](https://html.spec.whatwg.org/multipage/xhtml.html#the-xhtml-syntax),
>depending on context.”

— [The HTML Standard, Section 2.1](https://html.spec.whatwg.org/multipage/infrastructure.html#terminology)

This repo’s build system generates documents that will eventually be served
over the Internet. The generated files and the data that gets served are
“serialized byte streams using [the HTML syntax]”. That same section later goes
on to say

>“In the context of byte streams, the term HTML document refers to resources
>labeled as [`text/html`](https://html.spec.whatwg.org/multipage/iana.html#text/html),
>and the term XML document refers to resources labeled with an [XML MIME type](https://mimesniff.spec.whatwg.org/#xml-mime-type).”

— [The HTML Standard, Section 2.1](https://html.spec.whatwg.org/multipage/infrastructure.html#terminology)

Strictly speaking, in order to be an HTML document, there must be something
that labels these byte streams with a `text/html` MIME type.

Additionally, [an HTML document’s MIME type](https://www.iana.org/assignments/media-types/text/html)
[may specify that the](https://html.spec.whatwg.org/multipage/iana.html#text/html)
[charset is UTF-8](https://html.spec.whatwg.org/multipage/semantics.html#charset).

Here’s the problem: you can never be certain that the MIME type is correct.
Consider this question: how do you specify a MIME type? For one thing,
it depends on what [scheme] your using:

- [`http` and `https` use the “Content-Type” header field](https://datatracker.ietf.org/doc/html/rfc7231#section-3.1.1.5)
- [`coap` and its variants use the “Content-Format” option](https://www.rfc-editor.org/rfc/rfc7252.html#section-5.5.1)
- [`data` embeds the MIME type in the URL itself](https://www.rfc-editor.org/rfc/rfc2397.html#section-2)
- [`ipfs` doesn’t have a mechanism for specifying a MIME type](https://github.com/ipfs/in-web-browsers/issues/152)
- [`bzz` uses manifests](https://mainframe-swarm-guide.readthedocs.io/en/latest/architecture.html#manifests)
- [`file` doesn’t have a mechanism for specifying a MIME type](https://www.rfc-editor.org/rfc/rfc8089.html#section-1),
[so Web browsers let the OS choose one](https://github.com/whatwg/mimesniff/issues/138)

This suggests that an HTML document’s MIME type should be self-evident. In
other words, the computer should be able to detect the MIME type by looking
only at the file’s contents because there’s no guarantee that the scheme we’re
using provides a MIME type.

For the sake of argument, let’s say that we’re using a scheme like http or
data which provides a MIME type for the file. Even then, the MIME type should
be self-evident. Consider this: how does an HTTP server determine what gets put
in the Content-Type header? The server probably looks at the file to figure it
out. I’m sure it would be possible to manually specify MIME types, but that
still doesn’t guarantee that they’ll be correct.

MIME hinting is the act of including information in a file to make its MIME
type self-evident. Throughout this repo, you’ll find comments that say “MIME
hint note:”. Those comments will contain explanations of how MIME hinting is
done.

## [Creative Commons’s best practices for attribution](https://wiki.creativecommons.org/wiki/Best_practices_for_attribution)

SPDX-FileNotice: The [“HTML Standard”](https://html.spec.whatwg.org/multipage/) by [WHATWG (Apple, Google, Mozilla, Microsoft)](https://whatwg.org/) is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

[scheme]: https://www.w3.org/TR/webarch/#URI-scheme
[the HTML syntax]: https://html.spec.whatwg.org/multipage/syntax.html#syntax
