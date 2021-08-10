"""Unit tests for the interface for PatchmatchNet

Authors: Ren Liu
"""
import unittest
from pathlib import Path

import numpy as np
from gtsam import PinholeCameraCal3Bundler

from gtsfm.common.gtsfm_data import GtsfmData, SfmTrack
from gtsfm.densify.patchmatchnet_data import PatchmatchNetData
from gtsfm.loader.olsson_loader import OlssonLoader

DATA_ROOT_PATH = Path(__file__).resolve().parent.parent / "data"

DEFAULT_FOLDER = DATA_ROOT_PATH / "set1_lund_door"

NUM_VIEWS = 5

EXAMPLE_CAMERA_ID = 1

MIN_DEPTH_PERCENTILE = 0.01
MAX_DEPTH_PERCENTILE = 0.99


class TestPatchmatchNetData(unittest.TestCase):
    """Unit tests for the interface for PatchmatchNet."""

    def setUp(self) -> None:
        """Set up the image dictionary and gtsfm result for the test."""
        super().setUp()

        # initialize Olsson Loader
        self._loader = OlssonLoader(str(DEFAULT_FOLDER), image_extension="JPG")
        self._num_images = len(self._loader)

        # set up image dictionary
        self._img_dict = {i: self._loader.get_image(i) for i in range(self._num_images)}

        # initialize an empty sfm result in GtsfmData class
        self._sfm_result = GtsfmData(self._num_images)
        # add randomized dummy valid cameras to the sfm result
        self.add_dummy_cameras()
        # add randomized dummy tracks to the sfm result and calculate the expected depth ranges
        self.add_dummy_tracks()
        # build PatchmatchNet dataset from input images, sfm result, and the number of views used in PatchmatchNet
        self._dataset_patchmatchnet = PatchmatchNetData(self._img_dict, self._sfm_result, num_views=NUM_VIEWS)

    def add_dummy_cameras(self) -> None:
        """randomize half the number of all cameras as valid cameras, then add them into sfm_result"""
        # random valid cameras, the below number and indices of valid cameras are dummy values
        self._num_valid_cameras = self._num_images // 2
        valid_cameras = np.arange(self._num_valid_cameras)

        # add dummy valid cameras (camera_idx in valid_cameras) to sfm result
        for i in valid_cameras:
            self._sfm_result.add_camera(
                i, PinholeCameraCal3Bundler(self._loader.get_camera_pose(i), self._loader.get_camera_intrinsics(i))
            )

    def add_dummy_tracks(self) -> None:
        """randomize some dummy common tracks and corresponding measurements, insert the tracks into sfm result, and
        then calculate the expected depth ranges
        """
        # initialize dummy depth range for the test example
        self._example_depths = []

        # the below number of tracks is a dummy value
        self._num_tracks = self._num_valid_cameras * 4
        # add random tracks to sfm result
        for j in range(self._num_tracks):
            # the below 3D points of the random tracks are dummy locations, their depths are set to be the track indices
            world_x = np.array([0, -2.0, j])
            track_to_add = SfmTrack(world_x)

            # calculate dummy depth range for test example
            example_depth = self._sfm_result.get_camera(EXAMPLE_CAMERA_ID).pose().transformTo(world_x)[-1]
            self._example_depths.append(example_depth)

            # add random measurements of the random track
            for i in range(self._num_valid_cameras):
                # the below 2D measurements of the random tracks are dummy locations
                track_to_add.add_measurement(idx=i, m=np.array([i, i]))
            self._sfm_result.add_track(track_to_add)

        self._example_depths = sorted(self._example_depths)

        self._example_min_depth = np.percentile(self._example_depths, MIN_DEPTH_PERCENTILE)
        self._example_max_depth = np.percentile(self._example_depths, MAX_DEPTH_PERCENTILE)

    def test_initialize_and_configure(self) -> None:
        """Test initialization method and whether configuration is correct"""
        self.assertEqual(len(self._dataset_patchmatchnet), self._num_valid_cameras)

    def test_get_item(self) -> None:
        """Test get item method when yielding test data from dataset"""
        example = self._dataset_patchmatchnet[EXAMPLE_CAMERA_ID]

        B, C, H, W = example["imgs"]["stage_0"].shape

        # test batch size
        self.assertEqual(B, NUM_VIEWS)

        # test images
        h, w, c = self._img_dict[0].value_array.shape
        self.assertEqual((H, W, C), (h, w, c))

        # test 3x4 projection matrices
        sample_proj_mat = example["proj_matrices"]["stage_0"][0][:3, :4]
        sample_camera = self._sfm_result.get_camera(EXAMPLE_CAMERA_ID)
        actual_proj_mat = sample_camera.calibration().K() @ sample_camera.pose().inverse().matrix()[:3, :4]
        self.assertTrue(np.array_equal(sample_proj_mat, actual_proj_mat))

        # test depth range
        self.assertEqual(example["depth_min"], self._example_min_depth)
        self.assertEqual(example["depth_max"], self._example_max_depth)


if __name__ == "__main__":
    unittest.main()
