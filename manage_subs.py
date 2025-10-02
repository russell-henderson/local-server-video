# manage_subs.py
import argparse
import multiprocessing
import os
import sys
from datetime import datetime

from subtitles import (
    generate_for_file,
    generate_missing,
    has_any_subs,
    iter_video_files,
    within_quiet_hours
)


def check_cmd(args):
    found = []
    missing = []
    for vid_path in iter_video_files(args.root):
        if has_any_subs(vid_path):
            found.append(vid_path)
        else:
            missing.append(vid_path)

    print(f"Found subtitles: {len(found)}")
    print(f"Missing subtitles: {len(missing)}")
    if args.verbose:
        for m in missing:
            print(f"  MISSING: {m}")


def generate_cmd(args):
    if args.quiet_check and within_quiet_hours():
        print(f"In quiet hours, skipping generation at {datetime.now()}")
        return

    if args.file:
        result = generate_for_file(args.file)
        print(f"Generated: {result}")
    else:
        results = generate_missing(args.root)
        print(f"Generated subtitles for {len(results)} files")
        if args.verbose:
            for r in results:
                print(f"  {r['file']} -> {r['outputs']}")


def batch_cmd(args):
    if args.quiet_check and within_quiet_hours():
        now = datetime.now()
        print(f"In quiet hours, skipping batch generation at {now}")
        return

    video_files = [p for p in iter_video_files(args.root)
                   if not has_any_subs(p)]
    if not video_files:
        print("No files need subtitle generation")
        return

    worker_count = args.workers
    print(f"Batch processing {len(video_files)} files "
          f"with {worker_count} workers")

    if args.workers == 1:
        for vid_path in video_files:
            result = generate_for_file(vid_path)
            print(f"Generated: {result['file']}")
    else:
        with multiprocessing.Pool(args.workers) as pool:
            results = pool.map(generate_for_file, video_files)
            for r in results:
                print(f"Generated: {r['file']}")


def main():
    parser = argparse.ArgumentParser(description="Manage subtitle generation")
    parser.add_argument("--root", default="videos",
                        help="Root video directory")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # check command
    subparsers.add_parser("check", help="Check subtitle status")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate subtitles")
    gen_parser.add_argument("--file", help="Generate for specific file")
    gen_parser.add_argument("--quiet-check", action="store_true",
                            help="Skip generation during quiet hours")

    # batch command
    batch_parser = subparsers.add_parser("batch",
                                         help="Batch generate subtitles")
    batch_parser.add_argument("--workers", type=int, default=1,
                              help="Number of parallel workers")
    batch_parser.add_argument("--quiet-check", action="store_true",
                              help="Skip generation during quiet hours")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if not os.path.exists(args.root):
        print(f"Error: Root directory '{args.root}' does not exist")
        sys.exit(1)

    if args.command == "check":
        check_cmd(args)
    elif args.command == "generate":
        generate_cmd(args)
    elif args.command == "batch":
        batch_cmd(args)


if __name__ == "__main__":
    main()
