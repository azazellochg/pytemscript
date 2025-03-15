from typing import Tuple
import numpy as np

from ..utils.enums import (BasicTransformTypes, ModeTypes,
                           LorentzTypes, LensSeriesTypes)


class CalGetterPlugin:
    """ Main class that communicates with Calibrations service. """
    def __init__(self, com_iface):
        self.cg_iface = com_iface
        assert self.cg_iface.IsConnected is True

    def get_magnifications(self,
                           camera: str,
                           mode: ModeTypes = ModeTypes.NANOPROBE,
                           series: LensSeriesTypes = LensSeriesTypes.ZOOM,
                           lorentz: LorentzTypes = LorentzTypes.OFF,
                           kv: int = 200):
        """ Returns a dict of calibrated magnifications. """
        result = self.cg_iface.ActualMagnifications(camera,
                                                    mode.value,
                                                    series.value,
                                                    lorentz.value,
                                                    kv)
        if result is not None and type(result[0]) is tuple:
            mags_dict = {
                int(value): {
                    "calibrated": calibrated,
                    "index": int(index),
                    "mode": int(mode), # 1 - LM, 2 - Mi, 3 - SA
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

    def get_reference_camera(self):
        """ Returns the reference camera name."""
        return self.cg_iface.GetReferenceCameraName()

    def get_camera_pixel_size(self, camera) -> float:
        """ Get camera physical pixel size in um. """
        res = self.cg_iface.GetCameraPixelSize(camera)
        return res[0] * 1e6

    def get_camera_rotation(self, camera) -> float:
        """ Returns the rotation of the camera relative to the reference camera. """
        return self.cg_iface.CameraRotation(camera)

    def get_image_rotation(self,
                           camera: str,
                           mode: ModeTypes,
                           magindex: int,
                           mag: float,
                           series: LensSeriesTypes = LensSeriesTypes.ZOOM,
                           lorentz: LorentzTypes = LorentzTypes.OFF,
                           kv: int = 200) -> float:
        """ Returns the image rotation angle for a specific magnification. """
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
                             kv: int = 200) -> float:
        """ Returns the image pixel size for a specific magnification in meters."""
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
        Input matrix should be:
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
