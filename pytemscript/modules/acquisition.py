from typing import Optional
import time
import logging
from datetime import datetime
from functools import lru_cache

from ..plugins.tecnai_ccd_plugin import TecnaiCCDPlugin
from ..utils.misc import RequestBody, convert_image
from ..utils.enums import AcqImageSize, AcqShutterMode, PlateLabelDateFormat, ScreenPosition
from .extras import Image, SpecialObj


class AcquisitionObj(SpecialObj):
    """ Wrapper around cameras COM object with specific acquisition methods. """
    def __init__(self, com_object):
        super().__init__(com_object)
        self.current_camera = None

    def acquire_film(self,
                     film_text: str,
                     exp_time: float) -> None:
        """ Expose a film. """
        film = self.com_object
        film.PlateLabelDataType = PlateLabelDateFormat.DDMMYY
        exp_num = film.ExposureNumber
        film.ExposureNumber = exp_num + 1
        film.MainScreen = ScreenPosition.UP
        film.ScreenDim = True
        film.FilmText = film_text.strip()[:96]
        film.ManualExposureTime = exp_time
        film.TakeExposure()

    def find_camera_type(self,
                         cameraName: str,
                         has_cca: bool = False) -> str:
        """ Find camera type by name. """
        if has_cca:
            for cam in self.com_object.CameraContinuousAcquisition.SupportedCameras:
                if cam.Name == cameraName:
                    return "cca"
        else:
            for cam in self.com_object.CameraSingleAcquisition.SupportedCameras:
                if cam.Name == cameraName:
                    return "csa"

        return "std"

    def _check_binning(self,
                       binning: int,
                       is_advanced: bool = False,
                       recording: bool = False):
        """ Check if input binning is in SupportedBinnings.

        :param binning: Input binning
        :type binning: int
        :param is_advanced: Is this an advanced camera?
        :type is_advanced: bool
        :returns: Binning object
        """
        if is_advanced:
            if recording:
                param = self.com_object.CameraContinuousAcquisition.CameraSettings.Capabilities
            else:
                param = self.com_object.CameraSingleAcquisition.CameraSettings.Capabilities
            for b in param.SupportedBinnings:
                if int(b.Width) == int(binning):
                    return b
        else:
            info = self.current_camera.Info
            for b in info.Binnings:
                if int(b) == int(binning):
                    return b

        raise ValueError("Unsupported binning value: %d" % binning)

    def acquire(self, cameraName: str) -> Image:
        """ Perform actual acquisition. Camera settings should be set beforehand.

        :param cameraName: Camera name
        :returns: Image object
        """
        acq = self.com_object
        acq.RemoveAllAcqDevices()
        acq.AddAcqDeviceByName(cameraName)
        imgs = acq.AcquireImages()
        image = convert_image(imgs[0], name=cameraName)

        return image

    def acquire_advanced(self,
                         cameraName: str,
                         recording: bool = False) -> Optional[Image]:
        """ Perform actual acquisition with advanced scripting. """
        if recording:
            self.com_object.CameraContinuousAcquisition.Start()
            self.com_object.CameraContinuousAcquisition.Wait()
            return None
        else:
            img = self.com_object.CameraSingleAcquisition.Acquire()
            self.com_object.CameraSingleAcquisition.Wait()
            image = convert_image(img, name=cameraName, advanced=True)
            return image

    def restore_shutter(self,
                        cameraName: str,
                        prev_shutter_mode: int) -> None:
        """ Restore global shutter mode after exposure. """
        camera = None
        for cam in self.com_object:
            if cam.Info.Name == cameraName:
                camera = cam
        if camera is None:
            raise KeyError("No camera with name %s. If using standard scripting the "
                           "camera must be selected in the microscope user interface" % cameraName)

        camera.Info.ShutterMode = prev_shutter_mode

    def find_camera_size(self, cameraName: str) -> int:
        """ Find camera size by name. Only used by Tecnai CCD plugin. """
        camera = None
        for cam in self.com_object:
            if cam.Info.Name == cameraName:
                camera = cam
        if camera is None:
            raise KeyError("No camera with name %s. If using standard scripting the "
                           "camera must be selected in the microscope user interface" % cameraName)

        return int(camera.Info.Width)

    def set_tem_presets(self,
                        cameraName: str,
                        size: AcqImageSize = AcqImageSize.FULL,
                        exp_time: float = 1,
                        binning: int = 1,
                        **kwargs) -> Optional[int]:

        for cam in self.com_object:
            if cam.Info.Name == cameraName:
                self.current_camera = cam
        if self.current_camera is None:
            raise KeyError("No camera with name %s. If using standard scripting the "
                           "camera must be selected in the microscope user interface" % cameraName)

        info = self.current_camera.Info
        settings = self.current_camera.AcqParams
        settings.ImageSize = size

        binning = self._check_binning(binning)
        settings.Binning = binning
        prev_shutter_mode = None

        if 'correction' in kwargs:
            settings.ImageCorrection = kwargs['correction']
        if 'exposure_mode' in kwargs:
            settings.ExposureMode = kwargs['exposure_mode']
        if 'shutter_mode' in kwargs:
            # Save previous global shutter mode
            prev_shutter_mode = info.ShutterMode
            info.ShutterMode = kwargs['shutter_mode']
        if 'pre_exp_time' in kwargs:
            if kwargs['shutter_mode'] != AcqShutterMode.BOTH:
                raise RuntimeError("Pre-exposures can only be be done "
                                   "when the shutter mode is set to BOTH")
            settings.PreExposureTime = kwargs['pre_exp_time']
        if 'pre_exp_pause_time' in kwargs:
            if kwargs['shutter_mode'] != AcqShutterMode.BOTH:
                raise RuntimeError("Pre-exposures can only be be done when "
                                   "the shutter mode is set to BOTH")
            settings.PreExposurePauseTime = kwargs['pre_exp_pause_time']

        # Set exposure after binning, since it adjusted
        # automatically when binning is set
        settings.ExposureTime = exp_time

        return prev_shutter_mode

    def set_tem_presets_advanced(self,
                                 cameraName: str,
                                 size: AcqImageSize = AcqImageSize.FULL,
                                 exp_time: float = 1,
                                 binning: int = 1,
                                 camera_type: str = "csa",
                                 **kwargs) -> None:
        eer = kwargs.get("eer")
        if camera_type == "cca":
            for cam in self.com_object.CameraContinuousAcquisition.SupportedCameras:
                if cam.Name == cameraName:
                    self.current_camera = cam
        else:  # csa
            for cam in self.com_object.CameraSingleAcquisition.SupportedCameras:
                if cam.Name == cameraName:
                    self.current_camera = cam

        if self.current_camera is None:
            raise KeyError("No camera with name %s. If using standard scripting the "
                           "camera must be selected in the microscope user interface" % cameraName)

        if not self.current_camera.IsInserted:
            self.current_camera.Insert()

        if 'recording' in kwargs:
            self.com_object.CameraContinuousAcquisition.Camera = self.current_camera
            settings = self.com_object.CameraContinuousAcquisition.CameraSettings
            capabilities = settings.Capabilities
            binning = self._check_binning(binning, True, True)
            if hasattr(capabilities, 'SupportsRecording') and capabilities.SupportsRecording:
                settings.RecordingDuration = kwargs['recording']
            else:
                raise NotImplementedError("This camera does not support continuous acquisition")

        else:
            self.com_object.CameraSingleAcquisition.Camera = self.current_camera
            settings = self.com_object.CameraSingleAcquisition.CameraSettings
            capabilities = settings.Capabilities
            binning = self._check_binning(binning, True)

        if binning:
            settings.Binning = binning

        settings.ReadoutArea = size

        # Set exposure after binning, since it adjusted
        # automatically when binning is set
        settings.ExposureTime = exp_time

        if 'align_image' in kwargs:
            if capabilities.SupportsDriftCorrection:
                settings.AlignImage = kwargs['align_image']
            else:
                raise NotImplementedError("This camera does not support drift correction")

        if 'electron_counting' in kwargs:
            if capabilities.SupportsElectronCounting:
                settings.ElectronCounting = kwargs['electron_counting']
            else:
                raise NotImplementedError("This camera does not support electron counting")

        if eer is not None and hasattr(capabilities, 'SupportsEER'):
            if capabilities.SupportsEER:
                settings.EER = eer
                if eer and not settings.ElectronCounting:
                    raise RuntimeError("Electron counting should be enabled when using EER")
                if eer and 'frame_ranges' in kwargs:
                    raise RuntimeError("No frame ranges allowed when using EER")
            else:
                raise NotImplementedError("This camera does not support EER")

        if 'frame_ranges' in kwargs:  # a list of tuples
            dfd = settings.DoseFractionsDefinition
            dfd.Clear()
            for i in kwargs['frame_ranges']:
                dfd.AddRange(i[0], i[1])

            now = datetime.now()
            settings.SubPathPattern = cameraName + "_" + now.strftime("%d%m%Y_%H%M%S")
            output = settings.PathToImageStorage + settings.SubPathPattern

            logging.info("Movie of %s frames will be saved to: %s.mrc",
                         settings.CalculateNumberOfFrames(), output)
            if eer is False:
                logging.info("MRC format can only contain images of up to "
                             "16-bits per pixel, to get true CameraCounts "
                             "multiply pixels by PixelToValueCameraCounts "
                             "factor found in the metadata")

    def set_stem_presets(self,
                         cameraName: str,
                         size: AcqImageSize = AcqImageSize.FULL,
                         dwell_time: float = 1E-5,
                         binning: int = 1,
                         **kwargs) -> None:

        for stem in self.com_object:
            if stem.Info.Name == cameraName:
                self.current_camera = stem
                break
        if self.current_camera is None:
            raise KeyError("No STEM detector with name %s" % cameraName)

        info = self.current_camera.Info

        if 'brightness' in kwargs:
            info.Brightness = kwargs['brightness']
        if 'contrast' in kwargs:
            info.Contrast = kwargs['contrast']

        settings = self.com_object.AcqParams  # self._tem_acq.StemAcqParams
        settings.ImageSize = size

        binning = self._check_binning(binning)
        if binning:
            settings.Binning = binning

        settings.DwellTime = dwell_time

        logging.info("Max resolution: %s, %s",
                     settings.MaxResolution.X,
                     settings.MaxResolution.Y)


