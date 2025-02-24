import logging
import time

from ..utils.enums import AcqImageSize, AcqMode, AcqSpeed
from ..modules.extras import Image
from ..utils.misc import convert_image


class TecnaiCCDPlugin:
    """ Main class that uses FEI Tecnai CCD plugin on microscope PC. """
    def __init__(self, com_iface):
            self._plugin = com_iface
            self._img_params = dict()

    def _find_camera(self, name: str):
        """Find camera index by name. """
        for i in range(self._plugin.NumberOfCameras):
            if self._plugin.CameraName == name:
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
        if not self._plugin.IsAcquiring:
            #img = self._plugin.AcquireImageNotShown(id=1)
            #self._plugin.AcquireAndShowImage(mode)
            #img = self._plugin.AcquireImage() # variant
            #img = self._plugin.AcquireFrontImage()  # safe array
            #img = self._plugin.FrontImage  # variant
            #img = self._plugin.AcquireImageShown()
            #img = self._plugin.AcquireDarkSubtractedImage() # variant

            img = self._plugin.AcquireRawImage()  # variant

            if kwargs.get('show', False):
                self._plugin.ShowAcquiredImage()

            image = convert_image(img, name=cameraName, **self._img_params)
            return image
        else:
            raise Exception("Camera is busy acquiring...")

    def _set_camera_param(self,
                          name: str,
                          size: AcqImageSize,
                          exp_time: float,
                          binning: int,
                          camerasize: int,
                          **kwargs):
        """ Find the TEM camera and set its params. """
        camera_index = self._find_camera(name)
        self._img_params['bit_depth'] = self._plugin.PixelDepth(camera_index)

        self._plugin.CurrentCamera = camera_index

        if self._plugin.IsRetractable:
            if not self._plugin.IsInserted:
                logging.info("Inserting camera %s", name)
                self._plugin.Insert()
                time.sleep(5)
                if not self._plugin.IsInserted:
                    raise Exception("Could not insert camera!")

        mode = kwargs.get("mode", AcqMode.RECORD)
        self._plugin.SelectCameraParameters(mode)
        self._plugin.Binning = binning
        self._plugin.ExposureTime = exp_time

        speed = kwargs.get("speed", AcqSpeed.SINGLEFRAME)
        self._plugin.Speed = speed

        max_width = camerasize // binning
        max_height = camerasize // binning

        if size == AcqImageSize.FULL:
            self._plugin.CameraLeft = 0
            self._plugin.CameraTop = 0
            self._plugin.CameraRight = max_width
            self._plugin.CameraBottom = max_height
        elif size == AcqImageSize.HALF:
            self._plugin.CameraLeft = int(max_width/4)
            self._plugin.CameraTop = int(max_height/4)
            self._plugin.CameraRight = int(max_width*3/4)
            self._plugin.CameraBottom = int(max_height*3/4)
        elif size == AcqImageSize.QUARTER:
            self._plugin.CameraLeft = int(max_width*3/8)
            self._plugin.CameraTop = int(max_height*3/8)
            self._plugin.CameraRight = int(max_width*3/8 + max_width/4)
            self._plugin.CameraBottom = int(max_height*3/8 + max_height/4)

        self._img_params['width'] = self._plugin.CameraRight - self._plugin.CameraLeft
        self._img_params['height'] = self._plugin.CameraBottom - self._plugin.CameraTop

    def _run_command(self, command: str, *args):
        exists = self._plugin.ExecuteScript('DoesFunctionExist("%s")' % command)

        if exists:
            cmd = command % args
            ret = self._plugin.ExecuteScriptFile(cmd)
            if ret:
                raise Exception("Command %s failed" % cmd)
