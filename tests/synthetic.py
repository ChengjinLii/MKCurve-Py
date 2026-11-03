# Adapted from SlicerDSpace synthetic DKI tests, BSD-3-Clause.
"""Analytic, constant-directional-kurtosis signals, without a DIPY dependency."""

from pathlib import Path

import nibabel as nib
import numpy as np

AFFINE = np.array([[-1.25, 0, 0, 8], [0, 1.5, 0, -11], [0, 0, 2, 4], [0, 0, 0, 1]], dtype=float)
SPATIAL_SHAPE = (2, 3, 2)


def synthetic_case(*, noisy=False):
    directions = np.random.default_rng(80123).normal(size=(30, 3))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    bvals = np.r_[np.zeros(4), np.repeat([1000., 2000., 3000.], 30)]
    bvecs = np.vstack((np.zeros((4, 3)), np.tile(directions, (3, 1))))
    data = np.empty((*SPATIAL_SHAPE, len(bvals)), dtype=np.float64)
    eigenvalues = np.empty((*SPATIAL_SHAPE, 3))
    kurtosis = np.empty(SPATIAL_SHAPE)
    for index, coordinate in enumerate(np.ndindex(SPATIAL_SHAPE)):
        evals = np.array([.0012, .0008, .0005]) * (1 + index / 50)
        k = .4 + index / 40
        adc = bvecs ** 2 @ evals
        data[coordinate] = (1000 + 17 * index) * np.exp(-bvals * adc + bvals ** 2 * k * adc ** 2 / 6)
        eigenvalues[coordinate], kurtosis[coordinate] = evals, k
    if noisy:
        data *= np.exp(np.random.default_rng(3021).normal(0, .025, size=data.shape))
    mask = np.ones(SPATIAL_SHAPE, dtype=np.uint8)
    mask[0, 0, 0] = 0
    return {"data": data, "bvals": bvals, "bvecs": bvecs, "mask": mask,
            "eigenvalues": eigenvalues, "kurtosis": kurtosis}


def write_case(root, case):
    inputs = Path(root) / "input"
    inputs.mkdir(parents=True, exist_ok=True)
    paths = {"dwi": inputs / "data.nii.gz", "bval": inputs / "bvals", "bvec": inputs / "bvecs",
             "mask": inputs / "nodif_brain_mask.nii.gz"}
    nib.save(nib.Nifti1Image(case["data"], AFFINE), paths["dwi"])
    nib.save(nib.Nifti1Image(case["mask"], AFFINE), paths["mask"])
    np.savetxt(paths["bval"], case["bvals"][None, :], fmt="%.12g")
    np.savetxt(paths["bvec"], case["bvecs"].T, fmt="%.12g")
    return paths
