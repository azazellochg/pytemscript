#!/usr/bin/env python3

import comtypes.client

from pytemscript.utils.constants import CALGETTER
from pytemscript.utils.enums import ModeTypes, BasicTransformTypes, LensSeriesTypes
from pytemscript.plugins.calgetter import CalGetterPlugin


def main():
    """ Get existing calibrations from CalGetter. """
    try:
        comtypes.CoInitialize()
        obj = comtypes.client.CreateObject(CALGETTER)
    except:
        raise RuntimeError("Could not connect to %s interface" % CALGETTER)

    cg = CalGetterPlugin(obj)
    assert cg.is_connected()

    cameras = [
        "BM-Orius",
        "BM-Falcon",
        "EF-Falcon"
    ]
    kv = 300

    #camera = cg.get_reference_camera()
    for camera in cameras:
        print(camera)
        print("Pixel size = ", cg.get_camera_pixel_size(camera))
        print("Camera rotation = ", cg.get_camera_rotation(camera))
        print("Image pixel size 50kx = ", cg.get_image_pixel_size(camera,
                                                                  mode=ModeTypes.MICROPROBE,
                                                                  magindex=29,
                                                                  mag=50000.0,
                                                                  kv=kv))
        print("Beam tilt log to phys", cg.basic_transform(BasicTransformTypes.BEAMTILT_LOG_TO_PHYS,
                                                          x=0.1, y=0.1))

        modes = [ModeTypes.MICROPROBE, ModeTypes.NANOPROBE_STEM]
        for mode in modes:
            print(mode.name)
            print("TEM mags:", cg.get_magnifications(camera, mode=mode, kv=kv))
            print("EFTEM mags:", cg.get_magnifications(camera,
                                                       mode=mode,
                                                       series=LensSeriesTypes.EFTEM,
                                                       kv=kv))
            print("\n")



if __name__ == '__main__':
    print("Testing CalGetter methods...")
    main()
