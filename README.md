# wiki-link

Stupid as can be system for linking wiki content to an in-game friendly
format/location.

## Description

Dune runs a [DokuWiki] instance. DokuWiki has its own unique [markup language].
We want to be "render" the markup language into a format suitable for display
in-game. It turns out we can do that pretty easily for Markdown, but DokuWiki
doesn't use markdown...

Enter this repo. We install a simple Python script as a `systemd` service. It
watches the wiki content directory for `.txt` file changes. These occur whenever
a wiki page is edited/saved. This service invokes [pandoc] to convert the files
that changed from DokuWiki syntax to GitHub compatible markdown syntax. The
output markdown files are rendered to a location in-lib so that LPC code can
read them.

One last wrinkle: production Dune runs on a stable LTS operating system that
doesn't have a new enough version of `pandoc` in package repository to support
DokuWiki syntax. That's easy enough to solve: we download a pre-built `x86_64`
Linux binary and use that :P

Tada! Wiki content available in-game, nicely rendered, with very little code.

[DokuWiki]: https://www.dokuwiki.org/
[markup language]: https://www.dokuwiki.org/wiki:syntax
[pandoc]: https://pandoc.org/

## Usage

* Install `pandoc`
* `python3 -m venv .venv`
* `source .venv/bin/activate`
* `pip install -r requirements.txt`
* `./wiki-link.py --help`

## Development

* Install Python (we target 3.9 to match our crusty prod LTS OS).
* `python3 -m venv .venv`
* `source .venv/bin/activate`
* `pip install -r requirements.txt -r dev-requirements.txt`
