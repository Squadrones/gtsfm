"""Unit tests for matcher catcher.

Authors: Ayush Baid
"""
from pathlib import Path
from typing import Match
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from gtsfm.frontend.matcher.cacher.matcher_cacher import MatcherCacher
from gtsfm.common.image import Image
from gtsfm.common.keypoints import Keypoints

DUMMY_KEYPOINTS_I1 = Keypoints(
    coordinates=np.random.rand(10, 2), scales=np.random.rand(10), responses=np.random.rand(10)
)
DUMMY_DESCRIPTORS_I1 = np.random.rand(len(DUMMY_KEYPOINTS_I1), 128)
DUMMY_KEYPOINTS_I2 = Keypoints(
    coordinates=np.random.rand(15, 2), scales=np.random.rand(15), responses=np.random.rand(15)
)
DUMMY_DESCRIPTORS_I2 = np.random.rand(len(DUMMY_KEYPOINTS_I2), 128)
DUMMY_IM_SHAPE_I1 = (100, 200)
DUMMY_IM_SHAPE_I2 = (50, 50)

DUMMY_MATCH_INDICES = np.random.rand(5, 2)

ROOT_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent


class TestMatcherCacher(unittest.TestCase):
    """Unit tests for MatcherCacher."""

    @patch("gtsfm.utils.cache.generate_hash_for_numpy_array", return_value="numpy_key")
    @patch("gtsfm.utils.io.read_from_compressed_file", return_value=None)
    @patch("gtsfm.utils.io.write_to_compressed_file")
    def test_cache_miss(self, write_mock, read_mock, generate_hash_for_numpy_array_mock):
        """Test the scenario of cache miss."""

        # mock the underlying detector-descriptor which is used on cache miss
        underlying_matcher_mock = MagicMock()
        underlying_matcher_mock.match.return_value = DUMMY_MATCH_INDICES
        underlying_matcher_mock.__class__.__name__ = "mock_matcher"
        obj_under_test = MatcherCacher(matcher_obj=underlying_matcher_mock)

        computed_match_indices = obj_under_test.match(
            keypoints_i1=DUMMY_KEYPOINTS_I1,
            keypoints_i2=DUMMY_KEYPOINTS_I2,
            descriptors_i1=DUMMY_DESCRIPTORS_I1,
            descriptors_i2=DUMMY_DESCRIPTORS_I2,
            im_shape_i1=DUMMY_IM_SHAPE_I1,
            im_shape_i2=DUMMY_IM_SHAPE_I2,
        )
        # assert the returned value
        np.testing.assert_allclose(computed_match_indices, DUMMY_MATCH_INDICES)

        # assert that underlying object was called
        underlying_matcher_mock.match.assert_called_once_with(
            keypoints_i1=DUMMY_KEYPOINTS_I1,
            keypoints_i2=DUMMY_KEYPOINTS_I2,
            descriptors_i1=DUMMY_DESCRIPTORS_I1,
            descriptors_i2=DUMMY_DESCRIPTORS_I2,
            im_shape_i1=DUMMY_IM_SHAPE_I1,
            im_shape_i2=DUMMY_IM_SHAPE_I2,
        )

        # assert that hash generation was called twice
        # TODO: this need proper values
        # generate_hash_for_numpy_array_mock.assert_is_called()

        # assert that read function was called once and write function was called once
        cache_path = ROOT_PATH / "cache" / "matcher" / "mock_matcher_numpy_key.pbz2"
        read_mock.assert_called_once_with(cache_path)
        write_mock.assert_called_once_with(DUMMY_MATCH_INDICES, cache_path)

    @patch("gtsfm.utils.cache.generate_hash_for_numpy_array", return_value="numpy_key")
    @patch("gtsfm.utils.io.read_from_compressed_file", return_value=DUMMY_MATCH_INDICES)
    @patch("gtsfm.utils.io.write_to_compressed_file")
    def test_cache_hit(self, write_mock, read_mock, generate_hash_for_numpy_array_mock):
        """Test the scenario of cache miss."""

        # mock the underlying detector-descriptor which is used on cache miss
        underlying_matcher_mock = MagicMock()
        underlying_matcher_mock.match.return_value = DUMMY_MATCH_INDICES
        underlying_matcher_mock.__class__.__name__ = "mock_matcher"
        obj_under_test = MatcherCacher(matcher_obj=underlying_matcher_mock)

        computed_match_indices = obj_under_test.match(
            keypoints_i1=DUMMY_KEYPOINTS_I1,
            keypoints_i2=DUMMY_KEYPOINTS_I2,
            descriptors_i1=DUMMY_DESCRIPTORS_I1,
            descriptors_i2=DUMMY_DESCRIPTORS_I2,
            im_shape_i1=DUMMY_IM_SHAPE_I1,
            im_shape_i2=DUMMY_IM_SHAPE_I2,
        )
        # assert the returned value
        np.testing.assert_allclose(computed_match_indices, DUMMY_MATCH_INDICES)

        # assert that underlying object was not called
        underlying_matcher_mock.match.assert_not_called()

        # assert that hash generation was called twice
        # TODO: this need proper values
        # generate_hash_for_numpy_array_mock.assert_is_called()

        # assert that read function was called once and write function was called once
        cache_path = ROOT_PATH / "cache" / "matcher" / "mock_matcher_numpy_key.pbz2"
        read_mock.assert_called_once_with(cache_path)
        write_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
