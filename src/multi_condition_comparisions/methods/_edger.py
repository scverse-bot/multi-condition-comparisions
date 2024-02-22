import re
import warnings
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
import scanpy as sc
import statsmodels
import statsmodels.api as sm
from anndata import AnnData
from formulaic import model_matrix
from formulaic.model_matrix import ModelMatrix
from pydeseq2.dds import DeseqDataSet
from pydeseq2.default_inference import DefaultInference
from pydeseq2.ds import DeseqStats
from scanpy import logging
from scipy.sparse import issparse, spmatrix
from tqdm.auto import tqdm


class EdgeRDE(BaseMethod):
    """Differential expression test using EdgeR"""

    def _check_counts(self) -> bool:
        return self._check_count_matrix(self.adata.X)

    def fit(self, **kwargs):  # adata, design, mask, layer
        """
        Fit model using edgeR.

        Note: this creates its own adata object for downstream.

        Params:
        ----------
        **kwargs
            Keyword arguments specific to glmQLFit()
        '''

        ## -- Check installations
        """
        # For running in notebook
        # pandas2ri.activate()
        # rpy2.robjects.numpy2ri.activate()

        try:
            import rpy2.robjects.numpy2ri
            import rpy2.robjects.pandas2ri
            from rpy2 import robjects as ro
            from rpy2.robjects import numpy2ri, pandas2ri
            from rpy2.robjects.conversion import localconverter
            from rpy2.robjects.packages import importr

            pandas2ri.activate()
            rpy2.robjects.numpy2ri.activate()

        except ImportError:
            raise ImportError("edger requires rpy2 to be installed. ") from None

        try:
            edger = importr("edgeR")
        except ImportError:
            raise ImportError(
                "edgeR requires a valid R installation with the following packages: " "edgeR, BiocParallel, RhpcBLASctl"
            ) from None

        ## -- Convert dataframe
        # Feature selection
        # if mask is not None:
        #    self.adata = self.adata[:,~self.adata.var[mask]]

        # Convert dataframe
        with localconverter(ro.default_converter + numpy2ri.converter):
            expr = self.adata.X if self.layer is None else self.adata.layers[self.layer]
            if issparse(expr):
                expr = expr.T.toarray()
            else:
                expr = expr.T

        expr_r = ro.conversion.py2rpy(pd.DataFrame(expr, index=self.adata.var_names, columns=self.adata.obs_names))

        # Convert to DGE
        dge = edger.DGEList(counts=expr_r, samples=self.adata.obs)

        # Run EdgeR
        logging.info("Calculating NormFactors")
        dge = edger.calcNormFactors(dge)

        logging.info("Estimating Dispersions")
        dge = edger.estimateDisp(dge, design=self.design)

        logging.info("Fitting linear model")
        fit = edger.glmQLFit(dge, design=self.design, **kwargs)

        # Save object
        ro.globalenv["fit"] = fit
        self.fit = fit

    def _test_single_contrast(self, contrast: list[str], **kwargs) -> pd.DataFrame:
        """
        Conduct test for each contrast and return a data frame

        Parameters
        ----------
        contrast:
            numpy array of integars indicating contrast
            i.e. [-1, 0, 1, 0, 0]
        """
        ## -- Check installations
        # For running in notebook
        # pandas2ri.activate()
        # rpy2.robjects.numpy2ri.activate()

        # ToDo:
        #  parse **kwargs to R function
        #  Fix mask for .fit()

        try:
            import rpy2.robjects.numpy2ri
            import rpy2.robjects.pandas2ri  # noqa: F401
            from rpy2 import robjects as ro
            from rpy2.robjects import numpy2ri, pandas2ri  # noqa: F401
            from rpy2.robjects.conversion import localconverter  # noqa: F401
            from rpy2.robjects.packages import importr

        except ImportError:
            raise ImportError("edger requires rpy2 to be installed.") from None

        try:
            importr("edgeR")
        except ImportError:
            raise ImportError(
                "edgeR requires a valid R installation with the following packages: " "edgeR, BiocParallel, RhpcBLASctl"
            ) from None

        # Convert vector to R, which drops a category like `self.design_matrix` to use the intercept for the left out.
        contrast_vec = [0] * len(self.design.columns)
        make_contrast_column_key = lambda ind: f"{contrast[0]}[T.{contrast[ind]}]"
        for index in [1, 2]:
            if make_contrast_column_key(index) in self.design.columns:
                contrast_vec[self.design.columns.to_list().index(f"{contrast[0]}[T.{contrast[index]}]")] = 1
        contrast_vec_r = ro.conversion.py2rpy(np.asarray(contrast_vec))
        ro.globalenv["contrast_vec"] = contrast_vec_r

        # Test contrast with R
        ro.r(
            """
            test = edgeR::glmQLFTest(fit, contrast=contrast_vec)
            de_res =  edgeR::topTags(test, n=Inf, adjust.method="BH", sort.by="PValue")$table
            """
        )

        # Convert results to pandas
        de_res = ro.conversion.rpy2py(ro.globalenv["de_res"])

        return de_res.rename(columns={"PValue": "pvals", "logFC": "logfoldchanges", "FDR": "pvals_adj"})
