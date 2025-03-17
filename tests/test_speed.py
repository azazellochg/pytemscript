import argparse
from typing import Optional, List

from pytemscript.microscope import Microscope
from pytemscript.utils.enums import AcqImageSize
from pytemscript.modules.extras import Image


def acquire_image(microscope: Microscope, camera: str, **kwargs) -> Image:
    image = microscope.acquisition.acquire_tem_image(camera,
                                                     size=AcqImageSize.FULL,
                                                     exp_time=3.0,
                                                     binning=1,
                                                     **kwargs)
    return image


def main(argv: Optional[List] = None) -> None:
    """ Testing acquisition speed. """
    parser = argparse.ArgumentParser(
        description="This test checks acquisition speed",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--debug", dest="debug",
                        default=False, action='store_true',
                        help="Enable debug mode")
    args = parser.parse_args(argv)

    microscope = Microscope(debug=args.debug, useTecnaiCCD=True)

    print("Starting acquisition speed test, connection: %s" % args.type)
    cameras = microscope.acquisition.cameras
    if "BM-Falcon" in cameras:
        camera = "BM-Falcon"
        acquire_image(microscope, camera)
        acquire_image(microscope, camera, use_safearray=False, use_asfile=True)
        acquire_image(microscope, camera, use_tecnaiccd=True)


if __name__ == '__main__':
    main()
