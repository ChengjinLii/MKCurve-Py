"""Generate a tiny synthetic acquisition and run the real MK-Curve algorithm."""

import argparse
from pathlib import Path

import nibabel as nib
import numpy as np

from mkcurve import run_mkcurve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/synthetic-demo"))
    args = parser.parse_args()
    root = args.output_root
    root.mkdir(parents=True, exist_ok=False)
    directions = np.random.default_rng(42).normal(size=(30, 3))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    bvals = np.r_[0., np.repeat([1000., 2000., 3000.], 30)]
    bvecs = np.vstack((np.zeros((1, 3)), np.tile(directions, (3, 1))))
    adc = bvecs ** 2 @ np.array([.0012, .0008, .0005])
    signal = 1000 * np.exp(-bvals * adc + bvals ** 2 * .6 * adc ** 2 / 6)
    signal[0] = 650.  # Deliberate baseline perturbation, not an acquired scan.
    data = np.broadcast_to(signal, (2, 2, 1, len(signal))).copy()
    dwi, bval, bvec, mask = [root / name for name in ("dwi.nii.gz", "dwi.bval", "dwi.bvec", "mask.nii.gz")]
    nib.save(nib.Nifti1Image(data, np.eye(4)), dwi)
    nib.save(nib.Nifti1Image(np.ones(data.shape[:3], dtype=np.uint8), np.eye(4)), mask)
    np.savetxt(bval, bvals[None, :])
    np.savetxt(bvec, bvecs.T)
    record = run_mkcurve(dwi, bval, bvec, mask, root / "fit", log=print)
    print(record["record_path"])
    print("SYNTHETIC ONLY. Inspect validity masks; this is not clinical validation.")


if __name__ == "__main__":
    main()
