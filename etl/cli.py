from dotenv import load_dotenv

load_dotenv()

import argparse  # noqa: E402
from pathlib import Path  # noqa: E402

from etl import config  # noqa: E402
from etl.extract import crawl, links  # noqa: E402
from etl.load import supabase  # noqa: E402


def main():
    p = argparse.ArgumentParser(prog="etl")
    sub = p.add_subparsers(required=True)

    c = sub.add_parser("crawl")
    c.add_argument("--links", type=Path, default=config.LINKS)
    c.add_argument("--out", type=Path, default=config.RAW)
    c.add_argument("--failed", type=Path, default=config.FAILED)
    c.add_argument("--harvest", action="store_true")
    c.set_defaults(fn=_crawl)

    l = sub.add_parser("load")
    l.add_argument("--src", type=Path, default=config.RAW)
    l.set_defaults(fn=_load)

    sub.add_parser("ping").set_defaults(fn=_ping)

    args = p.parse_args()
    args.fn(args)


def _crawl(args):
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    if args.harvest:
        links.harvest_all(out_path=args.links)
    crawl.run(links_path=args.links, out_path=args.out, failed_path=args.failed)


def _load(args):
    supabase.load(src_path=args.src)


def _ping(args):
    supabase.ping()


if __name__ == "__main__":
    main()