class Acquisition:
    """ Image acquisition functions.

    In order for acquisition to be available TIA (TEM Imaging and Acquisition)
    must be running (even if you are using DigitalMicrograph as the CCD server).

    If it is necessary to update the acquisition object (e.g. when the STEM detector
    selection on the TEM UI has been changed), you have to release and recreate the
    main microscope object. If you do not do so, you keep accessing the same
    acquisition object which will not work properly anymore.
    """
    __slots__ = ("__client", "__id_adv", "__camera_type")

    def __init__(self, client):
        self.__client = client
        self.__id_adv = "tem_adv.Acquisitions"
        self.__camera_type = "std"

    @property
    @lru_cache(maxsize=1)
    def __has_cca(self) -> bool:
        """ CCA is supported by Ceta 2. """
        cca = RequestBody(attr=self.__id_adv + ".CameraContinuousAcquisition", validator=bool)

        return self.__client.has_advanced_iface and self.__client.call(method="has", body=cca)

    @property
    @lru_cache(maxsize=1)
    def __has_csa(self) -> bool:
        """ CSA is supported by Ceta 1, Ceta 2, Falcon 3, Falcon 4. """
        csa = RequestBody(attr=self.__id_adv + ".CameraSingleAcquisition", validator=bool)

        return self.__client.has_advanced_iface and self.__client.call(method="has", body=csa)

    @property
    @lru_cache(maxsize=1)
    def __has_film(self) -> bool:
        body = RequestBody(attr="tem.Camera.Stock", validator=int)

        return self.__client.call(method="has", body=body)

    def _check_prerequisites(self) -> None:
        """ Check if buffer cycle or LN filling is
        running before acquisition call. """
        counter = 0
        while counter < 10:
            body = RequestBody(attr="tem.Vacuum.PVPRunning", validator=bool)
            if self.__client.call(method="get", body=body):
                logging.info("Buffer cycle in progress, waiting...\r")
                time.sleep(2)
                counter += 1
            else:
                logging.info("Checking buffer levels...")
                break

        body = RequestBody(attr="tem.TemperatureControl.TemperatureControlAvailable", validator=bool)
        if self.__client.call(method="has", body=body):
            counter = 0
            while counter < 40:
                body = RequestBody("tem.TemperatureControl.DewarsAreBusyFilling", validator=bool)
                if self.__client.call(method="get", body=body):
                    logging.info("Dewars are filling, waiting...\r")
                    time.sleep(30)
                    counter += 1
                else:
                    logging.info("Checking dewars levels...")
                    break

    def _acquire_with_tecnaiccd(self,
                                cameraName: str,
                                size: AcqImageSize,
                                exp_time: float,
                                binning: int,
                                **kwargs):
        if not self.__client.has_ccd_iface:
            raise RuntimeError("Tecnai CCD plugin not found, did you "
                               "pass useTecnaiCCD=True to the Microscope() ?")
        else:
            logging.info("Using TecnaiCCD plugin for Gatan camera")
            # Get camera size from std scripting
            body = RequestBody(attr="tem.Acquisition.Cameras",
                               obj_cls=AcquisitionObj,
                               obj_method="find_camera_size",
                               cameraName=cameraName)
            camerasize = self.__client.call(method="exec_special", body=body)

            body = RequestBody(attr="tecnai_ccd",
                               obj_cls=TecnaiCCDPlugin,
                               obj_method="acquire_image",
                               cameraName=cameraName,
                               size=size,
                               exp_time=exp_time,
                               binning=binning,
                               camerasize=camerasize,
                               **kwargs)
            image = self.__client.call(method="exec_special", body=body)
            logging.info("TEM image acquired on %s", cameraName)

            return image

    def acquire_tem_image(self,
                          cameraName: str,
                          size: AcqImageSize = AcqImageSize.FULL,
                          exp_time: float = 1,
                          binning: int = 1,
                          **kwargs) -> Optional[Image]:
        """ Acquire a TEM image.

        :param cameraName: Camera name
        :type cameraName: str
        :param size: Image size (AcqImageSize enum)
        :type size: IntEnum
        :param exp_time: Exposure time in seconds
        :type exp_time: float
        :param binning: Binning factor
        :keyword bool align_image: Whether frame alignment (i.e. drift correction) is to be applied to the final image as well as the intermediate images. Advanced cameras only.
        :keyword bool electron_counting: Use counting mode. Advanced cameras only.
        :keyword bool eer: Use EER mode. Advanced cameras only.
        :keyword list frame_ranges: List of tuple frame ranges that define the intermediate images, e.g. [(1,2), (2,3)]. Advanced cameras only.
        :keyword bool use_tecnaiccd: Use Tecnai CCD plugin to acquire image via Digital Micrograph, only for Gatan cameras. Requires Microscope() initialized with useTecnaiCCD=True
        :returns: Image object

        Usage:
            >>> microscope = Microscope()
            >>> acq = microscope.acquisition
            >>> img = acq.acquire_tem_image("BM-Falcon", AcqImageSize.FULL, exp_time=5.0, binning=1, electron_counting=True, align_image=True)
            >>> img.save("aligned_sum.mrc")
            >>> print(img.width)
            4096
        """
        if kwargs.get("use_tecnaiccd", False):
            return self._acquire_with_tecnaiccd(cameraName, size, exp_time,
                                                binning, **kwargs)

        if kwargs.get("recording", False) and not self.__has_cca:
            raise NotImplementedError("Recording / continuous acquisition is not available")

        if self.__client.has_advanced_iface:
            # update camera type
            body = RequestBody(attr=self.__id_adv,
                               validator=str,
                               obj_cls=AcquisitionObj,
                               obj_method="find_camera_type",
                               cameraName=cameraName,
                               has_cca=self.__has_cca)
            self.__camera_type = self.__client.call(method="exec_special", body=body)
            logging.debug("Camera type detected for %s: %s", cameraName, self.__camera_type)

        if self.__camera_type == "std": # Use standard scripting
            body = RequestBody(attr="tem.Acquisition.Cameras",
                               obj_cls=AcquisitionObj,
                               obj_method="set_tem_presets",
                               cameraName=cameraName,
                               size=size,
                               exp_time=exp_time,
                               binning=binning,
                               **kwargs)
            prev_shutter_mode = self.__client.call(method="exec_special", body=body)

            self._check_prerequisites()
            body = RequestBody(attr="tem.Acquisition",
                               obj_cls=AcquisitionObj,
                               obj_method="acquire",
                               cameraName=cameraName)
            image = self.__client.call(method="exec_special", body=body)
            logging.info("TEM image acquired on %s", cameraName)

            if prev_shutter_mode is not None:
                body = RequestBody(attr="tem.Acquisition.Cameras",
                                   obj_cls=AcquisitionObj,
                                   obj_method="restore_shutter",
                                   cameraName=cameraName,
                                   prev_shutter_mode=prev_shutter_mode)
                self.__client.call(method="exec_special", body=body)

            return image

        else: # CCA or CSA camera type, use advanced scripting
            body = RequestBody(attr=self.__id_adv,
                               obj_cls=AcquisitionObj,
                               obj_method="set_tem_presets_advanced",
                               cameraName=cameraName,
                               size=size,
                               exp_time=exp_time,
                               binning=binning,
                               camera_type=self.__camera_type,
                               **kwargs)
            self.__client.call(method="exec_special", body=body)

            if "recording" in kwargs:
                body = RequestBody(attr=self.__id_adv,
                                   obj_cls=AcquisitionObj,
                                   obj_method="acquire_advanced",
                                   cameraName=cameraName,
                                   recording=True)
                self.__client.call(method="exec_special", body=body)
                logging.info("TEM image acquired on %s", cameraName)
                logging.info("Continuous acquisition and offloading job are completed.")
                return None
            else:
                body = RequestBody(attr=self.__id_adv,
                                   validator=Image,
                                   obj_cls=AcquisitionObj,
                                   obj_method="acquire_advanced",
                                   cameraName=cameraName)
                image = self.__client.call(method="exec_special", body=body)
                return image

    def acquire_stem_image(self,
                           cameraName: str,
                           size: AcqImageSize,
                           dwell_time: float = 1E-5,
                           binning: int = 1,
                           **kwargs) -> Image:
        """ Acquire a STEM image.

        :param cameraName: Camera name
        :type cameraName: str
        :param size: Image size (AcqImageSize enum)
        :type size: IntEnum
        :param dwell_time: Dwell time in seconds. The frame time equals the dwell time times the number of pixels plus some overhead (typically 20%, used for the line flyback)
        :type dwell_time: float
        :param binning: Binning factor
        :type binning: int
        :keyword float brightness: Brightness setting
        :keyword float contrast: Contrast setting
        :returns: Image object
        """
        body = RequestBody(attr="tem.Acquisition.Detectors",
                           obj_cls=AcquisitionObj,
                           obj_method="set_stem_presets",
                           cameraName=cameraName,
                           size=size,
                           dwell_time=dwell_time,
                           binning=binning,
                           **kwargs)
        self.__client.call(method="exec_special", body=body)

        self._check_prerequisites()
        body = RequestBody(attr="tem.Acquisition",
                           validator=Image,
                           obj_cls=AcquisitionObj,
                           obj_method="acquire",
                           cameraName=cameraName)
        image = self.__client.call(method="exec_special", body=body)
        logging.info("STEM image acquired on %s", cameraName)

        return image

    def acquire_film(self,
                     film_text: str,
                     exp_time: float) -> None:
        """ Expose a film.

        :param film_text: Film text, 96 symbols
        :type film_text: str
        :param exp_time: Exposure time in seconds
        :type exp_time: float
        """
        stock = RequestBody(attr="tem.Camera.Stock", validator=int)

        if self.__has_film and self.__client.call(method="get", body=stock) > 0:
            body = RequestBody(attr="tem.Camera",
                               obj_cls=AcquisitionObj,
                               obj_method="acquire_film",
                               film_text = film_text,
                               exp_time = exp_time)
            self.__client.call(method="exec_special", body=body)
            logging.info("Film exposure completed")
        else:
            raise RuntimeError("Plate is not available or stock is empty!")
