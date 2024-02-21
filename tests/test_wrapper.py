from inspect import signature
from typing import get_args

import numpy as np
import pytest
from pandas import testing as tm

from multi_condition_comparisions.tl.wrapper import MethodRegistry, run_de


def test_arg_types():
    run_de_args = set(get_args(signature(run_de).parameters["method"].annotation))
    assert run_de_args == set(MethodRegistry.keys()), run_de_args


@pytest.mark.parametrize(
    "method",
    list(MethodRegistry.keys()),
)
def test_simple(test_adata, method):
    res_df = run_de(adata=test_adata, method=method, contrasts=["condition", "A", "B"], design="~condition")

    assert len(res_df) == test_adata.n_vars
    # Check that the index of the result matches the var_names of the AnnData object
    tm.assert_index_equal(test_adata.var_names, res_df.index, check_order=False, check_names=False)

    expected_columns = {"pvals", "pvals_adj", "logfoldchanges"}
    assert expected_columns.issubset(set(res_df.columns))
    assert np.all((0 <= res_df["pvals"]) & (res_df["pvals"] <= 1))
