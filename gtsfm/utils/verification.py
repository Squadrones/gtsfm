"""Utilities for verification stage of the frontend.

Authors: Ayush Baid
"""
from typing import Optional, Tuple

import cv2 as cv
import numpy as np
from gtsam import Cal3Bundler, EssentialMatrix, Rot3, Unit3

import gtsfm.utils.features as feature_utils

EPS = 1e-8  # constant used to prevent division by zero error.


def recover_relative_pose_from_essential_matrix(
    i2Ei1: Optional[np.ndarray],
    verified_coordinates_i1: np.ndarray,
    verified_coordinates_i2: np.ndarray,
    camera_intrinsics_i1: Cal3Bundler,
    camera_intrinsics_i2: Cal3Bundler,
) -> Tuple[Optional[Rot3], Optional[Unit3]]:
    """Recovers the relative rotation and translation direction from essential matrix and verified correspondences
    using opencv's API.

    Args:
        i2Ei1: essential matrix as a numpy array, of shape 3x3.
        verified_coordinates_i1: coordinates of verified correspondences in image i1, of shape Nx2.
        verified_coordinates_i2: coordinates of verified correspondences in image i2, of shape Nx2.
        camera_intrinsics_i1: intrinsics for image i1.
        camera_intrinsics_i2: intrinsics for image i2.

    Returns:
        relative rotation i2Ri1, or None if the input essential matrix is None.
        relative translation direction i2Ui1, or None if the input essential matrix is None.
    """
    if i2Ei1 is None:
        return None, None

    # obtain points in normalized coordinates using intrinsics.
    normalized_coordinates_i1 = feature_utils.normalize_coordinates(verified_coordinates_i1, camera_intrinsics_i1)
    normalized_coordinates_i2 = feature_utils.normalize_coordinates(verified_coordinates_i2, camera_intrinsics_i2)

    # use opencv to recover pose
    _, i2Ri1, i2ti1, _ = cv.recoverPose(i2Ei1, normalized_coordinates_i1, normalized_coordinates_i2)

    return Rot3(i2Ri1), Unit3(i2ti1.squeeze())


def fundamental_to_essential_matrix(
    i2Fi1: np.ndarray, camera_intrinsics_i1: Cal3Bundler, camera_intrinsics_i2: Cal3Bundler
) -> np.ndarray:
    """Converts the fundamental matrix to essential matrix using camera intrinsics.

    Args:
        i2Fi1: fundamental matrix which maps points in image #i1 to lines in image #i2.
        camera_intrinsics_i1: intrinsics for image #i1.
        camera_intrinsics_i2: intrinsics for image #i2.

    Returns:
        Estimated essential matrix i2Ei1 as numpy array of shape (3x3).
    """
    return camera_intrinsics_i2.K().T @ i2Fi1 @ camera_intrinsics_i1.K()


def essential_to_fundamental_matrix(
    i2Ei1: EssentialMatrix, camera_intrinsics_i1: Cal3Bundler, camera_intrinsics_i2: Cal3Bundler
) -> np.ndarray:
    """Converts the essential matrix to fundamental matrix using camera intrinsics.

    Args:
        i2Ei1: essential matrix which maps points in image #i1 to lines in image #i2.
        camera_intrinsics_i1: intrinsics for image #i1.
        camera_intrinsics_i2: intrinsics for image #i2.

    Returns:
        Fundamental matrix i2Fi1 as numpy array of shape (3x3).
    """
    return np.linalg.inv(camera_intrinsics_i2.K().T) @ i2Ei1.matrix() @ np.linalg.inv(camera_intrinsics_i1.K())


def compute_epipolar_distances_sed(
    coordinates_i1: np.ndarray, coordinates_i2: np.ndarray, i2Fi1: np.ndarray
) -> Optional[np.ndarray]:
    """Compute symmetric point-line epipolar distance between corresponding coordinates in two images. The SED is the
    geometric point-line distance and is a biased estimate of the gold-standard reprojection error.

    References: 
    - "Fathy et al., Fundamental Matrix Estimation: A Study of Error Criteria"

    Args:
        coordinates_i1: coordinates in image i1, of shape Nx2.
        coordinates_i2: corr. coordinates in image i2, of shape Nx2.
        i2Fi1: fundamental matrix between two images.

    Returns:
        Symmetric epipolar point-line distances for each row of the input, of shape N.
    """

    if coordinates_i1 is None or coordinates_i1.size == 0 or coordinates_i2 is None or coordinates_i2.size == 0:
        return None

    epipolar_lines_i2 = feature_utils.convert_to_epipolar_lines(coordinates_i1, i2Fi1)  # Ex1
    epipolar_lines_i1 = feature_utils.convert_to_epipolar_lines(coordinates_i2, i2Fi1.T)  # Etx2

    numerator = feature_utils.point_line_dotproduct(coordinates_i1, epipolar_lines_i1)

    line_sq_norms_i1 = np.sum(np.square(epipolar_lines_i1[:, :2]), axis=1)
    line_sq_norms_i2 = np.sum(np.square(epipolar_lines_i2[:, :2]), axis=1)

    return numerator * np.sqrt(1 / line_sq_norms_i1 + 1 / line_sq_norms_i2)


def compute_epipolar_distances_sampson(
    coordinates_i1: np.ndarray, coordinates_i2: np.ndarray, i2Fi1: np.ndarray
) -> Optional[np.ndarray]:
    """Compute the sampson distance between corresponding coordinates in two images. Sampson distance is the first
    order approximation of the reprojection error.

    References: 
    - "Fathy et al., Fundamental Matrix Estimation: A Study of Error Criteria"

    Args:
        coordinates_i1: coordinates in image i1, of shape Nx2.
        coordinates_i2: corr. coordinates in image i2, of shape Nx2.
        i2Fi1: fundamental matrix between two images.

    Returns:
        Sampson distance for each row of the input, of shape N.
    """

    if coordinates_i1 is None or coordinates_i1.size == 0 or coordinates_i2 is None or coordinates_i2.size == 0:
        return None

    epipolar_lines_i2 = feature_utils.convert_to_epipolar_lines(coordinates_i1, i2Fi1)  # Ex1
    epipolar_lines_i1 = feature_utils.convert_to_epipolar_lines(coordinates_i2, i2Fi1.T)  # Etx2
    line_sq_norms_i1 = np.sum(np.square(epipolar_lines_i1[:, :2]), axis=1)
    line_sq_norms_i2 = np.sum(np.square(epipolar_lines_i2[:, :2]), axis=1)

    numerator = feature_utils.point_line_dotproduct(coordinates_i1, epipolar_lines_i1)
    denominator = np.sqrt(line_sq_norms_i1 + line_sq_norms_i2)

    return numerator / denominator
