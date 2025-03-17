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


def main() -> None:
    """ Testing acquisition speed. """
    microscope = Microscope(debug=True)

    print("Starting acquisition speed test")
    cameras = microscope.acquisition.cameras

    for camera in ["BM-Falcon", "EF-CCD"]:
        if camera in cameras:

            print("\tUsing SafeArray")
            acquire_image(microscope, camera)

            print("\tUsing AsFile")
            acquire_image(microscope, camera, use_safearray=False, use_asfile=True)

            if camera == "EF-CCD":
                print("\tUsing TecnaiCCD/TIA")
                acquire_image(microscope, camera, use_tecnaiccd=True)


if __name__ == '__main__':
    main()
