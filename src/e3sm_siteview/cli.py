import argparse
import json
from pathlib import Path

from e3sm_siteview import __version__


def read_state_file(path):
    """argparse type: content of a state file"""
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        msg = f"can't read state file ({e})"
        raise argparse.ArgumentTypeError(msg) from e


def configure_and_parse(parser):
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--cf", help="the nc file with connectivity information")
    parser.add_argument("--df", nargs="+", help="the nc file with data/variables")
    parser.add_argument(
        "--state",
        type=read_state_file,
        help="state file to restore, its data files are used without --cf/--df",
    )
    parser.add_argument(
        "--perf",
        dest="perf",
        action="store_true",
        help="Emit performance timing on stderr ([PERF] lines). Used to "
        "diagnose where slider-tick cost is going — reader I/O, pipeline, "
        "rendering, web layer, etc.",
    )

    args = parser.parse_known_args()[0]
    if args.state:
        args.cf = args.cf or args.state["files"]["connectivity"]
        args.df = args.df or args.state["files"]["data"]
    if not (args.cf and args.df):
        parser.error("--cf and --df are required, unless given by --state")

    return args
