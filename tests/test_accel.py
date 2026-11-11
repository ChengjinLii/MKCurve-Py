"""Tests for Chebyshev grid interpolation and optional PyTorch CUDA execution."""

import unittest

import numpy as np

from mkcurve import core as mkcurve, mkcurve_tensor as tensor
from tests.synthetic import synthetic_case


class AccelerationParityTests(unittest.TestCase):
    def test_chebyshev_fit_grid_matches_pointwise_wlls_to_fp64_precision(self):
        case = synthetic_case(noisy=True)
        signals = case["data"].reshape(-1, len(case["bvals"]))
        design = tensor.design_matrix(case["bvals"], case["bvecs"])
        grid = np.linspace(100.0, 2100.0, 80, dtype=np.float64)

        fitter = tensor._SyntheticB0Fitter(signals, design, solver="batched")
        approx = fitter.fit_grid(grid)
        exact = np.stack(
            [tensor.mean_kurtosis(fitter.fit(np.full(len(signals), float(val), dtype=np.float64))) for val in grid],
            axis=0,
        )
        np.testing.assert_allclose(approx, exact, rtol=1e-7, atol=1e-7)

    def test_cuda_chunk_matches_cpu_chunk_when_cuda_available(self):
        try:
            import torch
        except Exception:
            self.skipTest("PyTorch not installed")
        if not torch.cuda.is_available():
            self.skipTest("CUDA unavailable")

        case = synthetic_case(noisy=True)
        signals = case["data"].reshape(-1, len(case["bvals"]))
        design = tensor.design_matrix(case["bvals"], case["bvecs"])
        grid = np.linspace(100.0, 2100.0, 80, dtype=np.float64)

        cpu_out = mkcurve._fit_chunk((signals.copy(), design, grid, 0.5, "batched"))
        gpu_out = mkcurve._fit_chunk_cuda((signals.copy(), design, grid, 0.5, "batched"))
        for c_arr, g_arr in zip(cpu_out[:3], gpu_out[:3]):
            np.testing.assert_allclose(g_arr, c_arr, rtol=1e-8, atol=1e-8)
        for key in cpu_out[3]:
            arr_c, arr_g = cpu_out[3][key], gpu_out[3][key]
            if np.issubdtype(np.asarray(arr_c).dtype, np.bool_):
                np.testing.assert_array_equal(arr_g, arr_c)
            else:
                np.testing.assert_allclose(arr_g, arr_c, rtol=1e-8, atol=1e-8)


if __name__ == "__main__":
    unittest.main()
