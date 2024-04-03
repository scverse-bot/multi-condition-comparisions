from collections.abc import Sequence

import pytest
from pandas.core.api import DataFrame as DataFrame

from multi_condition_comparisions.methods import LinearModelBase


@pytest.fixture
def MockLinearModel():
    class _MockLinearModel(LinearModelBase):
        def _check_counts(self) -> None:
            pass

        def fit(self, **kwargs) -> None:
            pass

        def _test_single_contrast(self, contrast: Sequence[float], **kwargs) -> DataFrame:
            pass

    return _MockLinearModel


@pytest.mark.parametrize(
    "formula,cond_kwargs,expected_contrast",
    [
        ["~ condition", {"condition": "A"}, [1, 0]],
        ["~ condition", {"condition": "B"}, [1, 1]],
        ["~ 0 + condition", {"condition": "A"}, [1, 0]],
        ["~ 0 + condition", {"condition": "B"}, [0, 1]],
        ["~ donor", {"donor": "D0"}, [1, 0, 0, 0]],
        ["~ C(donor)", {"donor": "D0"}, [1, 0, 0, 0]],
        ["~ C(donor, contr.treatment(base='D2'))", {"donor": "D2"}, [1, 0, 0, 0]],
        ["~ C(donor, contr.treatment(base='D2'))", {"donor": "D0"}, [1, 1, 0, 0]],
        # TODO: also include tests for errors that should be caught by .cond
    ],
)
def test_model_cond(test_adata_minimal, MockLinearModel, formula, cond_kwargs, expected_contrast):
    mod = MockLinearModel(test_adata_minimal, formula)
    actual_contrast = mod.cond(**cond_kwargs)
    assert actual_contrast.tolist() == expected_contrast
    assert actual_contrast.index.tolist() == mod.design.columns.tolist()
