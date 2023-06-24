#!/usr/bin/env python3

import argparse
import logging


def log_init(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"invalid log level: {level}")
    logging.basicConfig(level=numeric_level)


def main(*, wiki_src: str, markdown_dest: str) -> None:
    logging.info(f"wiki-sync'ing from {wiki_src} to {markdown_dest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="wiki-link",
        description="Renders DokuWiki from one place, to markdown in another",
    )
    parser.add_argument("wiki_src_dir")
    parser.add_argument("markdown_dest_dir")
    parser.add_argument("-l", "--log", default="info")
    args = parser.parse_args()

    log_init(args.log)
    main(wiki_src=args.wiki_src_dir, markdown_dest=args.markdown_dest_dir)
