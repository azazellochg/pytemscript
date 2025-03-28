from typing import Optional, Dict
import time
import logging
from datetime import datetime
from functools import lru_cache

from ..utils.misc import RequestBody, convert_image
from ..utils.enums import AcqImageSize, AcqShutterMode, PlateLabelDateFormat, ScreenPosition
from .extras import Image, SpecialObj


class AcquisitionObj(SpecialObj):
    """ Wrapper around cameras COM object with specific acquisition methods. """
    def __init__(self, com_object):
        super().__init__(com_object)
        self.current_camera = None

    def show_film_settings(self) -> Dict:
        """ Returns a dict with film settings. """
        film = self.com_object
        return {
            "stock": film.Stock,  # Int
            "exposure_time": film.ManualExposureTime,
            "film_text": film.FilmText,
            "exposure_number": film.ExposureNumber,
            "user_code": film.Usercode,  # 3 digits
            "screen_current": film.ScreenCurrent * 1e9
        }

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

    def show_stem_detectors(self) -> Dict:
        """ Returns a dict with STEM detectors parameters. """
        stem_detectors = dict()
        for d in self.com_object:
            info = d.Info
            name = info.Name
            stem_detectors[name] = {"binnings": [int(b) for b in info.Binnings]}
        return stem_detectors

    def show_cameras(self) -> Dict:
        """ Returns a dict with parameters for all TEM cameras. """
        tem_cameras = dict()
        for cam in self.com_object:
            info = cam.Info
            param = cam.AcqParams
            name = info.Name
            tem_cameras[name] = {
                "supports_csa": False,
                "supports_cca": False,
                "height": info.Height,
                "width": info.Width,
                "pixel_size(um)": (info.PixelSize.X / 1e-6, info.PixelSize.Y / 1e-6),
                "binnings": [int(b) for b in info.Binnings],
                "shutter_modes": [AcqShutterMode(x).name for x in info.ShutterModes],
                "pre_exposure_limits(s)": (param.MinPreExposureTime, param.MaxPreExposureTime),
                "pre_exposure_pause_limits(s)": (param.MinPreExposurePauseTime,
                                                 param.MaxPreExposurePauseTime)
            }

        return tem_cameras

    def show_cameras_csa(self) -> Dict:
        """ Returns a dict with parameters for all TEM cameras that support CSA. """
        csa_cameras = dict()
        for cam in self.com_object.SupportedCameras:
            self.com_object.Camera = cam
            param = self.com_object.CameraSettings.Capabilities
            csa_cameras[cam.Name] = {
                "supports_csa": True,
                "supports_cca": False,
                "height": cam.Height,
                "width": cam.Width,
                "pixel_size(um)": (cam.PixelSize.Width / 1e-6, cam.PixelSize.Height / 1e-6),
                "binnings": [int(b.Width) for b in param.SupportedBinnings],
                "exposure_time_range(s)": (param.ExposureTimeRange.Begin,
                                           param.ExposureTimeRange.End),
                "supports_dose_fractions": param.SupportsDoseFractions,
                "max_number_of_fractions": param.MaximumNumberOfDoseFractions,
                "supports_drift_correction": param.SupportsDriftCorrection,
                "supports_electron_counting": param.SupportsElectronCounting,
                "supports_eer": getattr(param, 'SupportsEER', False)
            }

        return csa_cameras

    def show_cameras_cca(self, tem_cameras: Dict) -> Dict:
        """ Update input dict with parameters for all TEM cameras that support CCA. """
        for cam in self.com_object.SupportedCameras:
            if cam.Name in tem_cameras:
                self.com_object.Camera = cam
                param = self.com_object.CameraSettings.Capabilities
                tem_cameras[cam.Name].update({
                    "supports_cca": True,
                    "supports_recording": getattr(param, 'SupportsRecording', False)
                })

        return tem_cameras

    def acquire(self, cameraName: str, **kwargs) -> Image:
        """ Perform actual acquisition. Camera settings should be set beforehand.

        :param str cameraName: Camera name
        :returns: Image object
        """
        acq = self.com_object
        acq.RemoveAllAcqDevices()
        acq.AddAcqDeviceByName(cameraName)
        t0 = time.time()
        imgs = acq.AcquireImages()
        t1 = time.time()
        image = convert_image(imgs[0], name=cameraName, **kwargs)
        t2 = time.time()
        logging.debug("\tAcquisition took %f s" % (t1 - t0))
        logging.debug("\tConverting image took %f s" %(t2 - t1))

        return image

    def acquire_advanced(self,
                         cameraName: str,
                         recording: bool = False,
                         **kwargs) -> Optional[Image]:
        """ Perform actual acquisition with advanced scripting. """
        if recording:
            self.com_object.CameraContinuousAcquisition.Start()
            #self.com_object.CameraContinuousAcquisition.Wait()
            return None
        else:
            t0 = time.time()
            img = self.com_object.CameraSingleAcquisition.Acquire()
            t1 = time.time()
            #self.com_object.CameraSingleAcquisition.Wait()
            image = convert_image(img, name=cameraName, advanced=True, **kwargs)
            t2 = time.time()
            logging.debug("\tAcquisition took %f s" % (t1 - t0))
            logging.debug("\tConverting image took %f s" % (t2 - t1))
            return image

    def restore_shutter(self,
                        cameraName: str,
                        prev_shutter_mode: int) -> None:
        """ Restore global shutter mode after exposure. """
        camera = None
        for cam in self.com_object:
            if cam.Info.Name == cameraName:
                camera = cam
                break
        if camera is None:
            raise KeyError("No camera with name %s. If using standard scripting the "
                           "camera must be selected in the microscope user interface" % cameraName)

        camera.Info.ShutterMode = prev_shutter_mode

    def set_tem_presets(self,
                        cameraName: str,
                        size: AcqImageSize = AcqImageSize.FULL,
                        exp_time: float = 1.0,
                        binning: int = 1,
                        **kwargs) -> Optional[int]:

        for cam in self.com_object:
            if cam.Info.Name == cameraName:
                self.current_camera = cam
                break

        if self.current_camera is None:
            raise KeyError("No camera with name %s. If using standard scripting the "
                           "camera must be selected in the microscope user interface" % cameraName)

        info = self.current_camera.Info
        settings = self.current_camera.AcqParams
        settings.ImageSize = size

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

        # Set exposure after binning, since it adjusted automatically when binning is set
        settings.ExposureTime = exp_time

        return prev_shutter_mode

    def set_tem_presets_advanced(self,
                                 cameraName: str,
                                 size: AcqImageSize = AcqImageSize.FULL,
                                 exp_time: float = 1.0,
                                 binning: int = 1,
                                 use_cca: bool = False,
                                 **kwargs) -> None:
        eer = kwargs.get("eer")
        if use_cca:
            for cam in self.com_object.CameraContinuousAcquisition.SupportedCameras:
                if cam.Name == cameraName:
                    self.current_camera = cam
                    break
        else: # CSA
            for cam in self.com_object.CameraSingleAcquisition.SupportedCameras:
                if cam.Name == cameraName:
                    self.current_camera = cam
                    break

        if self.current_camera is None:
            raise KeyError("No camera with name %s. If using standard scripting the "
                           "camera must be selected in the microscope user interface" % cameraName)

        if not self.current_camera.IsInserted:
            self.current_camera.Insert()

        if 'recording' in kwargs:
            self.com_object.CameraContinuousAcquisition.Camera = self.current_camera
            settings = self.com_object.CameraContinuousAcquisition.CameraSettings
            capabilities = settings.Capabilities
            if hasattr(capabilities, 'SupportsRecording') and capabilities.SupportsRecording:
                settings.RecordingDuration = kwargs['recording']
            else:
                raise NotImplementedError("This camera does not support continuous acquisition")

        else:
            self.com_object.CameraSingleAcquisition.Camera = self.current_camera
            settings = self.com_object.CameraSingleAcquisition.CameraSettings
            capabilities = settings.Capabilities

        # Unfortunately, settings.Binning is an interface, not a simple int
        for b in capabilities.SupportedBinnings:
            if int(b.Width) == int(binning):
                settings.Binning = b

        settings.ReadoutArea = size
        # Set exposure after binning, since it adjusted automatically when binning is set
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

        # EER saving is supported in TEM server 7.6 (Titan 3.6 / Talos 2.6)
        if hasattr(capabilities, 'SupportsEER'):
            eer_is_supported = capabilities.SupportsEER
            if eer and eer_is_supported:
                settings.EER = eer
            elif eer and not eer_is_supported:
                raise NotImplementedError("This camera does not support EER")
            elif not eer and eer_is_supported:
                # EER param is persistent throughout camera COM object lifetime,
                # if not using EER we need to set it to False
                settings.EER = False

            if eer and not settings.ElectronCounting:
                raise RuntimeError("Electron counting should be enabled when using EER")
            if eer and 'group_frames' in kwargs:
                raise RuntimeError("No frame grouping allowed when using EER")

        if capabilities.SupportsDoseFractions:
            dfd = settings.DoseFractionsDefinition
            dfd.Clear()

        if kwargs.get('save_frames'):
            if not capabilities.SupportsDoseFractions:
                raise NotImplementedError("This camera does not support dose fractions")

            total = settings.CalculateNumberOfFrames()
            now = datetime.now()
            settings.SubPathPattern = cameraName + "_" + now.strftime("%d%m%Y_%H%M%S")
            output = settings.PathToImageStorage + settings.SubPathPattern

            if eer in [False, None]:
                group = kwargs.get('group_frames', 1)
                if group < 1:
                    raise ValueError("Frame group size must be at least 1")
                if group > total:
                    raise ValueError("Frame group size cannot exceed maximum possible "
                                     "number of frames: %d. Change exposure time." % total)

                frame_ranges = [(i, min(i + group, total)) for i in range(0, total-1, group)]
                logging.debug("Using frame ranges: %s", frame_ranges[:-1])
                for i in frame_ranges[:-1]:
                    dfd.AddRange(i[0], i[1])

                logging.info("Movie of %d fractions (%d frames, group=%d) "
                             "will be saved to: %s.mrc",
                             len(frame_ranges)-1, total, group, output)
                logging.info("MRC format can only contain images of up to "
                             "16-bits per pixel, to get true CameraCounts "
                             "multiply pixels by PixelToValueCameraCounts "
                             "factor found in the metadata")
            else:
                logging.info("Movie of %d frames will be saved to: %s.eer",
                             total, output)

    def set_stem_presets(self,
                         cameraName: str,
                         size: AcqImageSize = AcqImageSize.FULL,
                         dwell_time: float = 1e-5,
                         binning: int = 1,
                         **kwargs) -> None:

        for stem in self.com_object:
            if stem.Info.Name == cameraName:
                self.current_camera = stem
                break
        if self.current_camera is None:
            raise KeyError("No STEM detector with name %s" % cameraName)

        if 'brightness' in kwargs:
            self.current_camera.Info.Brightness = kwargs['brightness']
        if 'contrast' in kwargs:
            self.current_camera.Info.Contrast = kwargs['contrast']

        settings = self.com_object.AcqParams  # StemAcqParams
        settings.ImageSize = size
        settings.Binning = binning
        settings.DwellTime = dwell_time


