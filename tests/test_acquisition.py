import argparse
import logging
from typing import Optional, List
import numpy as np
import sys

if sys.version_info >= (3, 5):
    from math import isclose
else:
    def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

from pytemscript.microscope import Microscope
from pytemscript.utils.enums import AcqImageSize, ScreenPosition
from pytemscript.modules.extras import Image


def print_stats(image: Image,
                binning: int,
                exp_time: float,
                interactive: bool = False) -> None:
    """ Calculate statistics about the image and display it.
    :param image: Image object
    :param binning: Input binning
    :param exp_time: Input exposure time
    :param interactive: Show plot and other stats
    """
    img = image.data
    metadata = image.metadata

    print("Metadata: ", metadata)

    if 'TimeStamp' in metadata:
        assert int(metadata['Binning.Width']) == binning
        assert isclose(float(metadata['ExposureTime']), exp_time, abs_tol=0.05)

    assert img.shape[1] == metadata["width"]
    assert img.shape[0] == metadata["height"]

    if interactive:
        import matplotlib.pyplot as plt

        print("\tMean: ", np.mean(image.data))
        vmin = np.percentile(image.data, 3)
        vmax = np.percentile(image.data, 97)
        print("\tStdDev: ", np.std(image.data))

        logging.getLogger("matplotlib").setLevel(logging.INFO)

        plt.imshow(image.data, interpolation="nearest", cmap="gray",
                   vmin=vmin, vmax=vmax)
        print("\tStdDev: ", np.std(image.data))
        plt.colorbar()
        plt.suptitle(image.name)
        plt.ion()
        plt.show()
        plt.pause(1.0)


def camera_acquire(microscope: Microscope,
                   cam_name: str,
                   exp_time: float,
                   binning: int,
                   **kwargs) -> None:
    """ Acquire a test TEM image and check output metadata.
    :param microscope: Microscope object
    :param cam_name: Camera / detector name
    :param exp_time: Exposure time
    :param binning: Input binning
    :param kwargs: Keyword arguments
    """

    image = microscope.acquisition.acquire_tem_image(cam_name,
                                                     size=AcqImageSize.FULL,
                                                     exp_time=exp_time,
                                                     binning=binning,
                                                     **kwargs)
    if image is not None:
        print_stats(image, binning, exp_time)
        image.save(fn="test_image_%s.mrc" % cam_name, overwrite=True)
        image.save(fn="test_image_%s.tif" % cam_name, overwrite=True)
        image.save(fn="test_image_%s.jpg" % cam_name, overwrite=True, thumbnail=True)


def detector_acquire(microscope: Microscope,
                     cam_name: str,
                     dwell_time: float,
                     binning: int,
                     **kwargs) -> None:
    """ Acquire a test STEM image.
    :param microscope: Microscope object
    :param cam_name: Camera / detector name
    :param dwell_time: Dwell time
    :param binning: Input binning
    :param kwargs: Keyword arguments
    """
    image = microscope.acquisition.acquire_stem_image(cam_name,
                                                      size=AcqImageSize.FULL,
                                                      dwell_time=dwell_time,
                                                      binning=binning,
                                                      **kwargs)
    print_stats(image, binning, dwell_time)
    image.save(fn="test_image_%s.tiff" % cam_name, overwrite=True)


def main(argv: Optional[List] = None) -> None:
    """ Testing acquisition functions. """
    parser = argparse.ArgumentParser(
        description="This test can use local or remote client. In the latter case "
                    "pytemscript-server must be already running",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-t", "--type", type=str,
                        choices=["direct", "socket", "utapi"],
                        default="direct",
                        help="Connection type: direct, socket or utapi")
    parser.add_argument("-p", "--port", type=int, default=39000,
                        help="Specify port on which the server is listening")
    parser.add_argument("--host", type=str, default='127.0.0.1',
                        help="Specify host address on which the server is listening")
    parser.add_argument("-d", "--debug", dest="debug",
                        default=False, action='store_true',
                        help="Enable debug mode")
    args = parser.parse_args(argv)

    microscope = Microscope(connection=args.type, host=args.host,
                            port=args.port, debug=args.debug)

    print("Starting acquisition tests, connection: %s" % args.type)

    cameras = microscope.acquisition.cameras
    print("Available cameras:\n", cameras)

    acq_params = {
        "BM-Orius": {"exp_time": 0.25, "binning": 1},
        "BM-Ceta": {"exp_time": 1.0, "binning": 1},
        "BM-Falcon": {"exp_time": 0.5, "binning": 1},
        "EF-CCD": {"exp_time": 2.0, "binning": 1},
    }
    acq_csa_params = {
        "BM-Falcon": {"exp_time": 3.0, "binning": 1, "align_image": True,
                      "electron_counting": True, "save_frames": True, "group_frames": 2},
        "EF-Falcon": {"exp_time": 1.0, "binning": 1,
                      "electron_counting": True, "save_frames": True, "group_frames": 2},
    }

    def check_mode():
        if cam.startswith("BM-") and microscope.optics.projection.is_eftem_on:
            microscope.optics.projection.eftem_off()
        elif cam.startswith("EF-") and not microscope.optics.projection.is_eftem_on:
            microscope.optics.projection.eftem_on()

    microscope.acquisition.screen_position = ScreenPosition.UP
    for cam, cam_dict in cameras.items():
        csa = cam_dict["supports_csa"]
        if csa and cam in acq_csa_params:
            csa_params = acq_csa_params[cam]
            check_mode()
            camera_acquire(microscope, cam, **csa_params)

            if cam_dict["supports_eer"]:
                csa_params.pop("group_frames")
                csa_params["eer"] = True
                camera_acquire(microscope, cam, **csa_params)

        elif cam in acq_params:
            check_mode()
            camera_acquire(microscope, cam, **acq_params[cam])

    if microscope.stem.is_available:
        microscope.stem.enable()
        microscope.stem.magnification = 28000
        detectors = microscope.acquisition.stem_detectors
        for d in detectors:
            detector_acquire(microscope, d, dwell_time=5e-6, binning=1)
        microscope.stem.disable()


if __name__ == '__main__':
    main()
