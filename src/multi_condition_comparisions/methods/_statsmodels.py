import numpy as np
import pandas as pd
import scanpy as sc
import statsmodels
import statsmodels.api as sm
from tqdm.auto import tqdm

from multi_condition_comparisions._util import check_is_integer_matrix

from ._base import LinearModelBase


class Statsmodels(LinearModelBase):
    """Differential expression test using a statsmodels linear regression"""

    def _check_counts(self):
        check_is_integer_matrix(self.data)

    def fit(
        self,
        regression_model: sm.OLS | sm.GLM = sm.OLS,
        **kwargs,
    ) -> None:
        """
        Fit the specified regression model.

        Parameters
        ----------
        regression_model
            A statsmodels regression model class, either OLS or GLM. Defaults to OLS.

        **kwargs
            Additional arguments for fitting the specific method. In particular, this
            is where you can specify the family for GLM.

        Example
        -------
        >>> import statsmodels.api as sm
        >>> model = StatsmodelsDE(adata, design="~condition")
        >>> model.fit(sm.GLM, family=sm.families.NegativeBinomial(link=sm.families.links.Log()))
        >>> results = model.test_contrasts(np.array([0, 1]))
        """
        self.models = []
        for var in tqdm(self.adata.var_names):
            mod = regression_model(
                sc.get.obs_df(self.adata, keys=[var], layer=self.layer)[var],
                self.design,
                **kwargs,
            )
            mod = mod.fit()
            self.models.append(mod)

    def _test_single_contrast(self, contrast, **kwargs) -> pd.DataFrame:
        res = []
        for var, mod in zip(tqdm(self.adata.var_names), self.models, strict=False):
            t_test = mod.t_test(contrast)
            res.append(
                {
                    "variable": var,
                    "p_value": t_test.pvalue,
                    "t_value": t_test.tvalue.item(),
                    "sd": t_test.sd.item(),
                    "log_fc": t_test.effect.item(),
                    "adj_p_value": statsmodels.stats.multitest.fdrcorrection(np.array([t_test.pvalue]))[1].item(),
                }
            )
        return pd.DataFrame(res).sort_values("p_value")

    def contrast(self, column: str, baseline: str, group_to_compare: str) -> np.ndarray:
        """
        Build a simple contrast for pairwise comparisons.

        This is equivalent to

        ```
        model.cond(<column> = baseline) - model.cond(<column> = group_to_compare)
        ```
        """
        return self.cond(**{column: baseline}) - self.cond(**{column: group_to_compare})
