# Standalone Release Checks

Local checks performed on Linux on 2026-11-04 for package version 0.1.0.
This records software checks, not clinical validation or a fresh execution
of the original MATLAB/Octave implementation.

## Executed Tests

| Environment | NumPy | SciPy | NiBabel | threadpoolctl | Result |
| --- | --- | --- | --- | --- | --- |
| Python 3.13.5, editable installation | 2.5.4 | 1.18.1 | 5.4.2 | 3.7.0 | 37 pytest tests passed |
| Python 3.13.5, clean wheel installation | 2.5.4 | 1.18.1 | 5.4.2 | 3.7.0 | 37 pytest tests passed |
| Python 3.11.15, clean wheel, minimum declared runtime libraries | 1.24.0 | 1.10.0 | 5.1.0 | 3.1.0 | 37 pytest tests passed |

The editable environment also passed all 37 tests through
`python -m unittest discover -s tests`.
Wheel tests were launched from outside the checkout. Isolated-mode import
resolved `mkcurve` to the clean environment's `site-packages`, without a
SlicerDSpace/SlicerDDSurfer source path.

The suite covers synthetic recovery, stored author-reference comparison,
predicted weights, abnormal detection, repair, invalid/degenerate inputs,
serial/parallel scheduling, solver/log reuse, input immutability, geometry,
CLI discovery/fitting and refusal to overwrite outputs.

## Packaging and Algorithm Checks

- `python -m build --no-isolation` built both sdist and wheel, with the wheel
  built from the sdist. The direction JSON, Python tensor source and all four
  license files are present in the wheel; source provenance and tests are
  present in the sdist.
- `pip check` found no broken requirements in the current and minimum-library
  environments.
- The installed console CLI's `doctor` command succeeds outside the checkout.
- The installed-wheel synthetic demo executed the real algorithm for four
  artificial voxels and 206 adaptive b0 samples.
- Tensor source, integration directions, inherited synthetic fixture and
  upstream license texts match their source copies byte-for-byte.
- AST comparison of metric validity, grid generation, abnormal detection,
  signal repair and chunk fitting found no algorithm changes apart from
  package-relative imports.

## Scope Limits

Only synthetic data were executed. The inherited fixture records a previous
GNU Octave 7.3.0 run; it was not regenerated in this release task.
No real-subject, whole-brain, biological, clinical or performance-validation
claim follows from these checks. Other platforms and dependency combinations
require separate verification. GitHub Actions status must be checked on the
published commit rather than inferred from the local results above.
