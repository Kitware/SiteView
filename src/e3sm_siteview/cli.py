def configure_and_parse(parser):
    parser.add_argument(
        "-cf",
        help="the nc file with connnectivity information",
    )
    parser.add_argument(
        "-df",
        nargs="+",
        help="the nc file with data/variables",
    )
    parser.add_argument(
        "--perf",
        dest="perf",
        action="store_true",
        help="Emit performance timing on stderr ([PERF] lines). Used to "
        "diagnose where slider-tick cost is going — reader I/O, pipeline, "
        "rendering, web layer, etc.",
    )

    return parser.parse_known_args()[0]
