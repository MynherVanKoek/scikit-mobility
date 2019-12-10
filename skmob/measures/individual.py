from math import sqrt, sin, cos, pi, asin, pow, ceil, log
import numpy as np
from scipy import stats
import pandas as pd
from collections import defaultdict
import sys
from tqdm import tqdm
from skmob.utils.gislib import getDistanceByHaversine
tqdm.pandas()
from ..utils import constants

def _radius_of_gyration_individual(traj):
    """
    Compute the radius of gyration of a single individual given their TrajDataFrame

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectory of the individual
    
    Returns
    -------
    float
        the radius of gyration of the individual
    """
    lats_lngs = traj[[constants.LATITUDE, constants.LONGITUDE]].values
    center_of_mass = np.mean(lats_lngs, axis=0)
    rg = np.sqrt(np.mean([getDistanceByHaversine((lat, lng), center_of_mass) ** 2.0 for lat, lng in lats_lngs]))
    return rg


def radius_of_gyration(traj, show_progress=True):
    """Radius of gyration.
    
    Compute the radii of gyration (in kilometers) of a set of individuals in a TrajDataFrame.
    The radius of gyration of an individual :math:`u` is defined as [GHB2008]_ [PRQPG2013]_: 
    
    .. math:: 
        r_g(u) = \sqrt{ \\frac{1}{n_u} \sum_{i=1}^{n_u} dist(r_i(u) - r_{cm}(u))^2}
    
    where :math:`r_i(u)` represents the :math:`n_u` positions recorded for :math:`u`, and :math:`r_{cm}(u)` is the center of mass of :math:`u`'s trajectory. In mobility analysis, the radius of gyration indicates the characteristic distance travelled by :math:`u`.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the radius of gyration of each individual.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob import TrajDataFrame
    >>> from skmob.measures.individual import radius_of_gyration
    >>> tdf = TrajDataFrame.from_file('mydata.csv', user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> radius_of_gyration(tdf).head()
       uid  radius_of_gyration
    0    1           20.815129
    1    2           15.689436
    2    3           14.918760
    3    4           14.706123
    4    5           23.990570

    References
    ----------
    .. [GHB2008] González, M. C., Hidalgo, C. A. & Barabási, A. L. (2008) Understanding individual human mobility patterns. Nature, 453, 779–782, https://www.nature.com/articles/nature06958.
    .. [PRQPG2013] Pappalardo, L., Rinzivillo, S., Qu, Z., Pedreschi, D. & Giannotti, F. (2013) Understanding the patterns of car travel. European Physics Journal Special Topics 215(1), 61-73, https://link.springer.com/article/10.1140%2Fepjst%2Fe2013-01715-5

    See Also
    --------
    k_radius_of_gyration
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame([_radius_of_gyration_individual(traj)], columns=[sys._getframe().f_code.co_name])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _radius_of_gyration_individual(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _radius_of_gyration_individual(x))
    return pd.DataFrame(df).reset_index().rename(columns={0: sys._getframe().f_code.co_name}) 


def _k_radius_of_gyration_individual(traj, k=2):
    """Compute the k-radius of gyration of a single individual given their TrajDataFrame.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual.
    
    k : int, optional
        the number of most frequent locations to consider. The default is 2. The possible range of values is math:`[2, +inf]`.
    
    Returns
    -------
    float
        the k-radius of gyration of the individual. 
    """
    traj['visits'] = traj.groupby([constants.LATITUDE, constants.LONGITUDE]).transform('count')[constants.DATETIME]
    top_k_locations = traj.drop_duplicates(subset=[constants.LATITUDE, constants.LONGITUDE]).sort_values(by=['visits', constants.DATETIME],
                                                                              ascending=[False, True])[:k]
    visits = top_k_locations['visits'].values
    total_visits = sum(visits)
    lats_lngs = top_k_locations[[constants.LATITUDE, constants.LONGITUDE]].values

    center_of_mass = visits.dot(lats_lngs) / total_visits
    krg = np.sqrt(sum([visits[i] * (getDistanceByHaversine((lat, lng), center_of_mass) ** 2.0)
                       for i, (lat, lng) in enumerate(lats_lngs)]) / total_visits)
    return krg


def k_radius_of_gyration(traj, k=2, show_progress=True):
    """k-radius of gyration.
    
    Compute the k-radii of gyration (in kilometers) of a set of individuals in a TrajDataFrame.
    The k-radius of gyration of an individual :math:`u` is defined as [PSRPGB2015]_:
    
    .. math::
        r_g^{(k)}(u) = \sqrt{\\frac{1}{n_u^{(k)}} \sum_{i=1}^k (r_i(u) - r_{cm}^{(k)}(u))^2} 
        
    where :math:`r_i(u)` represents the :math:`n_u^{(k)}` positions recorded for :math:`u` on their k most frequent locations, and :math:`r_{cm}^{(k)}(u)` is the center of mass of :math:`u`'s trajectory considering the visits to the k most frequent locations only. In mobility analysis, the k-radius of gyration indicates the characteristic distance travelled by that individual as induced by their k most frequent locations.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual.
    
    k : int, optional
        the number of most frequent locations to consider. The default is 2. The possible range of values is :math:`[2, +inf]`.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the k-radii of gyration of the individuals

    Examples
    --------
    >>> import skmob
    >>> from skmob import TrajDataFrame
    >>> from skmob.measures.individual import k_radius_of_gyration
    >>> tdf = TrajDataFrame.from_file('../data/brightkite_data.csv', user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> k_radius_of_gyration(tdf).head()
       uid  k_radius_of_gyration
    0    1              1.798615
    1    2              2.449305
    2    3              1.223604
    3    4              6.034151
    4    5             20.678760

    See Also
    --------
    radius_of_gyration

    References
    ----------
    .. [PSRPGB2015] Pappalardo, L., Simini, F. Rinzivillo, S., Pedreschi, D. Giannotti, F. & Barabasi, A. L. (2015) Returners and Explorers dichotomy in human mobility. Nature Communications 6, https://www.nature.com/articles/ncomms9166
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame([_k_radius_of_gyration_individual(traj, k=k)], columns=['%s%s' % (k, sys._getframe().f_code.co_name)])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _k_radius_of_gyration_individual(x, k))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _k_radius_of_gyration_individual(x, k))
    return pd.DataFrame(df).reset_index().rename(columns={0: '%s%s' % (k, sys._getframe().f_code.co_name)})


