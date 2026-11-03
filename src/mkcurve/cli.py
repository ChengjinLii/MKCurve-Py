"""Command-line entry point for the standalone Python port."""

import argparse
import json
import sys

from . import __version__
from .core import inspect_mkcurve_backend, run_mkcurve


def main(argv=None):
    parser = argparse.ArgumentParser(description="MK-Curve Python port (unofficial; research use only).")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Check installed backend resources and dependencies")
    run = sub.add_parser("run", help="Fit and correct a preprocessed diffusion MRI acquisition")
    for name in ("dwi", "bval", "bvec", "mask"):
        run.add_argument("--" + name, required=True)
    run.add_argument("--output-dir", required=True, help="New or empty directory, separate from inputs")
    run.add_argument("--b0-threshold", type=float, default=50.)
    run.add_argument("--max-bvalue", type=float, default=3000.)
    run.add_argument("--threshold", type=float, default=.5)
    run.add_argument("--grid", help="Optional text/CSV file with one increasing positive synthetic b0 per row")
    run.add_argument("--solver", choices=("reference", "batched"), default="reference")
    run.add_argument("--num-workers", type=int, default=1)
    run.add_argument("--worker-threads", type=int)
    run.add_argument("--voxels-per-chunk", type=int, default=64)
    run.add_argument("--chunk-schedule", choices=("dynamic", "ordered"), default="dynamic")
    args = parser.parse_args(argv)
    if args.command == "doctor":
        record = inspect_mkcurve_backend()
        print(json.dumps(record, indent=2))
        return 0 if record["available"] else 1
    options = vars(args).copy()
    options.pop("command")
    try:
        if args.grid:
            import numpy as np
            options["grid"] = np.loadtxt(args.grid, delimiter=",")
        else:
            options["grid"] = None
        record = run_mkcurve(**{name + "_path": options.pop(name) for name in ("dwi", "bval", "bvec", "mask")},
                             **options, log=lambda message: print(message, file=sys.stderr))
    except Exception as exc:
        print(f"mkcurve: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": record["status"], "record_path": record["record_path"],
                      "mask_voxels": record["mask_voxels"], "corrected_voxels": record["corrected_voxels"],
                      "automatic_qc_passed": record["automatic_qc_passed"],
                      "human_review": record["human_review"]}, indent=2))
    return 0
