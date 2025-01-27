import numpy as np
import pytest
import statsmodels.api as sm
from pandas import testing as tm

import multi_condition_comparisions
from multi_condition_comparisions.tl.de import PyDESeq2DE, StatsmodelsDE, EdgeRDE


def test_package_has_version():
    assert multi_condition_comparisions.__version__ is not None


@pytest.mark.parametrize(
    "method_class,kwargs",
    [
        # OLS
        (StatsmodelsDE, {}),
        # Negative Binomial
        (
            StatsmodelsDE,
            {"regression_model": sm.GLM, "family": sm.families.NegativeBinomial()},
        ),
    ],
)
def test_de(test_adata, method_class, kwargs):
    """Check that the method can be initialized and fitted, and perform basic checks on
    the result of test_contrasts."""
    method = method_class(adata=test_adata, design="~condition")  # type: ignore
    method.fit(**kwargs)
    res_df = method.test_contrasts(np.array([0, 1]))
    # Check that the result has the correct number of rows
    assert len(res_df) == test_adata.n_vars


def test_pydeseq2_simple(test_adata):
    """Check that the pyDESeq2 method can be

    1. Initialized
    2. Fitted
    3. and that test_contrast returns a DataFrame with the correct number of rows.
    """
    method = PyDESeq2DE(adata=test_adata, design="~condition")
    method.fit()
    res_df = method.test_contrasts(["condition", "A", "B"])

    assert len(res_df) == test_adata.n_vars


def test_edger_simple(test_adata):
    """Check that the EdgeR method can be

    1. Initialized
    2. Fitted
    3. and that test_contrast returns a DataFrame with the correct number of rows.
    """
    method = EdgeRDE(adata=test_adata, design="~condition")
    method.fit()
    res_df = method.test_contrasts(["condition", "A", "B"])

    assert len(res_df) == test_adata.n_vars


def test_pydeseq2_complex(test_adata):
    """Check that the pyDESeq2 method can be initialized with a different covariate name and fitted and that the test_contrast
    method returns a dataframe with the correct number of rows.
    """
    test_adata.obs["condition1"] = test_adata.obs["condition"].copy()
    method = PyDESeq2DE(adata=test_adata, design="~condition1+group")
    method.fit()
    res_df = method.test_contrasts(["condition1", "A", "B"])

    assert len(res_df) == test_adata.n_vars
    # Check that the index of the result matches the var_names of the AnnData object
    tm.assert_index_equal(test_adata.var_names, res_df.index, check_order=False, check_names=False)

    expected_columns = {"pvals", "pvals_adj", "logfoldchanges"}
    assert expected_columns.issubset(set(res_df.columns))
    assert np.all((0 <= res_df["pvals"]) & (res_df["pvals"] <= 1))

def test_edger_complex(test_adata):
    """Check that the EdgeR method can be initialized with a different covariate name and fitted and that the test_contrast
    method returns a dataframe with the correct number of rows.
    """
    test_adata.obs["condition1"] = test_adata.obs["condition"].copy()
    method = EdgeRDE(adata=test_adata, design="~condition1+group")
    method.fit()
    res_df = method.test_contrasts(["condition1", "A", "B"])

    assert len(res_df) == test_adata.n_vars
    # Check that the index of the result matches the var_names of the AnnData object
    tm.assert_index_equal(test_adata.var_names, res_df.index, check_order=False, check_names=False)

    expected_columns = {"pvals", "pvals_adj", "logfoldchanges"}
    assert expected_columns.issubset(set(res_df.columns))
    assert np.all((0 <= res_df["pvals"]) & (res_df["pvals"] <= 1))