def _random_entropy_individual(traj):
    """
    Compute the random entropy of a single individual given their TrajDataFrame.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual
    
    Returns
    -------
    float
        the random entropy of the individual 
    """
    n_distinct_locs = len(traj.groupby([constants.LATITUDE, constants.LONGITUDE]))
    entropy = np.log2(n_distinct_locs)
    return entropy


def random_entropy(traj, show_progress=True):
    """Random entropy.
    
    Compute the random entropy of a set of individuals in a TrajDataFrame.
    The random entropy of an individual :math:`u` is defined as [EP2009]_ [SQBB2010]_: 
    
    .. math::
        E_{rand}(u) = log_2(N_u)
    
    where :math:`N_u` is the number of distinct locations visited by :math:`u`, capturing the degree of predictability of :math:`u`’s whereabouts if each location is visited with equal probability. 

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the random entropy of the individuals.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import random_entropy
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data/brightkite_data.csv', user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> random_entropy(tdf).head()
       uid  random_entropy
    0    1        6.658211
    1    2        6.942515
    2    3        6.491853
    3    4        6.228819
    4    5        6.727920

    See Also
    --------
    uncorrelated_entropy, real_entropy

    References
    ----------
    .. [EP2009] Eagle, N. & Pentland, A. S. (2009) Eigenbehaviors: identifying structure in routine. Behavioral Ecology and Sociobiology 63(7), 1057-1066, https://link.springer.com/article/10.1007/s00265-009-0830-6
    .. [SQBB2010] Song, C., Qu, Z., Blumm, N. & Barabási, A. L. (2010) Limits of Predictability in Human Mobility. Science 327(5968), 1018-1021, https://science.sciencemag.org/content/327/5968/1018
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame([_random_entropy_individual(traj)], columns=[sys._getframe().f_code.co_name])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _random_entropy_individual(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _random_entropy_individual(x))
    return pd.DataFrame(df).reset_index().rename(columns={0: sys._getframe().f_code.co_name})


def _uncorrelated_entropy_individual(traj, normalize=False):
    """
    Compute the uncorrelated entropy of a single individual given their TrajDataFrame.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    normalize : boolean, optional
        if True, normalize the entropy in the range :math:`[0, 1]` by dividing by :math:`log_2(N_u)`, where :math:`N` is the number of distinct locations visited by individual :math:`u`. The default is False.

    Returns
    -------
    float
        the temporal-uncorrelated entropy of the individual
    """
    n = len(traj)
    probs = [1.0 * len(group) / n for group in traj.groupby(by=[constants.LATITUDE, constants.LONGITUDE]).groups.values()]
    entropy = stats.entropy(probs, base=2.0)
    if normalize:
        n_vals = len(np.unique(traj[[constants.LATITUDE, constants.LONGITUDE]].values, axis=0))
        if n_vals > 1:
            entropy /= np.log2(n_vals)
        else:  # to avoid NaN
            entropy = 0.0
    return entropy


def uncorrelated_entropy(traj, normalize=False, show_progress=True):
    """Uncorrelated entropy.
    
    Compute the temporal-uncorrelated entropy of a set of individuals in a TrajDataFrame. The temporal-uncorrelated entropy of an individual :math:`u` is defined as [EP2009]_ [SQBB2010]_ [PVGSPG2016]_: 
    
    .. math::
        E_{unc}(u) = - \sum_{j=1}^{N_u} p_u(j) log_2 p_u(j)
    
    where :math:`N_u` is the number of distinct locations visited by :math:`u` and :math:`p_u(j)` is the historical probability that a location :math:`j` was visited by :math:`u`. The temporal-uncorrelated entropy characterizes the heterogeneity of :math:`u`'s visitation patterns.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    normalize : boolean, optional
        if True, normalize the entropy in the range :math:`[0, 1]` by dividing by :math:`log_2(N_u)`, where :math:`N` is the number of distinct locations visited by individual :math:`u`. The default is False.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the temporal-uncorrelated entropy of the individuals.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import uncorrelated_entropy
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data/brightkite_data.csv', user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> uncorrelated_entropy(tdf, normalize=False).head()
       uid  uncorrelated_entropy
    0    1              5.492801
    1    2              5.764952
    2    3              4.628958
    3    4              5.112809
    4    5              5.696118

    See Also
    --------
    random_entropy, real_entropy

    References
    ----------
    .. [PVGSPG2016] Pappalardo, L., Vanhoof, M., Gabrielli, L., Smoreda, Z., Pedreschi, D. & Giannotti, F. (2016) An analytical framework to nowcast well-being using mobile phone data. International Journal of Data Science and Analytics 2(75), 75-92, https://link.springer.com/article/10.1007/s41060-016-0013-2
    """
    column_name = sys._getframe().f_code.co_name
    if normalize:
        column_name = 'norm_%s' % sys._getframe().f_code.co_name
    
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame([_uncorrelated_entropy_individual(traj)], columns=[column_name])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _uncorrelated_entropy_individual(x, normalize=normalize))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _uncorrelated_entropy_individual(x, normalize=normalize))
    return pd.DataFrame(df).reset_index().rename(columns={0: column_name})


def _stringify(seq):
    return '|'.join(['_'.join(list(map(str, r))) for r in seq])


def _true_entropy(sequence):
    n = len(sequence)

    # these are the first and last elements
    sum_lambda = 1. + 2.

    for i in range(1, n - 1):
        str_seq = _stringify(sequence[:i])
        j = 1
        str_sub_seq = _stringify(sequence[i:i + j])
        while str_sub_seq in str_seq:
            j += 1
            str_sub_seq = _stringify(sequence[i:i + j])
            if i + j == n:
                # EOF character
                j += 1
                break
        sum_lambda += j

    return 1. / sum_lambda * n * np.log2(n)


def _real_entropy_individual(traj):
    """
    Compute the real entropy of a single individual given their TrajDataFrame.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual.
    
    Returns
    -------
    float
        the real entropy of the individual.
    """
    time_series = tuple(map(tuple, traj[[constants.LATITUDE, constants.LONGITUDE]].values))
    entropy = _true_entropy(time_series)
    return entropy


def real_entropy(traj, show_progress=True):
    """Real entropy.
    
    Compute the real entropy of a set of individuals in a TrajDataFrame. 
    The real entropy of an individual :math:`u` is defined as [SQBB2010]_: 
    
    .. math:: 
        E(u) = - \sum_{T'_u}P(T'_u)log_2[P(T_u^i)]
    
    where :math:`P(T'_u)` is the probability of finding a particular time-ordered subsequence :math:`T'_u` in the trajectory :math:`T_u`. The real entropy hence depends not only on the frequency of visitation, but also the order in which the nodes were visited and the time spent at each location, thus capturing the full spatiotemporal order present in an :math:`u`'s mobility patterns.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals
    
    show_progress : boolean, optional 
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the real entropy of the individuals
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import real_entropy
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data/brightkite_data.csv', user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> real_entropy(tdf).head()
       uid  real_entropy
    0    1      4.416683
    1    2      4.643135
    2    3      3.759747
    3    4      4.255130
    4    5      4.601280

    See Also
    --------
    random_entropy, uncorrelated_entropy
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame([_real_entropy_individual(traj)], columns=[sys._getframe().f_code.co_name])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _real_entropy_individual(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _real_entropy_individual(x))
    return pd.DataFrame(df).reset_index().rename(columns={0: sys._getframe().f_code.co_name})


