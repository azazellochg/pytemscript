from functools import lru_cache
from typing import Dict
import logging

from .extras import SpecialObj
from ..utils.misc import RequestBody
from ..utils.enums import ScreenPosition, AcqShutterMode


class DetectorsObj(SpecialObj):
    """ Wrapper around cameras COM object."""

    def show_film_settings(self) -> Dict:
        """ Returns a dict with film settings. """
        film = self.com_object
        return {
            "stock": film.Stock,  # Int
            "exposure_time": film.ManualExposureTime,
            "film_text": film.FilmText,
            "exposure_number": film.ExposureNumber,
            "user_code": film.Usercode,  # 3 digits
            "screen_current": film.ScreenCurrent * 1e9  # check if works without film
        }

    def show_stem_detectors(self) -> Dict:
        """ Returns a dict with STEM detectors parameters. """
        stem_detectors = dict()
        for d in self.com_object:
            info = d.Info
            name = info.Name
            stem_detectors[name] = {
                "type": "STEM_DETECTOR",
                "binnings": [int(b) for b in info.Binnings]
            }
        return stem_detectors

    def show_cameras(self) -> Dict:
        """ Returns a dict with parameters for all TEM cameras. """
        tem_cameras = dict()
        for cam in self.com_object:
            info = cam.Info
            param = cam.AcqParams
            name = info.Name
            tem_cameras[name] = {
                "type": "CAMERA",
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
                "type": "CAMERA_ADVANCED",
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
                    "supports_recording": getattr(param, 'SupportsRecording', False)
                })

        return tem_cameras


class Detectors:
    """ CCD/DDD, film/plate and STEM detectors. """
    __slots__ = ("__client", "__id")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem_adv.Acquisitions"

    @property
    @lru_cache(maxsize=1)
    def __has_cca(self) -> bool:
        """ CCA is supported by Ceta 2. """
        cca = RequestBody(attr=self.__id + ".CameraContinuousAcquisition", validator=bool)

        return self.__client.has_advanced_iface and self.__client.call(method="has", body=cca)

    @property
    @lru_cache(maxsize=1)
    def __has_film(self) -> bool:
        body = RequestBody(attr="tem.Camera.Stock", validator=int)

        return self.__client.call(method="has", body=body)

    @property
    def cameras(self) -> Dict:
        """ Returns a dict with parameters for all TEM cameras. """
        body = RequestBody(attr="tem.Acquisition.Cameras",
                           validator=dict,
                           obj_cls=DetectorsObj,
                           obj_method="show_cameras")
        tem_cameras = self.__client.call(method="exec_special", body=body)

        if not self.__client.has_advanced_iface:
            return tem_cameras

        # CSA is supported by Ceta 1, Ceta 2, Falcon 3, Falcon 4
        body = RequestBody(attr=self.__id + ".CameraSingleAcquisition",
                           validator=dict,
                           obj_cls=DetectorsObj,
                           obj_method="show_cameras_csa")
        csa_cameras = self.__client.call(method="exec_special", body=body)
        tem_cameras.update(csa_cameras)

        # CCA is supported by Ceta 2
        if self.__has_cca:
            body = RequestBody(attr=self.__id + ".CameraContinuousAcquisition",
                               validator=dict,
                               obj_cls=DetectorsObj,
                               obj_method="show_cameras_cca")
            tem_cameras =  self.__client.call(method="exec_special", body=body,
                                              tem_cameras=tem_cameras)

        return tem_cameras

    @property
    def stem_detectors(self) -> Dict:
        """ Returns a dict with STEM detectors parameters. """
        body = RequestBody(attr="tem.Acquisition.Detectors",
                           validator=dict,
                           obj_cls=DetectorsObj,
                           obj_method="show_stem_detectors")
        return self.__client.call(method="exec_special", body=body)

    @property
    def screen(self) -> str:
        """ Fluorescent screen position. (read/write)"""
        body = RequestBody(attr="tem.Camera.MainScreen", validator=int)
        result = self.__client.call(method="get", body=body)

        return ScreenPosition(result).name

    @screen.setter
    def screen(self, value: ScreenPosition) -> None:
        body = RequestBody(attr="tem.Camera.MainScreen", value=value)
        self.__client.call(method="set", body=body)

    @property
    def film_settings(self) -> Dict:
        """ Returns a dict with film settings.
        Note: The plate camera _has become obsolete with Win7 so
        most of the existing functions are no longer supported.
        """
        if self.__has_film:
            body = RequestBody(attr="tem.Camera",
                               validator=dict,
                               obj_cls=DetectorsObj,
                               obj_method="show_film_settings")
            return self.__client.call(method="exec_special", body=body)
        else:
            logging.error("No film/plate device detected.")
            return {}
