# -*- coding: latin-1 -*-
"""
@author: Ivano Lauriola and Michele Donini
@email: ivano.lauriola@phd.unipd.it
 
EasyMKL: a scalable multiple kernel learning algorithm
by Fabio Aiolli and Michele Donini

This file is part of MKLpy: a scikit-compliant framework for Multiple Kernel Learning
This file is distributed with the GNU General Public License v3 <http://www.gnu.org/licenses/>. 
 
Paper @ http://www.math.unipd.it/~mdonini/publications.html
"""

from .base import MKL, Solution
from .komd import KOMD
from ..multiclass import OneVsOneMKLClassifier as ovoMKL, OneVsRestMKLClassifier as ovaMKL
from ..arrange import summation
from ..utils.exceptions import BinaryProblemError
from ..utils.misc import identity_kernel
from ..metrics import margin

import torch
import numpy as np

 
 
class EasyMKL(MKL):
    ''' EasyMKL is a Multiple Kernel Learning algorithm.
        The parameter lam (lambda) has to be validated from 0 to 1.
 
        For more information:
        EasyMKL: a scalable multiple kernel learning algorithm
            by Fabio Aiolli and Michele Donini
 
        Paper @ http://www.math.unipd.it/~mdonini/publications.html
    '''
    def __init__(self, 
        learner=KOMD(lam=0.1), 
        lam=0.1, 
        multiclass_strategy='ova', 
        verbose=False,
        max_iter=10000,
        tolerance=1e-6,
        solver='auto',
        ):
        super().__init__(
            learner=learner, 
            multiclass_strategy=multiclass_strategy, 
            verbose=verbose,
            max_iter=max_iter,
            tolerance=tolerance,
            solver=solver,
        )

        self.func_form = summation
        self.lam = lam
        if self.solver == 'auto':
            self._solver = 'libsvm' if self.lam >0 else 'cvxopt'
        else:
            self._solver = self.solver


        
    def _combine_kernels(self):
        assert len(self.Y.unique()) == 2
        Y = torch.tensor([1 if y==self.classes_[1] else -1 for y in self.Y])
        n_sample = len(self.Y)
        ker_matrix = (1-self.lam) * self.func_form(self.KL) + self.lam * identity_kernel(n_sample)


        mar, gamma = margin(
            ker_matrix, Y, 
            return_coefs=True, 
            solver=self._solver, 
            max_iter=self.max_iter, 
            tol=self.tolerance)
        yg = gamma.T * Y
        weights = torch.tensor([(yg.view(n_sample, 1).T @ K @ yg).item() for K in self.KL])
        weights = weights / weights.sum()

        ker_matrix = self.func_form(self.KL, weights)
        return Solution(
            weights=weights,
            objective=None,
            ker_matrix=ker_matrix,
            )

 
    def get_params(self, deep=True):
        # this estimator has parameters:
        params = super().get_params()
        params.update({'lam': self.lam})
        return params
