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
    microscope = Microscope(debug=True, useTecnaiCCD=True)

    print("Starting acquisition speed test")
    cameras = microscope.acquisition.cameras

    for camera in ["BM-Orius", "BM-Ceta", "BM-Falcon", "EF-Falcon", "EF-CCD"]:
        if camera in cameras:

            print("\tUsing SafeArray")
            img1 = acquire_image(microscope, camera)
            img1.save(r"C:/%s_safearray.mrc" % camera, overwrite=True)

            print("\tUsing AsFile")
            # This should be 3x faster than SafeArray method above
            img2 = acquire_image(microscope, camera, use_asfile=True)
            img2.save(r"C:/%s_asfile.mrc" % camera, overwrite=True)

            if camera in ["EF-CCD", "BM-Orius"]:
                print("\tUsing TecnaiCCD")
                # This is faster than std scripting for Gatan CCD cameras
                img3 = acquire_image(microscope, camera, use_tecnaiccd=True)
                img3.save(r"C:/%s_tecnaiccd.mrc" % camera, overwrite=True)


if __name__ == '__main__':
    main()
