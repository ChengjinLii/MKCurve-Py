"""Standalone boundaries, installed CLI and synthetic input contracts."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import nibabel as nib
import numpy as np

from mkcurve import run_mkcurve
from mkcurve.core import UPSTREAM_COMMIT, metric_validity
from tests.synthetic import synthetic_case, write_case


class StandaloneTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def inputs(self):
        return write_case(self.root, synthetic_case(noisy=True))

    def run_case(self, paths, output="fit", **kwargs):
        return run_mkcurve(*(paths[k] for k in ("dwi", "bval", "bvec", "mask")),
                           self.root / output, grid=np.arange(100., 2200., 100.), **kwargs)

    def cli(self, *args):
        return subprocess.run([sys.executable, "-m", "mkcurve", *map(str, args)],
                              cwd=self.root, text=True, capture_output=True, timeout=90)

    def test_installed_cli_discovery_works_outside_checkout(self):
        result = self.cli("doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["available"])
        self.assertEqual(self.cli("--version").stdout.strip(), "0.1.0")

    def test_cli_fits_real_algorithm_with_custom_grid_and_reports_failure(self):
        paths = self.inputs()
        grid = self.root / "grid.csv"
        np.savetxt(grid, np.arange(100., 2200., 100.), delimiter=",")
        args = ["run"]
        for name, path in paths.items():
            args.extend(["--" + name, path])
        args.extend(["--output-dir", self.root / "fit", "--grid", grid])
        result = self.cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        record = json.loads(Path(summary["record_path"]).read_text())
        self.assertEqual(record["settings"]["grid_policy"], "explicit user grid")
        self.assertEqual(record["human_review"], "pending")
        self.assertTrue(Path(record["maps"]["corrected_mk"]).is_file())
        before = Path(summary["record_path"]).read_bytes()
        result = self.cli(*args)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must be empty", result.stderr)
        self.assertEqual(Path(summary["record_path"]).read_bytes(), before)

    def test_output_directory_cannot_contain_inputs(self):
        paths = self.inputs()
        before = {key: path.read_bytes() for key, path in paths.items()}
        for directory in (self.root, paths["dwi"].parent, paths["dwi"]):
            with self.assertRaisesRegex(ValueError, "contain any source"):
                self.run_case(paths, output=directory)
        for key, path in paths.items():
            self.assertEqual(path.read_bytes(), before[key])

    def test_nonempty_output_is_not_overwritten(self):
        paths = self.inputs()
        output = self.root / "fit"
        output.mkdir()
        sentinel = output / "mkcurve_record.json"
        sentinel.write_text("previous result")
        with self.assertRaises(FileExistsError):
            self.run_case(paths)
        self.assertEqual(sentinel.read_text(), "previous result")

    def test_plain_nifti_mask_and_n_by_three_gradients(self):
        paths = self.inputs()
        image = nib.load(paths["mask"])
        paths["mask"] = self.root / "mask.nii"
        nib.save(image, paths["mask"])
        np.savetxt(paths["bvec"], np.loadtxt(paths["bvec"]).T)
        self.assertEqual(self.run_case(paths)["status"], "completed")

    def test_mismatched_geometry_and_nonbinary_masks_fail(self):
        paths = self.inputs()
        image = nib.load(paths["mask"])
        affine = image.affine.copy()
        affine[0, 3] += 1
        nib.save(nib.Nifti1Image(np.asanyarray(image.dataobj), affine), paths["mask"])
        with self.assertRaisesRegex(ValueError, "geometry"):
            self.run_case(paths, "bad-affine")
        data = np.asanyarray(image.dataobj).copy()
        data[0, 0, 0] = 2
        nib.save(nib.Nifti1Image(data, image.affine), paths["mask"])
        with self.assertRaisesRegex(ValueError, "binary"):
            self.run_case(paths, "bad-mask")

    def test_missing_baseline_and_rank_deficient_protocol_fail(self):
        paths = self.inputs()
        bvals = np.loadtxt(paths["bval"])
        np.savetxt(paths["bval"], np.maximum(bvals, 100.))
        with self.assertRaisesRegex(ValueError, "baseline"):
            self.run_case(paths, "no-baseline")
        np.savetxt(paths["bval"], bvals)
        np.savetxt(paths["bvec"], np.zeros((3, len(bvals))))
        with self.assertRaisesRegex(ValueError, "no valid corrected"):
            self.run_case(paths, "rank-deficient")
        record = json.loads((self.root / "rank-deficient/mkcurve_record.json").read_text())
        self.assertEqual(record["status"], "failed")

    def test_bvalue_limits_and_grid_dimensions_are_validated(self):
        paths = self.inputs()
        for options in ({"b0_threshold": -1}, {"b0_threshold": np.nan},
                        {"max_bvalue": 50}, {"max_bvalue": np.inf}):
            with self.assertRaisesRegex(ValueError, "b-value limits"):
                self.run_case(paths, **options)
        with self.assertRaisesRegex(ValueError, "Synthetic b0 grid"):
            run_mkcurve(*(paths[k] for k in ("dwi", "bval", "bvec", "mask")),
                        self.root / "bad-grid", grid=np.ones((3, 2)))

    def test_independent_metric_validity_does_not_erase_good_mk(self):
        maps = {"mk": np.array([1., 1.]), "rk": np.array([np.nan, 1.]),
                "e1": np.array([.001, .001]), "e2": np.array([.001, .001]),
                "e3": np.array([.001, -.001])}
        masks = metric_validity(maps, np.ones(2, bool), np.ones(2, bool), np.zeros(2))
        np.testing.assert_array_equal(masks["mk"], [True, False])
        np.testing.assert_array_equal(masks["rk"], [False, False])

    def test_stored_author_fixture_is_explicitly_synthetic(self):
        fixture = json.loads(Path(__file__).with_name("fixtures").joinpath("mkcurve_author_octave.json").read_text())
        self.assertIn("SYNTHETIC ONLY", fixture["scope"])
        self.assertEqual(fixture["upstream_commit"], UPSTREAM_COMMIT)
        self.assertEqual(len(fixture["reference_output_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