def _jump_lengths_individual(traj):
    """
    Compute the jump lengths (in kilometers) of a single individual from their TrajDataFrame.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual.
    
    Returns
    -------
    list
        the list of distances (in kilometers) traveled by the individual.
    """
    if len(traj) == 1:  # if there is just one point, no distance can be computed
        return []
    lats_lngs = traj.sort_values(by=constants.DATETIME)[[constants.LATITUDE, constants.LONGITUDE]].values
    lengths = np.array([getDistanceByHaversine(lats_lngs[i], lats_lngs[i - 1]) for i in range(1, len(lats_lngs))])
    return lengths


def jump_lengths(traj, show_progress=True, merge=False):
    """Jump lengths.
    
    Compute the jump lengths (in kilometers) of a set of individuals in a TrajDataFrame.
    A jump length (or trip distance) :math:`\Delta r`made by an individual :math:`u` is defined as the geographic distance between two consecutive points visited by :math:`u`: 
    
    .. math:: \Delta r = dist(r_i, r_{i + 1})
    
    where :math:`r_i` and :math:`r_{i + 1}` are two consecutive points, described as a latitude, longitude pair, in the time-ordered trajectory of an individual, and :math:`dist` is the geographic distance between the two points [BHG2006]_ [GHB2008]_ [PRQPG2013]_.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    merge : boolean, optional
        if True, merge the individuals' lists into one list. The default is False.
    
    Returns
    -------
    pandas DataFrame or list
        the jump lengths for each individual, where :math:`NaN` indicates that an individual visited just one location and hence distance is not defined; or a list with all jumps together if `merge` is True.

    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import jump_lengths
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data/brightkite_data.csv', user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> jump_lengths(tdf).head()
       uid                                       jump_lengths
    0    1  [0.0, 2.235208041718699, 0.996946934364258, 68...
    1    2  [0.0, 0.0, 5.649741880693563, 1.41265548245858...
    2    3  [2.2311820297176572, 2.824995904497732, 4.9916...
    3    4  [48.52874706948018, 1.4124821185158252, 0.9972...
    4    5  [0.0, 1.0004402836501967, 2.825374437917952, 1...
    >>> jl_list = jump_lengths(tdf, merge=True)
    >>> print(jl_list[:10])
    [19.640467328877936, 0.0, 0.0, 1.743431101038163, 1553.5011134765616, 0.0, 30.14517724008101, 0.0, 2.563647571198179, 1.9309489380903868]
    
    See Also
    --------
    maximum_distance, distance_straight_line

    References
    ----------
    .. [BHG2006] Brockmann, D., Hufnagel, L. & Geisel, T. (2006) The scaling laws of human travel. Nature 439, 462-465, https://www.nature.com/articles/nature04292    
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame(pd.Series([_jump_lengths_individual(traj)]), columns=[sys._getframe().f_code.co_name])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _jump_lengths_individual(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _jump_lengths_individual(x))
    
    df = pd.DataFrame(df).reset_index().rename(columns={0: sys._getframe().f_code.co_name})
    
    if merge:
        # merge all lists 
        jl_list =[]
        for x in df.jump_lengths:
            jl_list.extend(x)
        return jl_list
    return df


def _maximum_distance_individual(traj):
    """
    Compute the maximum distance (in kilometers) traveled by an individual given their TrajDataFrame.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual
    
    Returns
    -------
    float
        the maximum traveled distance for the individual. Note that :math:`NaN` indicates that an individual visited just one location and hence distance is not defined.
    """
    jumps = _jump_lengths_individual(traj)
    if len(jumps) > 0:
        return max(jumps)
    return np.NaN

def maximum_distance(traj, show_progress=True):
    """Maximum distance.
    
    Compute the maximum distance (in kilometers) traveled by a set of individuals in a TrajDataFrame. The maximum distance :math:`d_{max}` travelled by an individual :math:`u` is defined as: 
    
    .. math:: d_{max} = \max\limits_{1 \leq i \lt j \lt n_u} dist(r_i, r_j)
    
    where :math:`n_u` is the number of points recorded for :math:`u`, :math:`r_i` and :math:`r_{i + 1}` are two consecutive points, described as a :math:`(latitude, longitude)` pair, in :math:`u`'s time-ordered trajectory, and :math:`dist` is the geographic distance between the two points [WTDED2015]_ [LBH2012]_.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the maximum traveled distance for each individual. Note that :math:`NaN` indicates that an individual visited just one location and so the maximum distance is not defined.

    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import maximum_distance
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data/brightkite_data.csv', user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> maximum_distance(tdf).head()
       uid  maximum_distance
    0    1         84.923674
    1    2         73.190512
    2    3         92.713548
    3    4         79.425210
    4    5         73.036719

    See Also
    --------
    jump_lengths, distance_straight_line

    References
    ----------
    .. [WTDED2015] Williams, N. E., Thomas, T. A., Dunbar, M., Eagle, N. & Dobra, A. (2015) Measures of Human Mobility Using Mobile Phone Records Enhanced with GIS Data. PLOS ONE 10(7): e0133630. https://doi.org/10.1371/journal.pone.0133630
    .. [LBH2012] Lu, X., Bengtsson, L. & Holme, P. (2012) Predictability of population displacement after the 2010 haiti earthquake. Proceedings of the National Academy of Sciences 109 (29) 11576-11581; https://doi.org/10.1073/pnas.1203882109
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame([_maximum_distance_individual(traj)], columns=[sys._getframe().f_code.co_name])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _maximum_distance_individual(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _maximum_distance_individual(x))
    return pd.DataFrame(df).reset_index().rename(columns={0: sys._getframe().f_code.co_name})

