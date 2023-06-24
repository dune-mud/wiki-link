#!/usr/bin/env python3

import argparse
import logging
import os
import pathlib


def log_init(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"invalid log level: {level}")
    logging.basicConfig(level=numeric_level)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="wiki-link",
        description="Renders DokuWiki from one place, to markdown in another",
    )
    parser.add_argument("wiki_src_dir")
    parser.add_argument("markdown_dest_dir")
    parser.add_argument("-l", "--log", default="info")
    args = parser.parse_args()

    src_path = pathlib.Path(args.wiki_src_dir).expanduser()
    if not src_path.is_dir():
        logging.error("wiki src dir must be a directory")
        exit(1)

    dest_path = pathlib.Path(args.markdown_dest_dir).expanduser()
    if not dest_path.is_dir():
        dest_path.mkdir()

    log_init(args.log)
    crawl(src_dir=src_path, dest_dir=dest_path)


def crawl(*, src_dir: pathlib.Path, dest_dir: pathlib.Path) -> None:
    logging.info(f"wiki-sync'ing from {src_dir} to {dest_dir}")

    for root, _, files in os.walk(src_dir, topdown=False):
        for name in filter(lambda f: f.endswith(".txt"), files):
            src_path = pathlib.Path(root, name)
            dest_path = pathlib.Path(dest_dir, src_path.relative_to(src_dir))

            logging.info(f"converting: {src_path} to {dest_path}")


if __name__ == "__main__":
    main()
