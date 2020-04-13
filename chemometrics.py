"""A (spectroscopic) chemometric library

Provides a number of functions for data pretreatment, plotting and regression.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm
import pdb


def asym_ls(X, y, asym_factor=0.1):
    r"""
    Perform an asymmetric least squares regression.

    A linear regression is performed where either negative (default) or
    positive residuals are more strongly penalized.
    `asym_factor` defines the asymmetry of the regression.

    Parameters
    ----------
    X : (n, m) ndarray
        coefficient matrix
    y : (n, o) ndarray
        dependent variables

    Returns
    -------
    beta : (m, o) ndarray
        regression coefficients

    Notes
    -----

    Following equation is solved:

    .. math:: \hat{\beta} = \argmin_\beta (w(y-Xb))^2

    with :math:`w` being a diagonal matrix of weights.
    If :math:`(y-Xb)>0: w_{ii}=asym_factor`
    otherwise :math:`w_{ii} = 1 - asym_factor`

    The problem is solved by iteratively adjusting :math:`w` and using a normal
    least-squares regression [1]. The alogrithm stops as soon as the weights
    are not adjusted from the previous cycle.

    References
    ----------
    .. [1] Hans F.M. Boelens, Reyer J. Dijkstra, Paul H.C. Eilers, Fiona
    Fitzpatrick, Johan A. Westerhuis, New background correction method for
    liquid chromatography with diode array detection, infrared spectroscopic
    detection and Raman spectroscopic detection, J. Chromatogr. A, vol. 1057,
    pp. 21-30, 2004.

    Examples
    --------
    X = np.random.normal(size=[10,3])
    y = np.random.normal(size=[10,1])
    beta = chem.asym_als(X, y)
    """
    n, m = X.shape
    o = y.shape[1]
    beta = np.zeros(shape=[m, o])
    # iterate over each regression
    for i in range(n_regressions):
        # initialize variables for iterative regression
        w = np.zeros([n, 1])
        w_new = np.ones([n, 1])
        max_cycles = 10
        cycle = 0
        # iterate linear regression until weights converge
        while not np.all(w == w_new) and cycle < max_cycles:
            # update weights
            w = w_new.copy()
            # update variables for weighted regression
            X_scaled = w * X
            y_scaled = w * y
            # solve weighted least squares problem
            beta[:, i] = np.linalg.lstsq(X_scaled, y_scaled, rcond=None)[0]
            # calculate new weights
            residuals = y - np.dot(X, beta)
            w_new[residuals > 0] = asym_factor
            w_new[residuals <= 0] = 1 - asym_factor
            # increase counter
            cycle += 1
    return beta


def emsc(D, p_order=2, background=None, normalize=False, algorithm='als'):
    r"""
    Perform extended multiplicative scatter correction (EMSC) on `D`

    `emsc` is a spectral pretreatment which is based on a linear decomposition
    of data into baseline contributions and chemical information. Baseline
    contributions are modelled by polynomial terms up to order `p_order`. The
    chemical information is summarized by the mean spectrum orthogonalized to
    the baseline terms. `emsc` additionally provides a the functionality for
    orthogonalizing spectra with respect to background information and for
    normalizing the returned spectra.

    Parameters
    ----------
    D : (n, m) ndarray
        Data to be pretreated. ``n`` samples x ``m`` variables (typically
        wavelengths)
    p_order : int
        Polynoms up to order `p_order` are included for baseline subtraction.
    background : {None (default), (o, m) ndarray}
        Perform additional orthogonalization with respect to background. If
        ``None`` omitted. Otherwise, ``o`` background spectra x ``m`` variables
    normalize : {False (default), True}
        Perform normalization of results
    algorithm : {'als' (default)}
        choice of algorithms for regression. Currently, only asymmetric least
        squares is supported

    Returns
    -------
    D_pretreated : (n, m) ndarray
        Pretreated data.
    coefficients : (n, k) ndarray
        Coefficient matrix summarizing regression coefficients of EMSC.

    References
    ----------
    An introduction to EMSC is given in [1]. Asymmetric least squares
    regression may be looked up at [2].
    .. [1] Nils Kristian Afseth, Achim Kohler, Extended multiplicative signal
    correction in vibrational spectroscopy, a tutorial, Chemometrics and
    Intelligent Laboratory Systems, vol. 117, pp. 92-99, 2012.
    .. [2] Hans F.M. Boelens, Reyer J. Dijkstra, Paul H.C. Eilers, Fiona
    Fitzpatrick, Johan A. Westerhuis, New background correction method for
    liquid chromatography with diode array detection, infrared spectroscopic
    detection and Raman spectroscopic detection, J. Chromatogr. A, vol. 1057,
    pp. 21-30, 2004.
    """
    n_series, n_variables = D.shape
    # generate matrix of baseline polynomials
    baseline = np.zeros([n_variables, p_order+1])
    multiplier = np.linspace(-1, 1, num=n_variables)
    for i in range(0, p_order+1):
        baseline[:, i] = multiplier ** i
    # matrix for summarizing all factors
    regressor = baseline.copy()

    # if included: prepare background data
    if background:
        # orthogonalize background to baseline information
        beta_background = asym_ls(baseline, background)
        background_pretreated = background - np.dot(baseline, beta_background)
        regressor = np.array([regressor, background_pretreated])

    # prepare estimate of chemical information
    D_bar = np.mean(D, axis=0)  # mean spectra
    beta_D_bar = asym_ls(regressor, D_bar)
    D_bar_pretreated = D_bar - np.dot(regressor, beta_D_bar)
    regressor = np.array([regressor, D_bar_pretreated])

    # perform EMSC on data
    coefficients = asym_ls(regressor, D)
    D_pretreated = D - np.dot(regressor[:, :-1], coefficients[:-1, :])
    if normalize:
        D_pretreated = D_pretreated * np.diag(1/coefficients[-1, :])
    return D_pretreated, coefficients


def plot_colored_series(x, Y, reference=None):
    r"""
    Plot matrix colored by position or `reference`

    Generate a line plot with `x` on x-axis and one or multiple dataseries
    `Y`. The lines are either colored by position in the matrix `Y` or by
    value in the `reference` matrix.

    Parameters
    ----------
    x : (n,) ndarray
        Location on x-axis
    Y : (n, m) ndarray
        Matrix containing data series to plot. The function expects. ``n``
        datapoints in ``m``series.
    reference : {None (default), (m,) ndarray}
        Reference values to color data series by. If None, the series are
        colored by the position in the second dimension of matrix ``Y``.

    Returns
    -------
    lines : list
        A list of line objects generated by plotting the spectra.
    """
    # define number of input series for line plot
    if (Y.ndim > 1):
        n_series = Y.shape[1]
    else:
        n_series = 1
    # if no reference is given a dummy reference is needed
    if reference is None:
        reference = np.arange(n_series)
    myMapper = matplotlib.cm.ScalarMappable(cmap='viridis')
    colors = myMapper.to_rgba(reference)
    lines = []
    for i in range(n_series):
        line_i = plt.plot(x, Y[:, i], color=colors[i, :])
        lines.append(line_i)
    return lines


def generate_spectra(n_wl, n_band, bandwidth):
    r"""
    Generate a dummy spectra with n_band
    """
    wl = np.arange(n_wl)
    spectra = np.zeros(n_wl)
    for i in range(n_band):
        center_wl = np.random.choice(wl)
        bandwidth_i = np.random.gamma(shape=bandwidth, scale=bandwidth)
        intensity = np.random.poisson(lam=5)*np.random.normal(loc=1, scale=0.2)
        current_spectra = intensity * _gaussian_fun(wl, center_wl, bandwidth_i)
        spectra += current_spectra
    return spectra


def _gaussian_fun(x, mu, sigma):
    r"""
    Generates Gaussian profile
    """
    return np.exp(-((x - mu) / sigma) ** 2 / 2)
