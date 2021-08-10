"""MVS math methods for gtsfm

Authors: Ren Liu
"""
import math
import numpy as np

from gtsfm.utils.geometry_comparisons import angle_between_vectors


def piecewise_gaussian(
    xPa: np.ndarray, xPb: np.ndarray, theta_0: float = 5, sigma_1: float = 1, sigma_2: float = 10
) -> float:
    """Evaluate the similarity of vectors from a common track's coordinates to different cameras' centers in world frame
    1. This piecewise Gaussian function outputs a float score to show the evaluation result.
    2. The total score of a view can be calculated by summing up the scores of all common tracks with other views.
    3. A higher score suggests that the angle between vectors from a common track's coordinates to different cameras'
    centers in world frame is closer to a small pre-defined angle theta_0 (5 degrees in default), which means the
    centers of camera a and camera b are close but not the same, and they have common track points. So the view pair is
    suitable to be set as the reference view and the source view.

    More details can be found in "View Selection" paragraphs in Yao's paper https://arxiv.org/abs/1804.02505.

    Args:
        xPa: vector from the track point to camera a's center in the world frame, with shape (3,).
        xPb: vector from the track point to camera b's center in the world frame, with shape (3,).
        theta_0: Defaults to 5.
            theta_0 is the threshold angle (in degrees) between vectors from the track point to camera a and b's centers
        sigma_1: Defaults to 1.
            If the angle between vectors from the track point to camera a and b's centers is no larger than the
            threshold angle, which means for this track, the relative position of centers of camera a and b are close,
            and they can both see the track point. The Gaussian variance should be smaller to make the score higher.
        sigma_2: Defaults to 10.
            If the angle between vectors from the track point to camera a and b's centers is larger than the threshold
            angle, which means for this track, the relative position of centers of camera a and b are not close enough,
            although they can both see the track point. The Gaussian variance should be larger to make the score lower.

    Returns:
        float: A score of the track between two views in the range (0,1]
    """
    # 1. Calculate the angle between the vectors from the track point to camera a's center and camera b's center
    theta_est = angle_between_vectors(xPa, xPb)
    # 2. Calculate the score according to the angle
    if theta_est <= theta_0:  # if the angle is less than or equal to the threshold, we should attach more importance
        sigma = sigma_1
    else:  # if the angle is larger than the threshold, we should attach less importance
        sigma = sigma_2

    return math.exp(-((theta_est - theta_0) ** 2) / (2 * sigma ** 2))