def _distance_straight_line_individual(traj):
    """
    Compute the distance straight line travelled by the individual given their TrajDataFrame.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual
    
    Returns
    -------
    float
        the straight line distance traveled by the individual. Note the :math:`NaN` indicates that the individual visited just one location and hence distance is not defined.
    """
    jumps = _jump_lengths_individual(traj)
    if len(jumps) > 0:
        return sum(jumps)
    return 0.0

def distance_straight_line(traj, show_progress=True):
    """Distance straight line.
    
    Compute the distance (in kilometers) travelled straight line by a set of individuals in a TrajDataFrame. The distance straight line :math:`d_{SL}` travelled by an individual :math:`u` is computed as the sum of the distances travelled :math:`u`: 
    
    .. math:: d_{SL} = \sum_{j=2}^{n_u} dist(r_{j-1}, r_j)
    
    where :math:`n_u` is the number of points recorded for :math:`u`, :math:`r_{j-1}` and :math:`r_j` are two consecutive points, described as a :math:`(latitude, longitude)` pair, in :math:`u`'s time-ordered trajectory, and :math:`dist` is the geographic distance between the two points [WTDED2015]_.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    show_progress : boolean, optional 
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the straight line distance traveled by the individuals. Note that :math:`NaN` indicates that an individual visited just one location and hence distance is not defined.

    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import distance_straight_line
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data/brightkite_data.csv', user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> distance_straight_line(tdf).head()
       uid  distance_straight_line
    0    1             7917.805713
    1    2             5330.312205
    2    3             6481.041936
    3    4             3370.984587
    4    5             7300.563980

    See Also
    --------
    jump_lengths, maximum_distance
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame([_distance_straight_line_individual(traj)], columns=[sys._getframe().f_code.co_name])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _distance_straight_line_individual(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _distance_straight_line_individual(x))
    return pd.DataFrame(df).reset_index().rename(columns={0: sys._getframe().f_code.co_name})


def _waiting_times_individual(traj):
    """
    Compute the waiting times for a single individual given their TrajDataFrame.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual.
    
    Returns
    -------
    list
        the waiting times of the individual.
    """
    if len(traj) == 1:
        return []
    times = traj.sort_values(by=constants.DATETIME)[constants.DATETIME]
    wtimes = times.diff()[1:].values.astype('timedelta64[s]').astype('float')
    return wtimes


def waiting_times(traj, show_progress=True, merge=False):
    """Waiting times.
    
    Compute the waiting times (in seconds) between the movements of each individual in a TrajDataFrame. A waiting time (or inter-time) by an individual :math:`u` is defined as the time between two consecutive points in :math:`u`'s trajectory:
    
    .. math:: \Delta t = |t(r_i) - t(r_{i + 1})|
    
    where :math:`r_i` and :math:`r_{i + 1}` are two consecutive points, described as a :math:`(latitude, longitude)` pair, in the time-ordered trajectory of :math:`u`, and :math:`t(r)` indicates the time when :math:`u` visits point :math:`r` [SKWB2010]_ [PF2018]_.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    merge : boolean, optional
        if True, merge the individuals' lists into one list. The default is False.
    
    Returns
    -------
    pandas DataFrame or list
        the list of waiting times for each individual, where :math:`NaN` indicates that an individual visited just one location and hence waiting time is not defined; or a list with all waiting times together if `merge` is True.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import waiting_times
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data/brightkite_data.csv', user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> waiting_times(tdf).head()
       uid                                      waiting_times
    0    1  [2005.0, 2203.0, 1293.0, 823.0, 2636.0, 893.0,...
    1    2  [1421.0, 1948.0, 1508.0, 815.0, 8954.0, 1248.0...
    2    3  [5014.0, 838.0, 1425.0, 1250.0, 993.0, 1596.0,...
    3    4  [5623.0, 617.0, 721.0, 1954.0, 956.0, 1479.0, ...
    4    5  [1461.0, 13354.0, 1258.0, 7966.0, 768.0, 615.0...sys._getframe().f_code.co_name
    >>> wl_list = waiting_times(tdf, merge=True)
    >>> print(wl_list[:10])
    [2358.0, 136.0, 303.0, 1836.0, 14869.0, 517.0, 8995.0, 41306.0, 949.0, 11782.0]
    
    References
    ----------
    .. [SKWB2010] Song, C., Koren, T., Wang, P. & Barabasi, A.L. (2010) Modelling the scaling properties of human mobility. Nature Physics 6, 818-823, https://www.nature.com/articles/nphys1760
    .. [PF2018] Pappalardo, L. & Simini, F. (2018) Data-driven generation of spatio-temporal routines in human mobility. Data Mining and Knowledge Discovery 32, 787-829, https://link.springer.com/article/10.1007/s10618-017-0548-4
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame(pd.Series([_waiting_times_individual(traj)]), columns=[sys._getframe().f_code.co_name])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _waiting_times_individual(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _waiting_times_individual(x))
    
    df = pd.DataFrame(df).reset_index().rename(columns={0: sys._getframe().f_code.co_name})
    
    if merge:
        wl_list =[]
        for x in df.waiting_times:
            wl_list.extend(x)
        return wl_list
    
    return df


def _number_of_locations_individual(traj):
    """
    Compute the number of visited locations of a single individual given their TrajDataFrame.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual.
    
    Returns
    -------
    int
        number of distinct locations visited by the individual.
    """
    n_locs = len(traj.groupby([constants.LATITUDE, constants.LONGITUDE]).groups)
    return n_locs


def number_of_locations(traj, show_progress=True):
    """Number of distinct locations.
    
    Compute the number of distinct locations visited by a set of individuals in a TrajDataFrame [GHB2008]_.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the number of distinct locations visited by the individuals.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import number_of_locations
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file(datadata,  user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> number_of_locations(tdf).head()
       uid  number_of_locations
    0    1                  101
    1    2                  123
    2    3                   90
    3    4                   75
    4    5                  106
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame([_number_of_locations_individual(traj)], columns=[sys._getframe().f_code.co_name])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _number_of_locations_individual(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _number_of_locations_individual(x))
    return pd.DataFrame(df).reset_index().rename(columns={0: sys._getframe().f_code.co_name})


def _home_location_individual(traj, start_night='22:00', end_night='07:00'):
    """
    Compute the home location of a single individual given their TrajDataFrame.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    start_night : str, optional
        the starting time of the night (format HH:MM). The default is '22:00'.
        
    end_night : str, optional
        the ending time for the night (format HH:MM). The default is '07:00'.
    
    Returns
    -------
    tuple
        the latitude and longitude coordinates of the individual's home location 
    """
    night_visits = traj.set_index(pd.DatetimeIndex(traj.datetime)).between_time(start_night, end_night)
    if len(night_visits) != 0:
        lat, lng = night_visits.groupby([constants.LATITUDE, constants.LONGITUDE]).count().sort_values(by=constants.DATETIME, ascending=False).iloc[0].name
    else:
        lat, lng = traj.groupby([constants.LATITUDE, constants.LONGITUDE]).count().sort_values(by=constants.DATETIME, ascending=False).iloc[0].name
    home_coords = (lat, lng)
    return home_coords


def home_location(traj, start_night='22:00', end_night='07:00', show_progress=True):
    """Home location.
    
    Compute the home location of a set of individuals in a TrajDataFrame. The home location is defined as the location an individual visits the most during nighttime [CBTDHVSB2012]_ [PSO2012]_.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    start_night : str, optional
        the starting time of the night (format HH:MM). The default is '22:00'.
        
    end_night : str, optional
        the ending time for the night (format HH:MM). The default is '07:00'.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the home location (in terms of latitude and longitude coordinates) of the individuals.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import home_location
    >>> tdf = skmob.read_trajectories('data_test/gps_test_dataset.csvdata', user_id='user', longitude='lon')
    >>> home_location(tdf).head()
       uid        lat        lng
    0    1  46.126505  11.867149
    1    2  46.442010  10.998368
    2    3  45.818599  11.130413
    3    4  45.873280  11.093846
    4    5  46.215770  11.067935

    See Also
    --------
    max_distance_from_home
    
    References
    ----------
    .. [CBTDHVSB2012] Csáji, B. C., Browet, A., Traag, V. A., Delvenne, J.-C., Huens, E., Van Dooren, P., Smoreda, Z. & Blondel, V. D. (2012) Exploring the Mobility of Mobile Phone Users. Physica A: Statistical Mechanics and its Applications 392(6), 1459-1473.
    .. [PSO2012] Phithakkitnukoon, S., Smoreda, Z. & Olivier, P. (2012) Socio-geography of human mobility: A study using longitudinal mobile phone data. PLOS ONE 7(6): e39253. https://doi.org/10.1371/journal.pone.0039253
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame([_home_location_individual(traj, start_night=start_night, end_night=end_night)], columns=[constants.LATITUDE, constants.LONGITUDE])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _home_location_individual(x, start_night=start_night, end_night=end_night))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _home_location_individual(x, start_night=start_night, end_night=end_night))
    return df.apply(pd.Series).reset_index().rename(columns={0: constants.LATITUDE, 1: constants.LONGITUDE})


def _max_distance_from_home_individual(traj, start_night='22:00', end_night='07:00'):
    """
    Compute the maximum distance from home traveled by a single individual, given their TrajDataFrame.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    start_night : str, optional
        the starting time of the night (format HH:MM). The default is '22:00'.
        
    end_night : str, optional
        the ending time for the night (format HH:MM). The default is '07:00'.
    
    Returns
    -------
    float
        the maximum distance from home traveled by the individual.
    """    
    lats_lngs = traj.sort_values(by=constants.DATETIME)[[constants.LATITUDE, constants.LONGITUDE]].values
    home = home_location(traj, start_night=start_night, end_night=end_night, show_progress=False).iloc[0]
    home_lat, home_lng = home[constants.LATITUDE], home[constants.LONGITUDE]
    lengths = np.array([getDistanceByHaversine((lat, lng), (home_lat, home_lng)) for i, (lat, lng) in enumerate(lats_lngs)])
    return lengths.max()


def max_distance_from_home(traj, start_night='22:00', end_night='07:00', show_progress=True):
    """Maximum distance from home.
    
    Compute the maximum distance (in kilometers) traveled from their home location by a set of individuals in a TrajDataFrame [CM2015]_.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    start_night : str, optional
        the starting time of the night (format HH:MM). The default is '22:00'.
        
    end_night : str, optional
        the ending time for the night (format HH:MM). The default is '07:00'.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the maximum distance from home of the individuals.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import max_distance_from_home
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data_test/brightkite_data.csv'data,  user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> max_distance_from_home(tdf).head()
       uid  max_distance_from_home
    0    1               46.409510
    1    2               68.499333
    2    3               56.806038
    3    4               78.949592
    4    5               69.393777

    See Also
    --------
    maximum_distance, home_location

    References
    ----------
    .. [CM2015] Canzian, L. & Musolesi, M. (2015) Trajectories of depression: unobtrusive monitoring of depressive states by means of smartphone mobility traces analysis. Proceedings of the 2015 ACM International Joint Conference on Pervasive and Ubiquitous Computing, 1293--1304.
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return pd.DataFrame([_max_distance_from_home_individual(traj, 
                                                                start_night=start_night, 
                                                                end_night=end_night)], columns=[sys._getframe().f_code.co_name])
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _max_distance_from_home_individual(x, start_night=start_night, end_night=end_night))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _max_distance_from_home_individual(x, start_night=start_night, end_night=end_night))
    return pd.DataFrame(df).reset_index().rename(columns={0: sys._getframe().f_code.co_name})


def number_of_visits(traj, show_progress=True):
    """Number of visits.
    
    Compute the number of visits of a set a individuals in a TrajDataFrame.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the number of visits or points per each individual.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import number_of_visits
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data_test/brightkite_data.csv'data,  user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> number_of_visits(tdf).head()
       uid  number_of_visits
    0    1               340
    1    2               316
    2    3               355
    3    4               375
    4    5               245
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return len(traj)
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: len(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: len(x))
    return pd.DataFrame(df).reset_index().rename(columns={0: sys._getframe().f_code.co_name})


def _location_frequency_individual(traj, normalize=True,
                                   location_columns=[constants.LATITUDE, constants.LONGITUDE]):
    """
    Compute the visitation frequency of each location for a single individual given their TrajDataFrame.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual.
    
    normalize : boolean, optional
        if True compute the ratio of visits, otherwise the row count of visits to each location. The default is True.
    
    location_columns : list, optional
        the name of the column(s) indicating the location. The default is [constants.LATITUDE, constants.LONGITUDE].
    
    Returns
    -------
    pandas DataFrame
        the location frequency of each location of the individual 
    """
    freqs = traj.groupby(location_columns).count()[constants.DATETIME].sort_values(ascending=False)
    if normalize:
        freqs /= freqs.sum()
    return freqs


def location_frequency(traj, normalize=True, as_ranks=False, show_progress=True,
                       location_columns=[constants.LATITUDE, constants.LONGITUDE]):
    """Location frequency.
    
    Compute the visitation frequency of each location, for a set of individuals in a TrajDataFrame [SKWB2010]_ [PF2018]_.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    normalize : boolean, optional
        if True, the frequencies are normalized (i.e., divided by the individual's total number of visits). The default is True.
    
    as_ranks : boolean, optional
        if True, return a list where element :math:`i` indicates the average visitation frequency of the :math:`i`-th most frequent location. The default is False.
   
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
        
    location_columns : list, optional
        the name of the column(s) indicating the location. The default is [constants.LATITUDE, constants.LONGITUDE].
    
    Returns
    -------
    pandas DataFrame or list
        the location frequency for each location for each individual, or the ranks list for each individual.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import location_frequency
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data_test/brightkite_data.csv', user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> location_frequency(tdf).head()
       uid        lat        lng  datetime
    0    1  46.180259  11.040689  0.255882
    1    1  46.180027  11.053637  0.055882
    2    1  46.337311  10.799639  0.044118
    3    1  46.307321  10.980472  0.032353
    4    1  46.144740  11.013478  0.026471

    See Also
    --------
    visits_per_location
    """
    # TrajDataFrame without 'uid' column
    if constants.UID not in traj.columns: 
        df = pd.DataFrame(_location_frequency_individual(traj, location_columns=location_columns))
        return df.reset_index()
    
    # TrajDataFrame with a single user
    n_users = len(traj[constants.UID].unique())
    if n_users == 1: # if there is only one user in the TrajDataFrame
        df = pd.DataFrame(_location_frequency_individual(traj, location_columns=location_columns))
        return df.reset_index()
    
    # TrajDataFrame with multiple users
    if show_progress:
        df = pd.DataFrame(traj.groupby(constants.UID)
                          .progress_apply(lambda x: _location_frequency_individual(x, normalize=normalize, location_columns=location_columns)))
    else:
        df = pd.DataFrame(traj.groupby(constants.UID)
                          .apply(lambda x: _location_frequency_individual(x, normalize=normalize, location_columns=location_columns)))
    
    df = df.rename(columns={constants.DATETIME: 'location_frequency'})
    
    if as_ranks:
        ranks = [[] for i in range(df.groupby('uid').count().max().location_frequency)]
        for i, group in df.groupby('uid'):
            for j, (index, row) in enumerate(group.iterrows()):
                ranks[j].append(row.location_frequency)
        ranks = [np.mean(rr) for rr in ranks]
        return ranks
    
    return df


def _individual_mobility_network_individual(traj, self_loops=False):
    """
    Compute the individual mobility network of a single individual given their TrajDataFrame.
    
    Parameters
    -----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    self_loops : boolean, optional
        if True adds self loops also. The default is False.
    
    Returns
    -------
    pandas DataFrame
        the individual mobility network of the individual.
    """
    loc2loc2weight = defaultdict(lambda: defaultdict(lambda: 0))
    traj = traj.sort_values(by=constants.DATETIME)
    lats_lngs = traj[[constants.LATITUDE, constants.LONGITUDE]].values

    i = 1
    for lat, lng in lats_lngs[1:]:
        prev = tuple(lats_lngs[i - 1])
        current = (lat, lng)
        if prev != current:
            loc2loc2weight[prev][current] += 1
        elif self_loops:
            loc2loc2weight[prev][current] += 1
        else:
            pass
        i += 1

    rows = []
    for loc1, loc2weight in loc2loc2weight.items():
        for loc2, weight in loc2weight.items():
            rows.append([loc1[0], loc1[1], loc2[0], loc2[1], weight])
    return pd.DataFrame(rows, columns=[constants.LATITUDE + '_origin', constants.LONGITUDE + '_origin',
                                       constants.LATITUDE + '_dest', constants.LONGITUDE + '_dest', 'n_trips'])


def individual_mobility_network(traj, self_loops=False, show_progress=True):
    """Individual Mobility Network.
    
    Compute the individual mobility network of a set of individuals in a TrajDataFrame [RGNPPG2014]_ [BL2012]_ [SQBB2010]_.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    self_loops : boolean, optional
        if True, adds self loops also. The default is False.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the individual mobility network of each individual.

    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import individual_mobility_network
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data_test/brightkite_data.csv',  user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> individual_mobility_network(tdf).head()
       uid  lat_origin  lng_origin   lat_dest    lng_dest n_trips
    0    0   37.774929 -122.419415  37.600747 -122.382376       1
    1    0   37.600747 -122.382376  37.615223 -122.389979       1
    2    0   37.600747 -122.382376  37.580304 -122.343679       1
    3    0   37.615223 -122.389979  39.878664 -104.682105       1
    4    0   37.615223 -122.389979  37.580304 -122.343679       1

    References
    ----------
    .. [RGNPPG2014] Rinzivillo, S., Gabrielli, L., Nanni, M., Pappalardo, L., Pedreschi, D. & Giannotti, F. (2012) The purpose of motion: Learning activities from Individual Mobility Networks. Proceedings of the 2014 IEEE International Conference on Data Science and Advanced Analytics, 312-318.
    .. [BL2012] Bagrow, J. P. & Lin, Y.-R. (2012) Mesoscopic Structure and Social Aspects of Human Mobility. PLOS ONE 7(5): e37676. https://doi.org/10.1371/journal.pone.0037676
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return _individual_mobility_network_individual(traj)
    
    if show_progress:
        return traj.groupby(constants.UID).progress_apply(lambda x: _individual_mobility_network_individual(x,
                self_loops=self_loops)).reset_index().drop('level_1', axis=1)
    else:
        return traj.groupby(constants.UID).apply(lambda x: _individual_mobility_network_individual(x,
                self_loops=self_loops)).reset_index().drop('level_1', axis=1)


def _recency_rank_individual(traj):
    """
    Compute the recency rank of the locations of an individual given their TrajDataFrame.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual.
    
    Returns
    -------
    pandas DataFrame
        the recency rank for each location of the individuals.
    """
    traj = traj.sort_values(constants.DATETIME, ascending=False).drop_duplicates(subset=[constants.LATITUDE,
                                                                                         constants.LONGITUDE],
                                                                                 keep="first")
    traj['recency_rank'] = range(1, len(traj) + 1)
    return traj[[constants.LATITUDE, constants.LONGITUDE, 'recency_rank']]


def recency_rank(traj, show_progress=True):
    """Recency rank.
    
    Compute the recency rank of the locations of a set of individuals in a TrajDataFrame [BDEM2015]_.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the recency rank for each location of the individual.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import recency_rank
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file('../data_test/brightkite_data.csv'data,  user_id='user', datetime='check-in time', latitude='latitude', longitude='longitude')
    >>> recency_rank(tdf).head()
                  lat        lng  recency_rank
    uid
    324 18  43.776687  11.235343             1
        17  43.792211  11.245647             2
        16  43.824934  11.282771             3
        15  43.797951  11.240277             4
        14  43.530801  10.319265             5

    See Also
    --------
    frequency_rank

    References
    ----------
    .. [BDEM2015] Barbosa, H., de Lima-Neto, F. B., Evsukoff, A., Menezes, R. (2015) The effect of recency to human mobility, EPJ Data Science 4(21), doi:10.1140/epjds/s13688-015-0059-8
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return _recency_rank_individual(traj)
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _recency_rank_individual(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _recency_rank_individual(x))
    return pd.DataFrame(df)


def _frequency_rank_individual(traj):
    """
    Compute the frequency rank of the locations of a single individual given their TrajDataFrame.
    
    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individual.
    
    Returns
    -------
    pandas DataFrame
        the frequency rank for each location of the individual.
    """
    traj = traj.groupby([constants.LATITUDE, constants.LONGITUDE]).count().sort_values(by=constants.DATETIME, ascending=False).reset_index()
    traj['frequency_rank'] = range(1, len(traj) + 1)
    return traj[[constants.LATITUDE, constants.LONGITUDE, 'frequency_rank']]


def frequency_rank(traj, show_progress=True):
    """Frequency rank.
    
    Compute the frequency rank of the locations of a set of individuals in a TrajDataFrame [BDEM2015]_.

    Parameters
    ----------
    traj : TrajDataFrame
        the trajectories of the individuals.
    
    show_progress : boolean, optional
        if True, show a progress bar. The default is True.
    
    Returns
    -------
    pandas DataFrame
        the frequency rank for each location of the individuals.
    
    Examples
    --------
    >>> import skmob
    >>> from skmob.measures.individual import frequency_rank
    >>> from skmob import TrajDataFrame
    >>> tdf = TrajDataFrame.from_file(data, user_id='user', dadataheck-in time', latitude='latitude', longitude='longitude')
    >>> frequency_rank(tdf).head()
                lat        lng  frequency_rank
    uid
    324 0  42.970399  10.695334               1
        1  43.404161  10.873485               2
        2  43.530801  10.319265               3
        3  43.776687  11.235343               4
        4  43.797951  11.240277               5

    See Also
    --------
    recency_rank
    """
    # if 'uid' column in not present in the TrajDataFrame
    if constants.UID not in traj.columns:
        return _frequency_rank_individual(traj)
    
    if show_progress:
        df = traj.groupby(constants.UID).progress_apply(lambda x: _frequency_rank_individual(x))
    else:
        df = traj.groupby(constants.UID).apply(lambda x: _frequency_rank_individual(x))
    return df
