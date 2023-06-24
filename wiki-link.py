#!/usr/bin/env python3

import argparse
import logging
import os
import pathlib
import shlex
import shutil
import subprocess

import watchdog.events
import watchdog.observers


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

    if not args.bulk and not args.watch:
        logging.error("one of --bulk or --watch must be provided")
        exit(1)

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
    parser.add_argument(
        "wiki_src_dir", help="directory with DokuWiki page content"
    )
    parser.add_argument(
        "markdown_dest_dir", help="directory for Markdown page content"
    )
    parser.add_argument(
        "-l", "--log", default="info", help="log level (info, debug, etc)"
    )
    parser.add_argument(
        "-b",
        "--bulk",
        help="Bulk convert all src files at startup",
        action="store_true",
    )
    parser.add_argument(
        "--no-bulk",
        dest="bulk",
        help="Skip bulk converting all src files at startup",
        action="store_false",
    )
    parser.add_argument(
        "-w",
        "--watch",
        help="Watch src directory to auto-convert changed files",
        action="store_true",
    )
    parser.add_argument(
        "--no-watch",
        dest="watch",
        help="Skip watching src directory to auto-convert changed files",
        action="store_false",
    )
    parser.set_defaults(bulk=True, watch=True)
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
            doku_file = pathlib.Path(root, name)
            md_file = output_path(
                src_dir=src_dir, dest_dir=dest_dir, path=doku_file
            )
            md_file.parent.mkdir(parents=True, exist_ok=True)

            logging.info(f"converting: {doku_file} to {md_file}")
            pandoc_convert(
                doku_file=doku_file, md_file=md_file, pandoc_cmd=pandoc_cmd
            )


def watch(
    *, src_dir: pathlib.Path, dest_dir: pathlib.Path, pandoc_cmd: str
) -> None:
    event_handler = PandocEventHandler(
        src_dir=src_dir, dest_dir=dest_dir, pandoc_cmd=pandoc_cmd
    )
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, str(src_dir), recursive=True)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        logging.info("exiting for keyboard interrupt")
    finally:
        observer.stop()
        observer.join()


class PandocEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(
        self, src_dir: pathlib.Path, dest_dir: pathlib.Path, pandoc_cmd: str
    ):
        super().__init__()

        self.src_dir = src_dir
        self.dest_dir = dest_dir
        self.pandoc_cmd = pandoc_cmd

    def on_moved(self, event: watchdog.events.FileMovedEvent) -> None:
        super().on_moved(event)
        # K.I.S.S - we don't expect DokuWiki to atomically move pages,
        # just create new ones and remove old ones.

    def on_created(self, event: watchdog.events.FileCreatedEvent) -> None:
        super().on_created(event)

        event_path = pathlib.Path(event.src_path)
        out_path = output_path(
            src_dir=self.src_dir, dest_dir=self.dest_dir, path=event_path
        )
        if event.is_directory:
            logging.info(f"creating dir {out_path}")
            out_path.mkdir(parents=True, exist_ok=True)
        else:
            logging.info(f"converting {event_path} to {out_path}")
            pandoc_convert(
                doku_file=event_path,
                md_file=out_path,
                pandoc_cmd=self.pandoc_cmd,
            )

    def on_deleted(self, event: watchdog.events.FileDeletedEvent) -> None:
        super().on_deleted(event)

        event_path = pathlib.Path(event.src_path)
        out_path = output_path(
            src_dir=self.src_dir, dest_dir=self.dest_dir, path=event_path
        )
        logging.info(f"deleting {out_path}")
        if event.is_directory:
            shutil.rmtree(out_path, ignore_errors=True)
        else:
            out_path.unlink(missing_ok=True)

    def on_modified(self, event: watchdog.events.FileModifiedEvent) -> None:
        super().on_modified(event)
        if event.is_directory:
            return

        event_path = pathlib.Path(event.src_path)
        out_path = output_path(
            src_dir=self.src_dir, dest_dir=self.dest_dir, path=event_path
        )
        logging.info(f"converting {event_path} to {out_path}")
        pandoc_convert(
            doku_file=event_path,
            md_file=out_path,
            pandoc_cmd=self.pandoc_cmd,
        )


def output_path(
    *,
    src_dir: pathlib.Path,
    dest_dir: pathlib.Path,
    path: pathlib.Path,
) -> pathlib.Path:
    dest_path = pathlib.Path(dest_dir, path.relative_to(src_dir))
    return dest_path


def pandoc_convert(
    *, doku_file: pathlib.Path, md_file: pathlib.Path, pandoc_cmd: str
) -> None:
    cmd = f"{pandoc_cmd} --from=dokuwiki --to=gfm {doku_file}"
    logging.debug(f"running: {cmd}")
    try:
        proc = subprocess.run(
            shlex.split(cmd), shell=False, capture_output=True, check=True
        )
        with open(md_file, "wb+") as f:
            f.write(proc.stdout)
    except subprocess.CalledProcessError:
        logging.error(f"failed to convert {doku_file}")


if __name__ == "__main__":
    main()
