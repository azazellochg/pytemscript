from typing import Tuple, Dict, Optional
import time
import numpy as np

from ..utils.enums import BasicTransformTypes, ModeTypes, LorentzTypes, LensSeriesTypes


class CalGetterPlugin:
    """ Main class that communicates with Calibrations service. """
    def __init__(self, com_iface):
        self.cg_iface = com_iface

    def is_connected(self) -> bool:
        """ If calgetter.exe is not already running, this call usually starts it."""
        for _ in range(3):
            try:
                if self.cg_iface.IsConnected:
                    return True
            except:
                pass

            time.sleep(1)

        return False

    def get_magnifications(self,
                           camera: str,
                           mode: ModeTypes = ModeTypes.NANOPROBE,
                           series: LensSeriesTypes = LensSeriesTypes.ZOOM,
                           lorentz: LorentzTypes = LorentzTypes.OFF,
                           kv: int = 300) -> Optional[Dict]:
        """ Returns a dict of calibrated magnifications.
        :param camera: Camera name
        :param mode: Microprobe or nanoprobe mode
        :param series: Zoom of EFTEM projection mode
        :param lorentz: Lorentz lens
        :param kv: voltage
        """
        result = self.cg_iface.ActualMagnifications(camera,
                                                    mode.value,
                                                    series.value,
                                                    lorentz.value,
                                                    kv)
        if result is not None and type(result[0]) is tuple:
            mag_range = {1: "LM", 2: "M", 3: "SA", 4: "Mh"}
            mags_dict = {
                int(value): {
                    "calibrated": calibrated,
                    "index": int(index),
                    "mode": mag_range[int(mode)],
                    "rotation": rotation
                }
                for value, calibrated, index, mode, rotation in zip(result[0],
                                                                    result[1],
                                                                    result[2],
                                                                    result[3],
                                                                    result[4])
            }
            return mags_dict
        else:
            # not calibrated
            return None

    def get_reference_camera(self) -> str:
        """ Returns the reference camera name."""
        return self.cg_iface.GetReferenceCameraName()

    def get_camera_pixel_size(self, camera) -> float:
        """ Get camera physical pixel size in um at current settings.
        :param camera: Camera name
        """
        res = self.cg_iface.GetCameraPixelSize(camera)
        return res[0] * 1e6

    def get_camera_rotation(self, camera) -> float:
        """ Returns the rotation of the camera relative to the reference camera.
         :param camera: Camera name
        """
        return self.cg_iface.CameraRotation(camera)

    def get_image_rotation(self,
                           camera: str,
                           mode: ModeTypes,
                           magindex: int,
                           mag: float,
                           series: LensSeriesTypes = LensSeriesTypes.ZOOM,
                           lorentz: LorentzTypes = LorentzTypes.OFF,
                           kv: int = 300) -> float:
        """ Returns the image rotation angle for a specific magnification.
        :param camera: Camera name
        :param mode: Microprobe or nanoprobe mode
        :param magindex: Magnification index
        :param mag: Nominal magnification
        :param series: Zoom of EFTEM projection mode
        :param lorentz: Lorentz lens
        :param kv: voltage
        """
        return self.cg_iface.ActualTemRotation(camera,
                                               mode.value,
                                               magindex,
                                               mag,
                                               series.value,
                                               lorentz.value,
                                               kv)

    def get_image_pixel_size(self,
                             camera: str,
                             mode: ModeTypes,
                             magindex: int,
                             mag: float,
                             series: LensSeriesTypes = LensSeriesTypes.ZOOM,
                             lorentz: LorentzTypes = LorentzTypes.OFF,
                             kv: int = 300) -> float:
        """ Returns the image pixel size for a specific magnification in meters.
        :param camera: Camera name
        :param mode: Microprobe or nanoprobe mode
        :param magindex: Magnification index
        :param mag: Nominal magnification
        :param series: Zoom of EFTEM projection mode
        :param lorentz: Lorentz lens
        :param kv: voltage
        """
        res = self.cg_iface.GetPhysicalPixelSize(camera,
                                                 mode.value,
                                                 magindex,
                                                 mag,
                                                 series.value,
                                                 lorentz.value,
                                                 kv)
        return res[0]

    def basic_transform(self,
                        transform_type: BasicTransformTypes,
                        input_matrix: np.ndarray = None,
                        x: float = 0,
                        y: float = 0,
                        x_ref: float = 0,
                        y_ref: float = 0) -> Tuple[float, float]:
        """ Transform a vector from one coordinate system to another.
        :param transform_type: Transformation type
        :param input_matrix: Input matrix
        :param x: input x value
        :param y: input y value
        :param x_ref: input x reference value
        :param y_ref: input y reference value

        Input matrix must be 2D:
        A = np.array([[a11, a12, a13],
                      [a21, a22, a23]])
        """
        if input_matrix is None:
            input_matrix = np.zeros((2, 3))

        assert input_matrix.ndim == 2

        x_out, y_out = self.cg_iface.BasicTransform(
            transform_type.value,
            input_matrix[0, 0],
            input_matrix[0, 1],
            input_matrix[0, 2],
            input_matrix[1, 0],
            input_matrix[1, 1],
            input_matrix[1, 2],
            x, y,
            0, 0,
            x_ref, y_ref)
        return x_out, y_out
