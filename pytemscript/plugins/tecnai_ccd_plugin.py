import logging
import time
from typing import Optional

from ..utils.enums import AcqImageSize, AcqMode, AcqSpeed
from ..modules.extras import Image
from ..utils.misc import convert_image


class TecnaiCCDPlugin:
    """ Main class that uses FEI Tecnai CCD plugin on microscope PC. """
    def __init__(self, com_iface):
            self.tia_plugin = com_iface.tia
            self.ccd_plugin = com_iface.tecnai_ccd
            self._img_params = dict()

    def _find_camera(self, name: str):
        """Find camera index by name. """
        for i in range(self.ccd_plugin.NumberOfCameras):
            if self.ccd_plugin.CameraName == name:
                return i
        raise KeyError("No camera with name %s" % name)

    def acquire_image(self,
                      cameraName: str,
                      size: AcqImageSize = AcqImageSize.FULL,
                      exp_time: float = 1,
                      binning: int = 1,
                      camerasize: int = 1024,
                      **kwargs) -> Image:
        self._set_camera_param(cameraName, size, exp_time, binning, camerasize, **kwargs)
        if not self.ccd_plugin.IsAcquiring:
            #img = self._ccd_plugin.AcquireImageNotShown(id=1)
            #self._ccd_plugin.AcquireAndShowImage(mode)
            #img = self._ccd_plugin.AcquireImage() # variant
            #img = self._ccd_plugin.AcquireFrontImage()  # safe array
            #img = self._ccd_plugin.FrontImage  # variant
            #img = self._ccd_plugin.AcquireImageShown()
            #img = self._ccd_plugin.AcquireDarkSubtractedImage() # variant

            img = self.ccd_plugin.AcquireRawImage()  # variant

            if kwargs.get('show', False):
                self.ccd_plugin.ShowAcquiredImage()

            pixel_size = self._get_pixel_size()
            self._img_params["pixel_size"] = pixel_size

            image = convert_image(img, name=cameraName, **self._img_params)
            return image
        else:
            raise Exception("Camera is busy acquiring...")

    def _get_pixel_size(self, isSpectrum=False) -> Optional[float]:
        """ Fetch pixel size (in meters) from TIA image. """
        if self.tia_plugin is not None:
            if isSpectrum:
                return self.tia_plugin.ScanningServer().ScanResolution
            else:
                window = self.tia_plugin.ActiveDisplayWindow()
                dsp = window.FindDisplay(window.DisplayNames[0])
                return dsp.image.calibration.deltaX
        else:
            return None

    def _set_camera_param(self,
                          name: str,
                          size: AcqImageSize,
                          exp_time: float,
                          binning: int,
                          camerasize: int,
                          **kwargs):
        """ Find the TEM camera and set its params. """
        camera_index = self._find_camera(name)
        self._img_params['bit_depth'] = self.ccd_plugin.PixelDepth(camera_index)

        self.ccd_plugin.CurrentCamera = camera_index

        if self.ccd_plugin.IsRetractable:
            if not self.ccd_plugin.IsInserted:
                logging.info("Inserting camera %s", name)
                self.ccd_plugin.Insert()
                time.sleep(5)
                if not self.ccd_plugin.IsInserted:
                    raise Exception("Could not insert camera!")

        mode = kwargs.get("mode", AcqMode.RECORD)
        self.ccd_plugin.SelectCameraParameters(mode)
        self.ccd_plugin.Binning = binning
        self.ccd_plugin.ExposureTime = exp_time

        speed = kwargs.get("speed", AcqSpeed.SINGLEFRAME)
        self.ccd_plugin.Speed = speed

        max_width = camerasize // binning
        max_height = camerasize // binning

        if size == AcqImageSize.FULL:
            self.ccd_plugin.CameraLeft = 0
            self.ccd_plugin.CameraTop = 0
            self.ccd_plugin.CameraRight = max_width
            self.ccd_plugin.CameraBottom = max_height
        elif size == AcqImageSize.HALF:
            self.ccd_plugin.CameraLeft = int(max_width / 4)
            self.ccd_plugin.CameraTop = int(max_height / 4)
            self.ccd_plugin.CameraRight = int(max_width * 3 / 4)
            self.ccd_plugin.CameraBottom = int(max_height * 3 / 4)
        elif size == AcqImageSize.QUARTER:
            self.ccd_plugin.CameraLeft = int(max_width * 3 / 8)
            self.ccd_plugin.CameraTop = int(max_height * 3 / 8)
            self.ccd_plugin.CameraRight = int(max_width * 3 / 8 + max_width / 4)
            self.ccd_plugin.CameraBottom = int(max_height * 3 / 8 + max_height / 4)

        self._img_params['width'] = self.ccd_plugin.CameraRight - self.ccd_plugin.CameraLeft
        self._img_params['height'] = self.ccd_plugin.CameraBottom - self.ccd_plugin.CameraTop

    def _run_command(self, command: str, *args):
        exists = self.ccd_plugin.ExecuteScript('DoesFunctionExist("%s")' % command)

        if exists:
            cmd = command % args
            ret = self.ccd_plugin.ExecuteScriptFile(cmd)
            if ret:
                raise Exception("Command %s failed" % cmd)
