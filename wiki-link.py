#!/usr/bin/env python3

import argparse
import logging
import os
import pathlib
import shlex
import shutil
import subprocess


def log_init(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"invalid log level: {level}")
    logging.basicConfig(level=numeric_level)


def main() -> None:
    args = parse_args()

    log_init(args.log)

    src_path = pathlib.Path(args.wiki_src_dir).expanduser()
    if not src_path.is_dir():
        logging.error("wiki src dir must be a directory")
        exit(1)

    dest_path = pathlib.Path(args.markdown_dest_dir).expanduser()
    if not dest_path.is_dir():
        dest_path.mkdir()

    pandoc_cmd: str = "pandoc"
    if not args.pandoc and shutil.which(pandoc_cmd) is None:
        logging.error("pandoc is not in $PATH - install it first")
    elif args.pandoc:
        pandoc_path = pathlib.Path(args.pandoc).expanduser()
        if not pandoc_path.is_file():
            logging.error("--pandoc must be a file")
            exit(1)
        pandoc_cmd = str(args.pandoc)

    if args.bulk:
        logging.info(f"bulk converting {src_path} to {dest_path}")
        crawl(src_dir=src_path, dest_dir=dest_path, pandoc_cmd=pandoc_cmd)

    if args.watch:
        logging.info(f"watching {src_path} for changes")
        watch(src_dir=src_path, dest_dir=dest_path, pandoc_cmd=pandoc_cmd)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="wiki-link",
        description="Renders DokuWiki from one place, to markdown in another",
    )
    parser.add_argument("wiki_src_dir")
    parser.add_argument("markdown_dest_dir")
    parser.add_argument(
        "-l", "--log", default="info", help="log level (info, debug, etc)"
    )
    parser.add_argument(
        "-b",
        "--bulk",
        default=True,
        help="Bulk convert all src files at startup",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "-w",
        "--watch",
        default=True,
        help="Watch src directory to auto-convert changed files",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "-p",
        "--pandoc",
        default=None,
        help="path to a pandoc binary, if omitted $PATH is used",
    )
    return parser.parse_args()


def crawl(
    *, src_dir: pathlib.Path, dest_dir: pathlib.Path, pandoc_cmd: str
) -> None:
    for root, _, files in os.walk(src_dir, topdown=False):
        for name in filter(lambda f: f.endswith(".txt"), files):
            src_path = pathlib.Path(root, name)
            dest_path = pathlib.Path(dest_dir, src_path.relative_to(src_dir))
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            logging.info(f"converting: {src_path} to {dest_path}")
            pandoc_convert(
                src_path=src_path, dest_path=dest_path, pandoc_cmd=pandoc_cmd
            )


def watch(
    *, src_dir: pathlib.Path, dest_dir: pathlib.Path, pandoc_cmd: str
) -> None:
    pass


def pandoc_convert(
    *, src_path: pathlib.Path, dest_path: pathlib.Path, pandoc_cmd: str
) -> None:
    cmd = f"{pandoc_cmd} --from=dokuwiki  --to=gfm {src_path}"
    logging.debug(f"running: {cmd}")
    try:
        proc = subprocess.run(
            shlex.split(cmd), shell=False, capture_output=True, check=True
        )
        with open(dest_path, "wb+") as f:
            f.write(proc.stdout)
    except subprocess.CalledProcessError:
        logging.error(f"failed to convert {src_path}")


if __name__ == "__main__":
    main()