class Acquisition:
    """ Image acquisition functions. """
    __slots__ = ("__client", "__id_adv")

    def __init__(self, client):
        self.__client = client
        self.__id_adv = "tem_adv.Acquisitions"

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

    @staticmethod
    def __find_camera(cameraName: str,
                      cameras_dict: Dict,
                      binning: int) -> Dict:
        """ Check camera name and supported binning. """
        camera_dict = cameras_dict.get(cameraName)

        if camera_dict is None:
            raise KeyError("No camera with name %s. If using standard scripting the "
                           "camera must be selected in the microscope user interface" % cameraName)

        if binning not in camera_dict["binnings"]:
            raise ValueError("Unsupported binning value: %d" % binning)

        return camera_dict

    def __check_prerequisites(self) -> None:
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

    def __acquire_with_tecnaiccd(self,
                                 cameraName: str,
                                 size: AcqImageSize,
                                 exp_time: float,
                                 binning: int,
                                 camerasize: int,
                                 **kwargs) -> Image:
        if not self.__client.has_ccd_iface:
            raise RuntimeError("Tecnai CCD plugin not found, did you "
                               "pass useTecnaiCCD=True to the Microscope() ?")
        else:
            logging.info("Using TecnaiCCD plugin for Gatan camera")
            from ..plugins.tecnai_ccd import TecnaiCCDPlugin

            body = RequestBody(attr=None,
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
                          exp_time: float = 1.0,
                          binning: int = 1,
                          **kwargs) -> Optional[Image]:
        """ Acquire a TEM image.

        :param str cameraName: Camera name
        :param AcqImageSize size: Image size
        :param float exp_time: Exposure time in seconds
        :param int binning: Binning factor
        :keyword AcqImageCorrection correction: Image correction
        :keyword AcqExposureMode exposure_mode: CCD exposure mode
        :keyword AcqShutterMode shutter_mode: CCD shutter mode
        :keyword float pre_exp_time: The pre-exposure time in seconds.
        :keyword float pre_exp_pause_time: The time delay after pre-exposure and before the actual CCD exposure in seconds.
        :keyword bool align_image: Whether frame alignment (i.e. drift correction) is to be applied to the final image as well as the intermediate images. Advanced cameras only.
        :keyword bool electron_counting: Use counting mode. Advanced cameras only.
        :keyword bool eer: Use EER mode. Advanced cameras only.
        :keyword bool save_frames: Use to save movies. Advanced cameras only.
        :keyword bool group_frames: Group frames into fractions of this size. Advanced cameras only.
        :keyword float recording: minimum amount of time the acquisition will take, as it will take as much complete frames with the set exposure time as is needed to get to the set RecordingDuration. E.g. if the exposure time is 0.5 and the RecordingDuration is 2.3, there will be an acquisition of 2.5 (5 frames). Advanced cameras only.
        :keyword bool use_tecnaiccd: Use Tecnai CCD plugin to acquire image via Digital Micrograph, only for Gatan cameras. Requires Microscope() initialized with useTecnaiCCD=True
        :returns: Image object
        :rtype: Image

        Extra notes:

        - Keyword arguments correction, exposure_mode, shutter_mode, pre_exp_time, pre_exp_pause_time are only available for CCD cameras that use standard scripting.
        - Advanced cameras are Ceta 1, Ceta 2, Falcon 3, Falcon 4(i).
        - Counting mode and frame saving requires a separate license enabled in TEM software.
        - Continuous acquisition with recording is supported only by Ceta 2.
        - TecnaiCCD plugin is only available for Gatan CCD cameras.

        Usage:
            >>> microscope = Microscope()
            >>> acq = microscope.acquisition
            >>> img = acq.acquire_tem_image("BM-Falcon", AcqImageSize.FULL, exp_time=5.0, binning=1, electron_counting=True, align_image=True)
            >>> img.save("aligned_sum.mrc")
            >>> print(img.width)
            4096
        """
        camera_dict = self.__find_camera(cameraName, self.cameras, binning)

        if kwargs.get("use_tecnaiccd", False):
            return self.__acquire_with_tecnaiccd(cameraName, size, exp_time,
                                                 binning, camera_dict["width"],
                                                 **kwargs)

        if kwargs.get("recording", False) and not camera_dict.get("supports_recording", False):
            raise NotImplementedError("Recording / continuous acquisition is not available")

        csa, cca = camera_dict["supports_csa"], camera_dict["supports_cca"]

        if not csa: # Use standard scripting
            body = RequestBody(attr="tem.Acquisition.Cameras",
                               obj_cls=AcquisitionObj,
                               obj_method="set_tem_presets",
                               cameraName=cameraName,
                               size=size,
                               exp_time=exp_time,
                               binning=binning,
                               **kwargs)
            prev_shutter_mode = self.__client.call(method="exec_special", body=body)

            self.__check_prerequisites()
            body = RequestBody(attr="tem.Acquisition",
                               obj_cls=AcquisitionObj,
                               obj_method="acquire",
                               cameraName=cameraName,
                               **kwargs)
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
                               use_cca=cca,
                               **kwargs)
            self.__client.call(method="exec_special", body=body)

            if "recording" in kwargs:
                body = RequestBody(attr=self.__id_adv,
                                   obj_cls=AcquisitionObj,
                                   obj_method="acquire_advanced",
                                   cameraName=cameraName,
                                   recording=kwargs["recording"],
                                   **kwargs)
                self.__client.call(method="exec_special", body=body)
                logging.info("TEM image acquired on %s", cameraName)
                return None
            else:
                body = RequestBody(attr=self.__id_adv,
                                   validator=Image,
                                   obj_cls=AcquisitionObj,
                                   obj_method="acquire_advanced",
                                   cameraName=cameraName,
                                   **kwargs)
                image = self.__client.call(method="exec_special", body=body)
                return image

    def acquire_stem_image(self,
                           cameraName: str,
                           size: AcqImageSize = AcqImageSize.FULL,
                           dwell_time: float = 1e-5,
                           binning: int = 1,
                           **kwargs) -> Image:
        """ Acquire a STEM image.

        :param str cameraName: Camera name
        :param AcqImageSize size: Image size
        :param float dwell_time: Dwell time in seconds. The frame time equals the dwell time times the number of pixels plus some overhead (typically 20%, used for the line flyback)
        :param int binning: Binning factor. Technically speaking these are "pixel skipping" values, since in STEM we do not combine pixels as a CCD does.
        :keyword float brightness: Brightness setting (0.0-1.0)
        :keyword float contrast: Contrast setting (0.0-1.0)
        :returns: Image object
        :rtype: Image
        """
        _ = self.__find_camera(cameraName, self.stem_detectors, binning)

        body = RequestBody(attr="tem.Acquisition.Detectors",
                           obj_cls=AcquisitionObj,
                           obj_method="set_stem_presets",
                           cameraName=cameraName,
                           size=size,
                           dwell_time=dwell_time,
                           binning=binning,
                           **kwargs)
        self.__client.call(method="exec_special", body=body)

        self.__check_prerequisites()
        body = RequestBody(attr="tem.Acquisition",
                           validator=Image,
                           obj_cls=AcquisitionObj,
                           obj_method="acquire",
                           cameraName=cameraName,
                           **kwargs)
        image = self.__client.call(method="exec_special", body=body)
        logging.info("STEM image acquired on %s", cameraName)

        return image

    def acquire_film(self,
                     film_text: str,
                     exp_time: float) -> None:
        """ Expose a film.

        :param str film_text: Film text, 96 symbols
        :param float exp_time: Exposure time in seconds
        """
        stock = RequestBody(attr="tem.Camera.Stock", validator=int)

        if self.__has_film and self.__client.call(method="get", body=stock) > 0:
            body = RequestBody(attr="tem.Camera",
                               obj_cls=AcquisitionObj,
                               obj_method="acquire_film",
                               film_text=film_text,
                               exp_time=exp_time)
            self.__client.call(method="exec_special", body=body)
            logging.info("Film exposure completed")
        else:
            raise RuntimeError("Plate is not available or stock is empty!")

    @property
    def film_settings(self) -> Dict:
        """ Returns a dict with film settings.

        Note: The plate camera has become obsolete with Windows 7 so
        most of the existing functions are no longer supported.
        """
        if self.__has_film:
            body = RequestBody(attr="tem.Camera",
                               validator=dict,
                               obj_cls=AcquisitionObj,
                               obj_method="show_film_settings")
            return self.__client.call(method="exec_special", body=body)
        else:
            logging.error("No film/plate device detected.")
            return {}

    @property
    def screen_position(self) -> str:
        """ Fluorescent screen position, ScreenPosition enum. (read/write) """
        body = RequestBody(attr="tem.Camera.MainScreen", validator=int)
        result = self.__client.call(method="get", body=body)

        return ScreenPosition(result).name

    @screen_position.setter
    def screen_position(self, value: ScreenPosition) -> None:
        body = RequestBody(attr="tem.Camera.MainScreen", value=value)
        self.__client.call(method="set", body=body)

    @property
    @lru_cache(maxsize=1)
    def stem_detectors(self) -> Dict:
        """ Returns a dict with STEM detectors parameters. """
        body = RequestBody(attr="tem.Acquisition.Detectors",
                           validator=dict,
                           obj_cls=AcquisitionObj,
                           obj_method="show_stem_detectors")
        return self.__client.call(method="exec_special", body=body)

    @property
    @lru_cache(maxsize=1)
    def cameras(self) -> Dict:
        """ Returns a dict with parameters for all TEM cameras.

        supports_csa means single acquisition (Ceta 1, Ceta 2, Falcon 3, Falcon 4(i));
        supports_cca means continuous acquisition (Ceta 2 only)
        """
        body = RequestBody(attr="tem.Acquisition.Cameras",
                           validator=dict,
                           obj_cls=AcquisitionObj,
                           obj_method="show_cameras")
        tem_cameras = self.__client.call(method="exec_special", body=body)

        if not self.__client.has_advanced_iface:
            return tem_cameras

        # CSA is supported by Ceta 1, Ceta 2, Falcon 3, Falcon 4(i)
        body = RequestBody(attr=self.__id_adv + ".CameraSingleAcquisition",
                           validator=dict,
                           obj_cls=AcquisitionObj,
                           obj_method="show_cameras_csa")
        csa_cameras = self.__client.call(method="exec_special", body=body)
        tem_cameras.update(csa_cameras)

        # CCA is supported by Ceta 2
        if self.__has_cca:
            body = RequestBody(attr=self.__id_adv + ".CameraContinuousAcquisition",
                               validator=dict,
                               obj_cls=AcquisitionObj,
                               obj_method="show_cameras_cca",
                               tem_cameras=tem_cameras)
            tem_cameras =  self.__client.call(method="exec_special", body=body)

        return tem_cameras
