import anndata as ad
import numpy as np
import pytest
import scipy.sparse as sp

from multi_condition_comparisions._util import check_is_integer_matrix
from multi_condition_comparisions.methods import Statsmodels


@pytest.mark.parametrize(
    "matrix_type,invalid_input",
    [
        [np.array, np.nan],
        [np.array, np.inf],
        [np.array, "foo"],
        # not possible to have a sparse matrix with 'object' dtype (e.g. "foo")
        [sp.csr_matrix, np.nan],
        [sp.csr_matrix, np.nan],
        [sp.csc_matrix, np.inf],
        [sp.csc_matrix, np.inf],
    ],
)
def test_invalid_inputs(matrix_type, invalid_input, test_counts, test_metadata):
    """Check that invalid inputs in MethodBase counts raise an error."""
    test_counts[0, 0] = invalid_input
    adata = ad.AnnData(X=matrix_type(test_counts), obs=test_metadata)
    with pytest.raises((ValueError, TypeError)):
        Statsmodels(adata=adata, design="~condition")


@pytest.mark.parametrize("matrix_type", [np.array, sp.csr_matrix, sp.csc_matrix])
@pytest.mark.parametrize(
    "input,expected",
    [
        pytest.param([[1, 2], [3, 4]], None, id="valid"),
        pytest.param([[1, -2], [3, 4]], ValueError, id="negative values"),
        pytest.param([[1, 2.5], [3, 4]], ValueError, id="non-integer"),
        pytest.param([[1, np.nan], [3, 4]], ValueError, id="nans"),
    ],
)
def test_valid_count_matrix(matrix_type, input, expected: type):
    """Test with a valid count matrix."""
    matrix = matrix_type(input, dtype=float)

    if expected is None:
        check_is_integer_matrix(matrix)
    else:
        with pytest.raises(expected):
            check_is_integer_matrix(matrix)
