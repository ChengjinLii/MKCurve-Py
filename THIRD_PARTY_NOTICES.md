# Third-Party Notices

MKCurve-Py is a modified, unofficial Python translation and standalone
distribution, not the original MATLAB software or an author-endorsed Python
release. Original numerical algorithm authorship is unchanged.
Research use only; no clinical approval is claimed.

## Original MK-Curve

Fan Zhang and collaborators, Brigham and Women's Hospital:
https://github.com/zhangfanmark/MK-Curve, pinned commit
`9a213e1a5850fe50c998793f31ed852df00242f8`.

`src/mkcurve/core.py` translates `run_MKCurve.m` and
`abnormal_voxel_detection.m`. Its BWH Contribution and Software License
Agreement (June 2019) is retained in full in `LICENSE`,
`licenses/MK-Curve-LICENSE.txt` and the README.
This translation retains author-style unconstrained predicted-weight WLLS,
synthetic-b0 curves, abnormal detection and baseline correction.
See README for port differences. Validity masks do not constrain fits.

All or portions of this licensed product (such portions are the "Software")
have been obtained under license from The Brigham and Women's Hospital, Inc.
and are subject to the following terms and conditions:
[the complete original agreement](licenses/MK-Curve-LICENSE.txt).

## DKI Routines

`src/mkcurve/mkcurve_tensor.py` and `src/mkcurve/mkcurve_directions.json`
derive from the original MK-Curve `lib/DKI/` routines, including
`dki_fit.m`, `dki_mk_only.m` and `dki_parameters.m`.
Copyright (c) 2017 New York University and University of Antwerp.
These modified Python source files and the direction table remain **MPL-2.0**.
The full license is in `licenses/MK-Curve-DKI-MPL-2.0.txt`.

SlicerDSpace modifications (2026) include Python translation, column
equilibration, pivoted QR, guarded batched fitting and fallback,
finite-value guards, pole-safe radial integration, and bounded design/log
reuse. Standalone packaging makes no numerical edits to this tensor module
or direction table. Source files ship in wheel/sdist and this repository.

## SlicerDSpace and Standalone Infrastructure

Source: https://github.com/ChengjinLii/SlicerDSpace, snapshot
`57b044f54411b84230564fdcef18c469742569c7`.
Copyright (c) 2026, Chengjin Li and the SlicerDSpace contributors.
BSD-3-Clause terms: `licenses/BSD-3-Clause.txt`.

This covers input staging (`mkcurve_inputs.py`), scheduling
(`chunk_dispatch.py`), extracted shell/provenance I/O (`_io.py`),
and synthetic test/harness infrastructure. New CLI, metadata, example and
tests use the same BSD-3-Clause terms. This does not relicense the BWH
workflow or MPL-2.0 tensor code. Standalone changes include relative imports,
CLI/API packaging, output overwrite protection, b-value option checks,
mask re-encoding and truthful custom-grid provenance.
Source hashes and mappings are in `provenance.json`.

The inherited Octave JSON fixture contains four synthetic voxel signals and
numeric results, not patient data. Its scope, source commit and reference
hash are preserved; it is not newly generated MATLAB/Octave evidence.

No original HCP sample, manuscript/PDF, weights, proprietary MathWorks helper,
MATLAB I/O library or unrelated backend is distributed. Dependencies are
installed, not vendored, and retain their own licenses.
