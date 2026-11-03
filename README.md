<div align="center">

# MKCurve-Py

**A native Python implementation of MK-Curve for robust diffusion kurtosis imaging.**

[![Python](https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white)](#key-dependencies)
[![NumPy](https://img.shields.io/badge/Numerics-NumPy-013243?logo=numpy&logoColor=white)](#key-dependencies)
[![SciPy](https://img.shields.io/badge/Solver-SciPy-8CAAE6?logo=scipy&logoColor=white)](#key-dependencies)
[![NiBabel](https://img.shields.io/badge/Imaging-NiBabel-4D7EB3)](#key-dependencies)

[Publication](#publication) | [Overview](#overview) | [Installation](#installation) | [Run MK-Curve](#run-mk-curve) | [Outputs](#outputs) | [Tests](#tests) | [License](#license)

</div>

MKCurve-Py is a standalone Python implementation of MK-Curve based on the
MATLAB code by Fan Zhang and collaborators and the Python translation
developed in SlicerDSpace. It provides a Python API and command-line interface
built on NumPy, SciPy and NiBabel.

**Preprocessed multi-shell diffusion MRI in. Original and b0-corrected
tensor/kurtosis maps, full MK curves, validity masks and provenance out.**

---

## Publication

If you use MKCurve-Py in research, please cite the original MK-Curve paper:

> Fan Zhang, Lipeng Ning, Lauren J. O'Donnell and Ofer Pasternak.
> [MK-curve - Characterizing the relation between mean kurtosis and alterations
> in the diffusion MRI signal.](https://doi.org/10.1016/j.neuroimage.2019.04.015)
> *NeuroImage* **196**, 68-80 (2019).

Original MATLAB code:
[zhangfanmark/MK-Curve](https://github.com/zhangfanmark/MK-Curve), pinned source
[`9a213e1a5850fe50c998793f31ed852df00242f8`](https://github.com/zhangfanmark/MK-Curve/tree/9a213e1a5850fe50c998793f31ed852df00242f8).
[CITATION.cff](CITATION.cff) records the software and preferred paper citation.

### Citation (BibTeX)

```bibtex
@article{Zhang2019MKCurve,
  author  = {Zhang, Fan and Ning, Lipeng and O'Donnell, Lauren J. and Pasternak, Ofer},
  title   = {MK-curve - Characterizing the relation between mean kurtosis
             and alterations in the diffusion MRI signal},
  journal = {NeuroImage},
  year    = {2019},
  volume  = {196},
  pages   = {68--80},
  doi     = {10.1016/j.neuroimage.2019.04.015}
}
```

---

## Overview

```text
DWI + bval + bvec + binary mask
 -> baseline averaging and complete-shell selection
 -> working-copy nonpositive/nonfinite signal repair
 -> unconstrained predicted-weight DKI WLLS
 -> MK over a synthetic b0 grid (256 original integration directions)
 -> abnormal/unusual-curve detection
 -> b0 correction and WLLS refit
 -> raw maps + validity masks + full curves + run record
```

The fit uses OLS initialization, **predicted-signal weights** and one weighted
solve. It retains raw diffusion eigenvalues and kurtosis values, with separate
validity masks and unsmoothed parameter maps. Bad input signals are repaired
sequentially from positive local neighbors in a working copy, following the
author policy. Repair counts are recorded.

### Implementation Notes

The Python translation originated in
[SlicerDSpace](https://github.com/ChengjinLii/SlicerDSpace), snapshot
`57b044f54411b84230564fdcef18c469742569c7`.
[provenance.json](provenance.json) records source paths and SHA-256 hashes.
The tensor core and 256-direction table match that snapshot.

This modified implementation adapts the original MATLAB workflow as follows:
- Baselines use caller-defined `b <= 50 s/mm^2` by default and are averaged.
- Complete shells (100 s/mm^2 tolerance anchored at the smallest b-value)
  are selected by their median, at most 3000 s/mm^2 by default.
  The upper b-value limit applies to shell medians.
- The adaptive integer grid is determined by baseline signal values.
- Radial integration is defined at principal-axis poles.
- Nonfinite curves receive an invalid-curve mask.
- The Python layer adds input preparation, bounded chunk scheduling,
  per-metric validity masks and provenance records.

---

## Installation

```bash
git clone https://github.com/ChengjinLii/MKCurve-Py.git
cd MKCurve-Py
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
mkcurve doctor
```

For development: `python -m pip install -e ".[test]"`.
The console command and `python -m mkcurve` work outside the checkout.

### Key Dependencies

| Dependency | Requirement | Purpose |
| --- | --- | --- |
| Python | >= 3.10 | Runtime |
| NumPy | >= 1.24 | Tensor algebra, disk-backed arrays |
| SciPy | >= 1.10 | Pivoted QR and LAPACK |
| NiBabel | >= 5.1 | NIfTI I/O |
| threadpoolctl | >= 3.1 | BLAS thread limits |
| pytest | >= 7, test extra only | Synthetic regressions |

`mkcurve doctor` reports installed versions, resources and source hashes.

---

## Inputs

Provide motion/eddy/susceptibility-corrected DWI with correspondingly rotated
gradients and an aligned binary mask. Preprocessing, mask generation and
resampling are separate steps.

```text
inputs/
  dwi.nii.gz     # 4D NIfTI; .nii also accepted
  dwi.bval      # N b-values in s/mm^2
  dwi.bvec      # FSL 3 x N or N x 3
  mask.nii.gz    # finite, nonempty, binary 3D mask on the same grid
```

Mask and DWI must share shape and affine. A baseline and enough independent
multi-shell measurements for a full-rank 22-column DKI design are required.
Weighted directions must be meaningful; nonzero vectors are normalized
during design construction. Diffusivities are mm^2/s; kurtosis and FA
are dimensionless.

**Signal scale matters.** The adaptive b0 grid uses integer signal values.
For normalized signals near 1, rescale the acquisition explicitly or provide a
custom grid in the same signal units. Signal intensities are used as supplied.

---

## Run MK-Curve

### Quick Start

```bash
mkcurve run \
  --dwi ./inputs/dwi.nii.gz \
  --bval ./inputs/dwi.bval \
  --bvec ./inputs/dwi.bvec \
  --mask ./inputs/mask.nii.gz \
  --output-dir ./outputs/subject01
```

Use a **new or empty output directory**, separate from all inputs. Nonempty
outputs, including failed runs, are refused. Source inputs remain unchanged,
with hashes recorded before and after fitting. Use separate output directories
for concurrent jobs.

### Common Options

| Option | Default / Meaning |
| --- | --- |
| `--threshold 0.5` | Interpolation from zero-MK to maximum-MK b0; [0,1]. |
| `--b0-threshold 50` | Baseline cutoff, s/mm^2. |
| `--max-bvalue 3000` | Upper shell-median cutoff, s/mm^2. |
| `--grid grid.csv` | One positive increasing b0 per row; at least 3 rows. |
| `--solver reference` | Pivoted-QR weighted solves; default. |
| `--solver batched` | Optional normal systems with QR fallback; numerical differences possible. |
| `--num-workers 2` | Spawned CPU workers; default 1. |
| `--worker-threads 1` | BLAS threads per worker; implicit 1 when workers > 1. |
| `--voxels-per-chunk 64` | Chunk size. |
| `--chunk-schedule dynamic` | Bounded completion-driven scheduling; `ordered` also available. |

Custom-grid CLI template:

```bash
python -c 'import numpy as np; np.savetxt("grid.csv", np.arange(100., 2001., 10.), delimiter=",")'
python -m mkcurve run \
  --dwi ./inputs/dwi.nii.gz --bval ./inputs/dwi.bval \
  --bvec ./inputs/dwi.bvec --mask ./inputs/mask.nii.gz \
  --output-dir ./outputs/subject01-custom \
  --grid grid.csv --num-workers 2 --worker-threads 1
```

That grid is only a template; choose bounds consistent with your signal scale.

### Python API

```python
from mkcurve import run_mkcurve

record = run_mkcurve(
    "inputs/dwi.nii.gz", "inputs/dwi.bval", "inputs/dwi.bvec",
    "inputs/mask.nii.gz", "outputs/subject01-api",
    solver="reference", num_workers=1,
)
print(record["maps"]["corrected_mk"])
```

Use an `if __name__ == "__main__":` guard in scripts with
`num_workers > 1` because workers use Python's spawn context.

### Synthetic Demo

From the checkout after installation:

```bash
python examples/synthetic_demo.py --output-root outputs/synthetic-demo
```

This generates a tiny artificial acquisition with a perturbed baseline and
runs the actual algorithm. Use a fresh directory on reruns.

---

## Outputs

| File(s) | Meaning |
| --- | --- |
| `mkcurve_original_{fa,md,ad,rd,mk,ak,rk,e1,e2,e3}.nii.gz` | Untruncated original maps. |
| `mkcurve_corrected_{fa,md,ad,rd,mk,ak,rk,e1,e2,e3}.nii.gz` | Untruncated corrected maps. |
| `mkcurve_{original,corrected}_*_valid_mask.nii.gz` | Per-metric validity. |
| `mkcurve_{original,corrected}_valid_mask.nii.gz` | Legacy joint validity. |
| `mkcurve_{original,corrected}_nrmse.nii.gz` | Normalized residuals. |
| `mkcurve_{abnormal,unusual,curve_valid}_mask.nii.gz` | Detection/curve masks. |
| `mkcurve_{zero_mk_b0,max_mk_b0,max_mk,corrected_b0}.nii.gz` | Curve landmarks and baseline. |
| `synthetic_b0_grid.csv` | Exact grid in input signal units. |
| `mk_vs_synthetic_b0.npy` | Float64: grid samples x masked voxels. |
| `original_coefficients.npy`, `corrected_coefficients.npy` | Float64: masked voxels x 22. |
| `mkcurve_record.json` | Status, settings, hashes, repair counts, outputs, QC. |
| `mkcurve_progress.json` | Running/completed/failed progress. |

Voxel order is **MATLAB/Fortran**. Reconstruct indices with
`np.unravel_index(np.flatnonzero(mask.ravel(order="F")), mask.shape, order="F")`.
Coefficients are log(S0), six diffusion entries (xx,xy,xz,yy,yz,zz), and
fifteen **unnormalized** symmetric fourth-order entries in lexicographic
`combinations_with_replacement(range(3), 4)` order.

Maps are float32, masks uint8, with the input affine; outside-mask values are
zero. Invalid in-mask values remain raw and may be nonfinite. Select fitted
voxels using validity masks.

Per-metric bounds: FA [0,1], kurtosis [0,3], diffusion [0,0.005], with finite
fit/curve/residual and positive diffusion eigenvalues. The retained legacy
joint gate checks all maps together and is distinct from per-metric checks.
Metric-specific masks let MK remain eligible when RK fails.
These ranges govern validity masks; fitted values remain unchanged.

The CLI exits nonzero on failure, including zero jointly valid corrected
voxels. Partial invalidity can exit zero: **inspect masks,
`automatic_qc_passed` and `human_review`**. Human review stays `pending`;
review the results before analysis. After a failure, use the run record to
distinguish partial artifacts from completed outputs.

Curve storage alone requires roughly `8 * grid_samples * mask_voxels` bytes,
in addition to temporary float64 signal volumes and map buffers.
Plan disk space and runtime for the grid size and number of masked voxels.

---

## Tests

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m unittest discover -s tests
```

Tests cover analytic synthetic map recovery, predicted weights, detection
indexing, invalid input, repair, chunk/parallel equivalence, QR fallback,
log reuse, geometry, input immutability and CLI behavior.
Executed local environments and results are recorded in
[VALIDATION.md](VALIDATION.md). Run the tests locally with the commands above.

The inherited [synthetic fixture](tests/fixtures/mkcurve_author_octave.json)
records previous outputs of unmodified author routines in GNU Octave 7.3.0.
Its upstream commit and reference-output SHA-256 are preserved. Current tests
compare results against that stored artifact.
[The harness](tests/mkcurve_author_reference.m) needs a separately obtained
author checkout and prepared MAT input.

---

## License

Licenses apply by component:
- Workflow translation: original BWH MK-Curve terms in [LICENSE](LICENSE)
  and [licenses/MK-Curve-LICENSE.txt](licenses/MK-Curve-LICENSE.txt).
- DKI tensor translation and direction table: MPL-2.0, Copyright (c) 2017
  New York University and University of Antwerp; source ships with the package.
  See [full MPL-2.0](licenses/MK-Curve-DKI-MPL-2.0.txt).
- SlicerDSpace input/I/O/scheduling/test infrastructure and new packaging:
  [BSD-3-Clause](licenses/BSD-3-Clause.txt).

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) provides file-level scope
and modifications. Dependencies retain their own licenses.

All or portions of this licensed product (such portions are the "Software")
have been obtained under license from The Brigham and Women's Hospital, Inc.
and are subject to the following terms and conditions:

<details>
<summary>Full original MK-Curve Contribution and Software License Agreement</summary>

```text
The MK-Curve license below is a BSD style license, with extensions
to cover contributions and other issues specific to MK-Curve. It is
inpsired by [3D Slicer License](https://github.com/Slicer/Slicer/blob/master/License.txt).

MK-Curve Contribution and Software License Agreement ("Agreement")
Version 1.0 (June, 2019)

This Agreement covers contributions to and downloads from the
MK-Curve project ("MK-Curve") maintained by The Brigham and Women's
Hospital, Inc. ("Brigham"). Part A of this Agreement applies to
contributions of software and/or data to MK-Curve (including making
revisions of or additions to code and/or data already in MK-Curve). Part
B of this Agreement applies to downloads of software and/or data from
MK-Curve. Part C of this Agreement applies to all transactions with
MK-Curve. If you distribute Software (as defined below) downloaded from
MK-Curve, all of the paragraphs of Part B of this Agreement must be
included with and apply to such Software.

Your contribution of software and/or data to MK-Curve (including prior
to the date of the first publication of this Agreement, each a
"Contribution") and/or downloading, copying, modifying, displaying,
distributing or use of any software and/or data from MK-Curve
(collectively, the "Software") constitutes acceptance of all of the
terms and conditions of this Agreement. If you do not agree to such
terms and conditions, you have no right to contribute your
Contribution, or to download, copy, modify, display, distribute or use
the Software.

PART A. CONTRIBUTION AGREEMENT - License to Brigham with Right to
Sublicense ("Contribution Agreement").

1. As used in this Contribution Agreement, "you" means the individual
   contributing the Contribution to MK-Curve and the institution or
   entity which employs or is otherwise affiliated with such
   individual in connection with such Contribution.

2. This Contribution Agreement applies to all Contributions made to
   MK-Curve, including without limitation Contributions made prior to
   the date of first publication of this Agreement. If at any time you
   make a Contribution to MK-Curve, you represent that (i) you are
   legally authorized and entitled to make such Contribution and to
   grant all licenses granted in this Contribution Agreement with
   respect to such Contribution; (ii) if your Contribution includes
   any patient data, all such data is de-identified in accordance with
   U.S. confidentiality and security laws and requirements, including
   but not limited to the Health Insurance Portability and
   Accountability Act (HIPAA) and its regulations, and your disclosure
   of such data for the purposes contemplated by this Agreement is
   properly authorized and in compliance with all applicable laws and
   regulations; and (iii) you have preserved in the Contribution all
   applicable attributions, copyright notices and licenses for any
   third party software or data included in the Contribution.

3. Except for the licenses granted in this Agreement, you reserve all
   right, title and interest in your Contribution.

4. You hereby grant to Brigham, with the right to sublicense, a
   perpetual, worldwide, non-exclusive, no charge, royalty-free,
   irrevocable license to use, reproduce, make derivative works of,
   display and distribute the Contribution. If your Contribution is
   protected by patent, you hereby grant to Brigham, with the right to
   sublicense, a perpetual, worldwide, non-exclusive, no-charge,
   royalty-free, irrevocable license under your interest in patent
   rights covering the Contribution, to make, have made, use, sell and
   otherwise transfer your Contribution, alone or in combination with
   any other code.

5. You acknowledge and agree that Brigham may incorporate your
   Contribution into MK-Curve and may make MK-Curve available to members
   of the public on an open source basis under terms substantially in
   accordance with the Software License set forth in Part B of this
   Agreement. You further acknowledge and agree that Brigham shall
   have no liability arising in connection with claims resulting from
   your breach of any of the terms of this Agreement.

6. YOU WARRANT THAT TO THE BEST OF YOUR KNOWLEDGE YOUR CONTRIBUTION
   DOES NOT CONTAIN ANY CODE THAT REQURES OR PRESCRIBES AN "OPEN
   SOURCE LICENSE" FOR DERIVATIVE WORKS (by way of non-limiting
   example, the GNU General Public License or other so-called
   "reciprocal" license that requires any derived work to be licensed
   under the GNU General Public License or other "open source
   license").

PART B. DOWNLOADING AGREEMENT - License from Brigham with Right to
Sublicense ("Software License").

1. As used in this Software License, "you" means the individual
   downloading and/or using, reproducing, modifying, displaying and/or
   distributing the Software and the institution or entity which
   employs or is otherwise affiliated with such individual in
   connection therewith. The Brigham and Women's Hospital,
   Inc. ("Brigham") hereby grants you, with right to sublicense, with
   respect to Brigham's rights in the software, and data, if any,
   which is the subject of this Software License (collectively, the
   "Software"), a royalty-free, non-exclusive license to use,
   reproduce, make derivative works of, display and distribute the
   Software, provided that:

(a) you accept and adhere to all of the terms and conditions of this
Software License;

(b) in connection with any copy of or sublicense of all or any portion
of the Software, all of the terms and conditions in this Software
License shall appear in and shall apply to such copy and such
sublicense, including without limitation all source and executable
forms and on any user documentation, prefaced with the following
words: "All or portions of this licensed product (such portions are
the "Software") have been obtained under license from The Brigham and
Women's Hospital, Inc. and are subject to the following terms and
conditions:"

(c) you preserve and maintain all applicable attributions, copyright
notices and licenses included in or applicable to the Software;

(d) modified versions of the Software must be clearly identified and
marked as such, and must not be misrepresented as being the original
Software; and

(e) you consider making, but are under no obligation to make, the
source code of any of your modifications to the Software freely
available to others on an open source basis.

2. The license granted in this Software License includes without
   limitation the right to (i) incorporate the Software into
   proprietary programs (subject to any restrictions applicable to
   such programs), (ii) add your own copyright statement to your
   modifications of the Software, and (iii) provide additional or
   different license terms and conditions in your sublicenses of
   modifications of the Software; provided that in each case your use,
   reproduction or distribution of such modifications otherwise
   complies with the conditions stated in this Software License.

3. This Software License does not grant any rights with respect to
   third party software, except those rights that Brigham has been
   authorized by a third party to grant to you, and accordingly you
   are solely responsible for (i) obtaining any permissions from third
   parties that you need to use, reproduce, make derivative works of,
   display and distribute the Software, and (ii) informing your
   sublicensees, including without limitation your end-users, of their
   obligations to secure any such required permissions.

4. The Software has been designed for research purposes only and has
   not been reviewed or approved by the Food and Drug Administration
   or by any other agency. YOU ACKNOWLEDGE AND AGREE THAT CLINICAL
   APPLICATIONS ARE NEITHER RECOMMENDED NOR ADVISED. Any
   commercialization of the Software is at the sole risk of the party
   or parties engaged in such commercialization. You further agree to
   use, reproduce, make derivative works of, display and distribute
   the Software in compliance with all applicable governmental laws,
   regulations and orders, including without limitation those relating
   to export and import control.

5. The Software is provided "AS IS" and neither Brigham nor any
   contributor to the software (each a "Contributor") shall have any
   obligation to provide maintenance, support, updates, enhancements
   or modifications thereto. BRIGHAM AND ALL CONTRIBUTORS SPECIFICALLY
   DISCLAIM ALL EXPRESS AND IMPLIED WARRANTIES OF ANY KIND INCLUDING,
   BUT NOT LIMITED TO, ANY WARRANTIES OF MERCHANTABILITY, FITNESS FOR
   A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL
   BRIGHAM OR ANY CONTRIBUTOR BE LIABLE TO ANY PARTY FOR DIRECT,
   INDIRECT, SPECIAL, INCIDENTAL, EXEMPLARY OR CONSEQUENTIAL DAMAGES
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY ARISING IN ANY WAY
   RELATED TO THE SOFTWARE, EVEN IF BRIGHAM OR ANY CONTRIBUTOR HAS
   BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. TO THE MAXIMUM
   EXTENT NOT PROHIBITED BY LAW OR REGULATION, YOU FURTHER ASSUME ALL
   LIABILITY FOR YOUR USE, REPRODUCTION, MAKING OF DERIVATIVE WORKS,
   DISPLAY, LICENSE OR DISTRIBUTION OF THE SOFTWARE AND AGREE TO
   INDEMNIFY AND HOLD HARMLESS BRIGHAM AND ALL CONTRIBUTORS FROM AND
   AGAINST ANY AND ALL CLAIMS, SUITS, ACTIONS, DEMANDS AND JUDGMENTS
   ARISING THEREFROM.

6. None of the names, logos or trademarks of Brigham or any of
   Brigham's affiliates or any of the Contributors, or any funding
   agency, may be used to endorse or promote products produced in
   whole or in part by operation of the Software or derived from or
   based on the Software without specific prior written permission
   from the applicable party.

7. Any use, reproduction or distribution of the Software which is not
   in accordance with this Software License shall automatically revoke
   all rights granted to you under this Software License and render
   Paragraphs 1 and 2 of this Software License null and void.

8. This Software License does not grant any rights in or to any
   intellectual property owned by Brigham or any Contributor except
   those rights expressly granted hereunder.

PART C. MISCELLANEOUS

This Agreement shall be governed by and construed in accordance with
the laws of The Commonwealth of Massachusetts without regard to
principles of conflicts of law. This Agreement shall supercede and
replace any license terms that you may have agreed to previously with
respect to MK-Curve.
```

</details>
