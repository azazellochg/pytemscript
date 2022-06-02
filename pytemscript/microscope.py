import logging
import math
import time
import os
from datetime import datetime

from .utils.enums import *
from .base_microscope import BaseMicroscope, BaseImage, Vector


class Microscope(BaseMicroscope):
    """ High level interface to the local microscope.
    Creating an instance of this class already queries COM interfaces for the instrument.

    :param address: IP address of the microscope PC, localhost if not specified
    :param timeout: Timeout for remote connection
    :param simulate: NA
    :param useLD: Connect to LowDose server on microscope PC (limited control only)
    :type useLD: bool
    :param useTecnaiCCD: Connect to TecnaiCCD plugin on microscope PC that controls Digital Micrograph (may be faster than via TIA / std scripting)
    :type useTecnaiCCD: bool
    :param useSEMCCD: Connect to SerialEMCCD plugin on Gatan PC that controls Digital Micrograph (may be faster than via TIA / std scripting)
    :type useSEMCCD: bool
    """
    def __init__(self, address=None, timeout=None, simulate=False, useLD=True,
                 useTecnaiCCD=False, useSEMCCD=False):

        super().__init__(address, timeout, simulate, useLD, useTecnaiCCD,
                         useSEMCCD)

        if useTecnaiCCD:
            if self._tecnai_ccd is None:
                raise Exception("Could not use Tecnai CCD plugin, please set useTecnaiCCD=False")
            else:
                from .tecnai_ccd_plugin import TecnaiCCDPlugin
                self._tecnai_ccd_plugin = TecnaiCCDPlugin(self)

        if useSEMCCD:
            if self._sem_ccd is None:
                raise Exception("Could not use SerialEM CCD plugin, please set useSEMCCD=False")
            else:
                from .serialem_ccd_plugin import SerialEMCCDPlugin
                self._sem_ccd_plugin = SerialEMCCDPlugin(self)

        self.acquisition = Acquisition(self)
        self.detectors = Detectors(self)
        self.gun = Gun(self)
        self.lowdose = LowDose(self)
        self.optics = Optics(self)
        self.stem = Stem(self)
        self.temperature = Temperature(self)
        self.vacuum = Vacuum(self)
        self.autoloader = Autoloader(self)
        self.stage = Stage(self)
        self.piezo_stage = PiezoStage(self)

        if self._tem_adv is not None:
            self.user_door = UserDoor(self)
            self.apertures = Apertures(self)

        if useLD:
            self.lowdose = LowDose(self)

    @property
    def family(self):
        """ Returns the microscope product family / platform. """
        return ProductFamily(self._tem.Configuration.ProductFamily).name

    @property
    def condenser_system(self):
        """ Returns the type of condenser lens system: two or three lenses. """
        return CondenserLensSystem(self._tem.Configuration.CondenserLensSystem).name

    @property
    def user_buttons(self):
        """ Returns a dict with assigned hand panels buttons. """
        return {b.Name: b.Label for b in self._tem.UserButtons}


class UserDoor:
    """ User door hatch controls. """
    def __init__(self, microscope):
        self._tem_door = microscope._tem_adv.UserDoorHatch

    @property
    def state(self):
        """ Returns door state. """
        return HatchState(self._tem_door.State).name

    def open(self):
        """ Open the door. """
        if self._tem_door.IsControlAllowed:
            self._tem_door.Open()
        else:
            raise Exception("Door control is unavailable")

    def close(self):
        """ Close the door. """
        if self._tem_door.IsControlAllowed:
            self._tem_door.Close()
        else:
            raise Exception("Door control is unavailable")


class Acquisition:
    """ Image acquisition functions. """
    def __init__(self, microscope):
        self._tem = microscope._tem
        self._tem_acq = self._tem.Acquisition
        self._tem_cam = self._tem.Camera
        self._is_advanced = False
        self._has_advanced = microscope._tem_adv is not None
        self._prev_shutter_mode = None
        self._eer = False

        try:
            _ = self._tem_cam.Stock
            self._has_film = True
        except:
            self._has_film = False

        if self._has_advanced:
            self._tem_csa = microscope._tem_adv.Acquisitions.CameraSingleAcquisition

        if getattr(microscope, "_tecnai_ccd_plugin", None):
            self._ccdplugin = microscope._tecnai_ccd_plugin

    def _find_camera(self, name):
        """Find camera object by name. Check adv scripting first. """
        if self._has_advanced:
            for cam in self._tem_csa.SupportedCameras:
                if cam.Name == name:
                    self._is_advanced = True
                    return cam
        for cam in self._tem_acq.Cameras:
            if cam.Info.Name == name:
                return cam
        raise KeyError("No camera with name %s. If using standard scripting the "
                       "camera must be selected in the microscope user interface" % name)

    def _find_stem_detector(self, name):
        """Find STEM detector object by name"""
        for stem in self._tem_acq.Detectors:
            if stem.Info.Name == name:
                return stem
        raise KeyError("No STEM detector with name %s" % name)

    def _check_binning(self, binning, camera, is_advanced=False):
        """ Check if input binning is in SupportedBinnings.

        :param binning: Input binning
        :type binning: int
        :param camera: Camera object
        :param is_advanced: Is this an advanced camera?
        :type is_advanced: bool
        :returns: Binning object
        """
        if is_advanced:
            param = self._tem_csa.CameraSettings.Capabilities
            for b in param.SupportedBinnings:
                if int(b.Width) == int(binning):
                    return b
        else:
            info = camera.Info
            for b in info.Binnings:
                if int(b) == int(binning):
                    return b

        raise Exception("Unsupported binning value: %d" % binning)

    def _set_camera_param(self, name, size, exp_time, binning, **kwargs):
        """ Find the TEM camera and set its params. """
        camera = self._find_camera(name)

        if self._is_advanced:
            if not camera.IsInserted:
                camera.Insert()

            self._tem_csa.Camera = camera

            settings = self._tem_csa.CameraSettings
            capabilities = settings.Capabilities
            settings.ReadoutArea = size

            binning = self._check_binning(binning, camera, is_advanced=True)
            if binning:
                settings.Binning = binning

            # Set exposure after binning, since it adjusted automatically when binning is set
            settings.ExposureTime = exp_time

            if 'align_image' in kwargs:
                if capabilities.SupportsDriftCorrection:
                    settings.AlignImage = kwargs['align_image']
                else:
                    raise Exception("This camera does not support drift correction")

            if 'electron_counting' in kwargs:
                if capabilities.SupportsElectronCounting:
                    settings.ElectronCounting = kwargs['electron_counting']
                else:
                    raise Exception("This camera does not support electron counting")

            if 'eer' in kwargs and hasattr(capabilities, 'SupportsEER'):
                if capabilities.SupportsEER:
                    self._eer = kwargs['eer']
                    settings.EER = self._eer

                    if self._eer and not settings.ElectronCounting:
                        raise Exception("Electron counting should be enabled when using EER")
                    if self._eer and 'frame_ranges' in kwargs:
                        raise Exception("No frame ranges allowed when using EER")
                else:
                    raise Exception("This camera does not support EER")

            if 'frame_ranges' in kwargs:  # a list of tuples
                dfd = settings.DoseFractionsDefinition
                dfd.Clear()
                for i in kwargs['frame_ranges']:
                    dfd.AddRange(i[0], i[1])

                now = datetime.now()
                settings.SubPathPattern = name + "_" + now.strftime("%d%m%Y_%H%M%S")
                output = settings.PathToImageStorage + settings.SubPathPattern

                print("Movie of %s frames will be saved to: %s.mrc" % (
                    settings.CalculateNumberOfFrames(), output))
                if not self._eer:
                    print("MRC format can only contain images of up to "
                          "16-bits per pixel, to get true CameraCounts "
                          "multiply pixels by PixelToValueCameraCounts "
                          "factor found in the metadata")

        else:
            info = camera.Info
            settings = camera.AcqParams
            settings.ImageSize = size

            binning = self._check_binning(binning, camera)
            settings.Binning = binning

            if 'correction' in kwargs:
                settings.ImageCorrection = kwargs['correction']
            if 'exposure_mode' in kwargs:
                settings.ExposureMode = kwargs['exposure_mode']
            if 'shutter_mode' in kwargs:
                # Save previous global shutter mode
                self._prev_shutter_mode = (info, info.ShutterMode)
                info.ShutterMode = kwargs['shutter_mode']
            if 'pre_exp_time' in kwargs:
                if kwargs['shutter_mode'] != AcqShutterMode.BOTH:
                    raise Exception("Pre-exposures can only be be done when the shutter mode is set to BOTH")
                settings.PreExposureTime = kwargs['pre_exp_time']
            if 'pre_exp_pause_time' in kwargs:
                if kwargs['shutter_mode'] != AcqShutterMode.BOTH:
                    raise Exception("Pre-exposures can only be be done when the shutter mode is set to BOTH")
                settings.PreExposurePauseTime = kwargs['pre_exp_pause_time']

            # Set exposure after binning, since it adjusted automatically when binning is set
            settings.ExposureTime = exp_time

    def _set_film_param(self, film_text, exp_time, **kwargs):
        """ Set params for plate camera / film. """
        self._tem_cam.FilmText = film_text
        self._tem_cam.ManualExposureTime = exp_time

    def _acquire(self, cameraName):
        """ Perform actual acquisition.

        :returns: Image object
        """
        self._tem_acq.RemoveAllAcqDevices()
        self._tem_acq.AddAcqDeviceByName(cameraName)
        img = self._tem_acq.AcquireImages()

        if self._prev_shutter_mode is not None:
            # restore previous shutter mode
            obj = self._prev_shutter_mode[0]
            old_value = self._prev_shutter_mode[1]
            obj.ShutterMode = old_value

        return Image(img[0], name=cameraName)

    def _check_prerequisites(self):
        """ Check if buffer cycle or LN filling is running before acquisition call. """
        tc = self._tem.TemperatureControl
        counter = 0
        while counter < 10:
            if self._tem.Vacuum.PVPRunning:
                print("Buffer cycle in progress, waiting...\r")
                time.sleep(2)
                counter += 1
            else:
                print("Checking buffer levels...")
                break

        counter = 0
        while counter < 40:
            if tc.TemperatureControlAvailable and tc.DewarsAreBusyFilling:
                print("Dewars are filling, waiting...\r")
                time.sleep(30)
                counter += 1
            else:
                print("Checking dewars levels...")
                break

    def _acquire_with_tecnaiccd(self, cameraName, size, exp_time, binning, **kwargs):
        if not hasattr(self, "_ccdplugin"):
            raise Exception("Tecnai CCD plugin not found, did you pass useTecnaiCCD=True to Microscope() ?")
        else:
            logging.info("Using TecnaiCCD plugin for Gatan camera")
            camerasize = self._find_camera(cameraName).Info.Width  # Get camera size from std scripting
            return self._ccdplugin.acquire_image(cameraName, size, exp_time, binning, camerasize=camerasize, **kwargs)

    def acquire_tem_image(self, cameraName, size=AcqImageSize.FULL, exp_time=1, binning=1, **kwargs):
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
            return self._acquire_with_tecnaiccd(cameraName, size, exp_time, binning, **kwargs)

        self._set_camera_param(cameraName, size, exp_time, binning, **kwargs)
        if self._is_advanced:
            self._check_prerequisites()
            img = self._tem_csa.Acquire()
            self._tem_csa.Wait()
            return Image(img, name=cameraName, isAdvanced=True)

        self._check_prerequisites()
        self._acquire(cameraName)

    def acquire_stem_image(self, cameraName, size, dwell_time=1E-5, binning=1, **kwargs):
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
        det = self._find_stem_detector(cameraName)
        info = det.Info

        if 'brightness' in kwargs:
            info.Brightness = kwargs['brightness']
        if 'contrast' in kwargs:
            info.Contrast = kwargs['contrast']

        settings = self._tem_acq.StemAcqParams
        settings.ImageSize = size

        binning = self._check_binning(binning, det)
        if binning:
            settings.Binning = binning

        settings.DwellTime = dwell_time

        print("Max resolution:",
              settings.MaxResolution.X,
              settings.MaxResolution.Y)

        self._check_prerequisites()
        self._acquire(cameraName)

    def acquire_film(self, film_text, exp_time, **kwargs):
        """ Expose a film.

        :param film_text: Film text
        :type film_text: str
        :param exp_time: Exposure time in seconds
        :type exp_time: float
        """
        if self._has_film and self._tem_cam.Stock > 0:
            self._tem_cam.PlateLabelDataType = PlateLabelDateFormat.DDMMYY
            exp_num = self._tem_cam.ExposureNumber
            self._tem_cam.ExposureNumber = exp_num + 1
            self._tem_cam.MainScreen = ScreenPosition.UP
            self._tem_cam.ScreenDim = True

            self._set_film_param(film_text, exp_time, **kwargs)
            self._tem_cam.TakeExposure()
        else:
            raise Exception("Plate is not available or stock is empty!")


class Detectors:
    """ CCD/DDD, film/plate and STEM detectors. """
    def __init__(self, microscope):
        self._tem_acq = microscope._tem.Acquisition
        self._tem_cam = microscope._tem.Camera
        self._has_advanced = microscope._tem_adv is not None

        try:
            _ = self._tem_cam.Stock
        except:
            logging.info("No film/plate device detected.")

        if self._has_advanced:
            self._tem_csa = microscope._tem_adv.Acquisitions.CameraSingleAcquisition

    @property
    def cameras(self):
        """ Returns a dict with parameters for all cameras. """
        self._cameras = dict()
        for cam in self._tem_acq.Cameras:
            info = cam.Info
            param = cam.AcqParams
            name = info.Name
            self._cameras[name] = {
                "type": "CAMERA",
                "height": info.Height,
                "width": info.Width,
                "pixel_size(um)": (info.PixelSize.X / 1e-6, info.PixelSize.Y / 1e-6),
                "binnings": [int(b) for b in info.Binnings],
                "shutter_modes": [AcqShutterMode(x).name for x in info.ShutterModes],
                "pre_exposure_limits(s)": (param.MinPreExposureTime, param.MaxPreExposureTime),
                "pre_exposure_pause_limits(s)": (param.MinPreExposurePauseTime, param.MaxPreExposurePauseTime)
            }
        if not self._has_advanced:
            return self._cameras

        for cam in self._tem_csa.SupportedCameras:
            self._tem_csa.Camera = cam
            param = self._tem_csa.CameraSettings.Capabilities
            self._cameras[cam.Name] = {
                "type": "CAMERA_ADVANCED",
                "height": cam.Height,
                "width": cam.Width,
                "pixel_size(um)": (cam.PixelSize.Width / 1e-6, cam.PixelSize.Height / 1e-6),
                "binnings": [int(b.Width) for b in param.SupportedBinnings],
                "exposure_time_range(s)": (param.ExposureTimeRange.Begin, param.ExposureTimeRange.End),
                "supports_dose_fractions": param.SupportsDoseFractions,
                "max_number_of_fractions": param.MaximumNumberOfDoseFractions,
                "supports_drift_correction": param.SupportsDriftCorrection,
                "supports_electron_counting": param.SupportsElectronCounting,
                "supports_eer": getattr(param, 'SupportsEER', False)
            }

        return self._cameras

    @property
    def stem_detectors(self):
        """ Returns a dict with STEM detectors parameters. """
        self._stem_detectors = dict()
        for det in self._tem_acq.Detectors:
            info = det.Info
            name = info.Name
            self._stem_detectors[name] = {
                "type": "STEM_DETECTOR",
                "binnings": [int(b) for b in info.Binnings]
            }
        return self._stem_detectors

    @property
    def screen(self):
        """ Fluorescent screen position. (read/write)"""
        return ScreenPosition(self._tem_cam.MainScreen).name

    @screen.setter
    def screen(self, value):
        self._tem_cam.MainScreen = value

    @property
    def film_settings(self):
        """ Returns a dict with film settings. """
        return {
            "stock": self._tem_cam.Stock,
            "exposure_time": self._tem_cam.ManualExposureTime,
            "film_text": self._tem_cam.FilmText,
            "exposure_number": self._tem_cam.ExposureNumber,
            "user_code": self._tem_cam.Usercode,
            "screen_current": self._tem_cam.ScreenCurrent
        }


class Temperature:
    """ LN dewars and temperature controls. """
    def __init__(self, microscope):
        self._tem_temp_control = microscope._tem.TemperatureControl

    def force_refill(self):
        """ Forces LN refill if the level is below 70%, otherwise does nothing. """
        if self._tem_temp_control.TemperatureControlAvailable:
            self._tem_temp_control.ForceRefill()
        else:
            raise Exception("TemperatureControl is not available")

    def dewar_level(self, dewar):
        """ Returns the LN level (%) in a dewar.

        :param dewar: Dewar name (RefrigerantDewar enum)
        :type dewar: IntEnum
        """
        if self._tem_temp_control.TemperatureControlAvailable:
            return self._tem_temp_control.RefrigerantLevel(dewar)
        else:
            raise Exception("TemperatureControl is not available")

    @property
    def is_dewar_filling(self):
        """ Returns TRUE if any of the dewars is currently busy filling. """
        if self._tem_temp_control.TemperatureControlAvailable:
            return self._tem_temp_control.DewarsAreBusyFilling
        else:
            raise Exception("TemperatureControl is not available")

    @property
    def dewars_time(self):
        """ Returns remaining time (seconds) until the next dewar refill.
        Returns -1 if no refill is scheduled (e.g. All room temperature, or no
        dewar present).
        """
        if self._tem_temp_control.TemperatureControlAvailable:
            return self._tem_temp_control.DewarsRemainingTime
        else:
            raise Exception("TemperatureControl is not available")


class Autoloader:
    """ Sample loading functions. """
    def __init__(self, microscope):
        self._tem_autoloader = microscope._tem.AutoLoader

    @property
    def number_of_slots(self):
        """ The number of slots in a cassette. """
        if self._tem_autoloader.AutoLoaderAvailable:
            return self._tem_autoloader.NumberOfCassetteSlots
        else:
            raise Exception("Autoloader is not available")

    def load_cartridge(self, slot):
        """ Loads the cartridge in the given slot into the microscope.

        :param slot: Slot number
        :type slot: int
        """
        if self._tem_autoloader.AutoLoaderAvailable:
            total = self.number_of_slots
            slot = int(slot)
            if slot > total:
                raise Exception("Only %s slots are available" % total)
            if self.slot_status(slot) != CassetteSlotStatus.OCCUPIED.name:
                raise Exception("Slot %d is not occupied" % slot)
            self._tem_autoloader.LoadCartridge(slot)
        else:
            raise Exception("Autoloader is not available")

    def unload_cartridge(self):
        """ Unloads the cartridge currently in the microscope and puts it back into its
        slot in the cassette.
        """
        if self._tem_autoloader.AutoLoaderAvailable:
            self._tem_autoloader.UnloadCartridge()
        else:
            raise Exception("Autoloader is not available")

    def run_inventory(self):
        """ Performs an inventory of the cassette. """
        # TODO: check if cassette is present
        if self._tem_autoloader.AutoLoaderAvailable:
            self._tem_autoloader.PerformCassetteInventory()
        else:
            raise Exception("Autoloader is not available")

    def slot_status(self, slot):
        """ The status of the slot specified.

        :param slot: Slot number
        :type slot: int
        """
        if self._tem_autoloader.AutoLoaderAvailable:
            total = self.number_of_slots
            if slot > total:
                raise Exception("Only %s slots are available" % total)
            status = self._tem_autoloader.SlotStatus(int(slot))
            return CassetteSlotStatus(status).name
        else:
            raise Exception("Autoloader is not available")


class Stage:
    """ Stage functions. """
    def __init__(self, microscope):
        self._tem_stage = microscope._tem.Stage

    def _from_dict(self, position, **values):
        axes = 0
        for key, value in values.items():
            if key not in 'xyzab':
                raise ValueError("Unexpected axis: %s" % key)
            attr_name = key.upper()
            setattr(position, attr_name, float(value))
            axes |= getattr(StageAxes, attr_name)
        return position, axes

    def _beta_available(self):
        return self.limits['b']['unit'] != MeasurementUnitType.UNKNOWN

    def _change_position(self, direct=False, **kwargs):
        if self._tem_stage.Status == StageStatus.READY:
            # convert units first
            new_pos = {key: kwargs[key] * 1e6 for key in 'xyz'}
            new_pos.update({key: math.radians(kwargs[key]) for key in 'ab'})
            speed = kwargs.pop("speed", None)

            if 'b' in new_pos and not self._beta_available():
                raise Exception("B-axis is not available")

            current_pos = self._tem_stage.Position
            new_pos, axes = self._from_dict(current_pos, **new_pos)
            if not direct:
                self._tem_stage.MoveTo(new_pos, axes)
                return
            if speed is not None:
                self._tem_stage.GoToWithSpeed(new_pos, axes, speed)
            else:
                self._tem_stage.GoTo(new_pos, axes)
        else:
            raise Exception("Stage is not ready.")

    @property
    def status(self):
        """ The current state of the stage. """
        return StageStatus(self._tem_stage.Status).name

    @property
    def holder(self):
        """ The current specimen holder type. """
        return StageHolderType(self._tem_stage.Holder).name

    @property
    def position(self):
        """ The current position of the stage (x,y,z in um and a,b in degrees). """
        pos = self._tem_stage.Position
        result = {key: getattr(pos, key.upper()) * 1e6 for key in 'xyz'}
        result.update({key: math.degrees(getattr(pos, key.upper())) for key in 'ab'})

        return result

    def go_to(self, **kwargs):
        """ Makes the holder directly go to the new position by moving all axes
        simultaneously. Keyword args can be x,y,z,a or b.

        :keyword float speed: fraction of the standard speed setting (max 1.0)
        """
        self._change_position(direct=True, **kwargs)

    def move_to(self, **kwargs):
        """ Makes the holder safely move to the new position.
        Keyword args can be x,y,z,a or b.
        """
        kwargs['speed'] = None
        self._change_position(**kwargs)

    @property
    def limits(self):
        """ Returns a dict with stage move limits. """
        result = dict()
        for axis in 'xyzab':
            data = self._tem_stage.AxisData(StageAxes[axis.upper()])
            result[axis] = {
                'min': data.MinPos,
                'max': data.MaxPos,
                'unit': MeasurementUnitType(data.UnitType).name
            }
        return result


class PiezoStage:
    """ Piezo stage functions. """
    def __init__(self, microscope):
        try:
            self._tem_pstage = microscope._tem_adv.PiezoStage
            self.high_resolution = self._tem_pstage.HighResolution
        except:
            logging.info("PiezoStage interface is not available.")

    @property
    def position(self):
        """ The current position of the piezo stage (x,y,z in um). """
        pos = self._tem_pstage.CurrentPosition
        return {key: getattr(pos, key.upper()) * 1e6 for key in 'xyz'}

    @property
    def position_range(self):
        """ Return min and max positions. """
        return self._tem_pstage.GetPositionRange()

    @property
    def velocity(self):
        """ Returns a dict with stage velocities. """
        pos = self._tem_pstage.CurrentJogVelocity
        return {key: getattr(pos, key.upper()) for key in 'xyz'}


class Vacuum:
    """ Vacuum functions. """
    def __init__(self, microscope):
        self._tem_vacuum = microscope._tem.Vacuum

    @property
    def status(self):
        """ Status of the vacuum system. """
        return VacuumStatus(self._tem_vacuum.Status).name

    @property
    def is_buffer_running(self):
        """ Checks whether the prevacuum pump is currently running
        (consequences: vibrations, exposure function blocked
        or should not be called).
        """
        return self._tem_vacuum.PVPRunning

    @property
    def is_column_open(self):
        """ The status of the column valves. """
        return self._tem_vacuum.ColumnValvesOpen

    @property
    def gauges(self):
        """ Returns a dict with vacuum gauges information.
        Pressure values are in Pascals.
        """
        gauges = {}
        for g in self._tem_vacuum.Gauges:
            # g.Read()
            if g.Status == GaugeStatus.UNDEFINED:
                # set manually if undefined, otherwise fails
                pressure_level = GaugePressureLevel.UNDEFINED
            else:
                pressure_level = GaugePressureLevel(g.PressureLevel).name

            gauges[g.Name] = {
                "status": GaugeStatus(g.Status).name,
                "pressure": g.Pressure,
                "trip_level": pressure_level
            }
        return gauges

    def column_open(self):
        """ Open column valves. """
        self._tem_vacuum.ColumnValvesOpen = True

    def column_close(self):
        """ Close column valves. """
        self._tem_vacuum.ColumnValvesOpen = False

    def run_buffer_cycle(self):
        """ Runs a pumping cycle to empty the buffer. """
        self._tem_vacuum.RunBufferCycle()


class Optics:
    """ Projection, Illumination functions. """
    def __init__(self, microscope):
        self._tem = microscope._tem
        self._tem_adv = microscope._tem_adv
        self._tem_cam = self._tem.Camera
        self._tem_illumination = self._tem.Illumination
        self._tem_projection = self._tem.Projection
        self._tem_control = self._tem.InstrumentModeControl

        self.illumination = Illumination(self._tem)
        self.projection = Projection(self._tem_projection)

    @property
    def screen_current(self):
        """ The current measured on the fluorescent screen (units: nanoAmperes). """
        return self._tem_cam.ScreenCurrent * 1e9

    @property
    def is_beam_blanked(self):
        """ Status of the beam blanker. """
        return self._tem_illumination.BeamBlanked

    @property
    def is_shutter_override_on(self):
        """ Determines the state of the shutter override function. """
        return self._tem.BlankerShutter.ShutterOverrideOn

    @property
    def is_autonormalize_on(self):
        """ Status of the automatic normalization procedures performed by
        the TEM microscope. Normally they are active, but for scripting it can be
        convenient to disable them temporarily.
        """
        return self._tem.AutoNormalizeEnabled

    def beam_blank(self):
        """ Activates the beam blanker. """
        self._tem_illumination.BeamBlanked = True

    def beam_unblank(self):
        """ Deactivates the beam blanker. """
        self._tem_illumination.BeamBlanked = False

    def normalize_all(self):
        """ Normalize all lenses. """
        self._tem.NormalizeAll()

    def normalize(self, mode):
        """ Normalize condenser or projection lens system.
        :param mode: Normalization mode (ProjectionNormalization or IlluminationNormalization enum)
        :type mode: IntEnum
        """
        if mode in ProjectionNormalization:
            self._tem_projection.Normalize(mode)
        elif mode in IlluminationNormalization:
            self._tem_illumination.Normalize(mode)
        else:
            raise ValueError("Unknown normalization mode: %s" % mode)


class Stem:
    """ STEM functions. """
    def __init__(self, microscope):
        self._tem = microscope._tem
        self._tem_illumination = self._tem.Illumination
        self._tem_control = self._tem.InstrumentModeControl

    @property
    def is_available(self):
        """ Returns whether the microscope has a STEM system or not. """
        return self._tem_control.StemAvailable

    def enable(self):
        """ Switch to STEM mode."""
        if self._tem_control.StemAvailable:
            self._tem_control.InstrumentMode = InstrumentMode.STEM
        else:
            raise Exception("No STEM mode available")

    def disable(self):
        """ Switch back to TEM mode. """
        self._tem_control.InstrumentMode = InstrumentMode.TEM

    @property
    def magnification(self):
        """ The magnification value in STEM mode. (read/write)"""
        if self._tem_control.InstrumentMode == InstrumentMode.STEM:
            return self._tem_illumination.StemMagnification
        else:
            raise Exception("Microscope not in STEM mode.")

    @magnification.setter
    def magnification(self, mag):
        if self._tem_control.InstrumentMode == InstrumentMode.STEM:
            self._tem_illumination.StemMagnification = float(mag)
        else:
            raise Exception("Microscope not in STEM mode.")

    @property
    def rotation(self):
        """ The STEM rotation angle (in mrad). (read/write)"""
        if self._tem_control.InstrumentMode == InstrumentMode.STEM:
            return self._tem_illumination.StemRotation * 1e3
        else:
            raise Exception("Microscope not in STEM mode.")

    @rotation.setter
    def rotation(self, rot):
        if self._tem_control.InstrumentMode == InstrumentMode.STEM:
            self._tem_illumination.StemRotation = float(rot) * 1e-3
        else:
            raise Exception("Microscope not in STEM mode.")

    @property
    def scan_field_of_view(self):
        """ STEM full scan field of view. (read/write)"""
        if self._tem_control.InstrumentMode == InstrumentMode.STEM:
            return (self._tem_illumination.StemFullScanFieldOfView.X,
                    self._tem_illumination.StemFullScanFieldOfView.Y)
        else:
            raise Exception("Microscope not in STEM mode.")

    @scan_field_of_view.setter
    def scan_field_of_view(self, values):
        if self._tem_control.InstrumentMode == InstrumentMode.STEM:
            Vector.set(self._tem_illumination, "StemFullScanFieldOfView", values)
        else:
            raise Exception("Microscope not in STEM mode.")


class Illumination:
    """ Illumination functions. """
    def __init__(self, tem):
        self._tem = tem
        self._tem_illumination = self._tem.Illumination

    @property
    def spotsize(self):
        """ Spotsize number, usually 1 to 11. (read/write)"""
        return self._tem_illumination.SpotsizeIndex

    @spotsize.setter
    def spotsize(self, value):
        self._tem_illumination.SpotsizeIndex = int(value)

    @property
    def intensity(self):
        """ Intensity / C2 condenser lens value. (read/write)"""
        return self._tem_illumination.Intensity

    @intensity.setter
    def intensity(self, value):
        self._tem_illumination.Intensity = float(value)

    @property
    def intensity_zoom(self):
        """ Intensity zoom. Set to False to disable. (read/write)"""
        return self._tem_illumination.IntensityZoomEnabled

    @intensity_zoom.setter
    def intensity_zoom(self, value):
        self._tem_illumination.IntensityZoomEnabled = bool(value)

    @property
    def intensity_limit(self):
        """ Intensity limit. Set to False to disable. (read/write)"""
        return self._tem_illumination.IntensityLimitEnabled

    @intensity_limit.setter
    def intensity_limit(self, value):
        self._tem_illumination.IntensityLimitEnabled = bool(value)

    @property
    def beam_shift(self):
        """ Beam shift X and Y in um. (read/write)"""
        return (self._tem_illumination.Shift.X * 1e6,
                self._tem_illumination.Shift.Y * 1e6)

    @beam_shift.setter
    def beam_shift(self, value):
        value[0] *= 1e-6
        value[1] *= 1e-6
        Vector.set(self._tem_illumination, "Shift", value)

    @property
    def rotation_center(self):
        """ Rotation center X and Y in mrad. (read/write)"""
        return (self._tem_illumination.RotationCenter.X * 1e3,
                self._tem_illumination.RotationCenter.Y * 1e3)

    @rotation_center.setter
    def rotation_center(self, value):
        value[0] *= 1e-3
        value[1] *= 1e-3
        Vector.set(self._tem_illumination, "RotationCenter", value)

    @property
    def condenser_stigmator(self):
        """ C2 condenser stigmator X and Y. (read/write)"""
        return (self._tem_illumination.CondenserStigmator.X,
                self._tem_illumination.CondenserStigmator.Y)

    @condenser_stigmator.setter
    def condenser_stigmator(self, value):
        Vector.set(self._tem_illumination, "CondenserStigmator", value, range=(-1.0, 1.0))

    @property
    def illuminated_area(self):
        """ Illuminated area. Works only on 3-condenser lens systems. (read/write)"""
        if self._tem.Configuration.CondenserLensSystem == CondenserLensSystem.THREE_CONDENSER_LENSES:
            return self._tem_illumination.IlluminatedArea
        else:
            raise NotImplementedError("Illuminated area exists only on 3-condenser lens systems.")

    @illuminated_area.setter
    def illuminated_area(self, value):
        if self._tem.Configuration.CondenserLensSystem == CondenserLensSystem.THREE_CONDENSER_LENSES:
            self._tem_illumination.IlluminatedArea = float(value)
        else:
            raise NotImplementedError("Illuminated area exists only on 3-condenser lens systems.")

    @property
    def probe_defocus(self):
        """ Probe defocus. Works only on 3-condenser lens systems. (read/write)"""
        if self._tem.Configuration.CondenserLensSystem == CondenserLensSystem.THREE_CONDENSER_LENSES:
            return self._tem_illumination.ProbeDefocus
        else:
            raise NotImplementedError("Probe defocus exists only on 3-condenser lens systems.")

    @probe_defocus.setter
    def probe_defocus(self, value):
        if self._tem.Configuration.CondenserLensSystem == CondenserLensSystem.THREE_CONDENSER_LENSES:
            self._tem_illumination.ProbeDefocus = float(value)
        else:
            raise NotImplementedError("Probe defocus exists only on 3-condenser lens systems.")

    @property
    def convergence_angle(self):
        """ Convergence angle. Works only on 3-condenser lens systems. (read/write)"""
        if self._tem.Configuration.CondenserLensSystem == CondenserLensSystem.THREE_CONDENSER_LENSES:
            return self._tem_illumination.ConvergenceAngle
        else:
            raise NotImplementedError("Convergence angle exists only on 3-condenser lens systems.")

    @convergence_angle.setter
    def convergence_angle(self, value):
        if self._tem.Configuration.CondenserLensSystem == CondenserLensSystem.THREE_CONDENSER_LENSES:
            self._tem_illumination.ConvergenceAngle = float(value)
        else:
            raise NotImplementedError("Convergence angle exists only on 3-condenser lens systems.")

    @property
    def C3ImageDistanceParallelOffset(self):
        """ C3 image distance parallel offset. Works only on 3-condenser lens systems. (read/write)"""
        if self._tem.Configuration.CondenserLensSystem == CondenserLensSystem.THREE_CONDENSER_LENSES:
            return self._tem_illumination.C3ImageDistanceParallelOffset
        else:
            raise NotImplementedError("C3ImageDistanceParallelOffset exists only on 3-condenser lens systems.")

    @C3ImageDistanceParallelOffset.setter
    def C3ImageDistanceParallelOffset(self, value):
        if self._tem.Configuration.CondenserLensSystem == CondenserLensSystem.THREE_CONDENSER_LENSES:
            self._tem_illumination.C3ImageDistanceParallelOffset = float(value)
        else:
            raise NotImplementedError("C3ImageDistanceParallelOffset exists only on 3-condenser lens systems.")

    @property
    def mode(self):
        """ Illumination mode: microprobe or nanoprobe. (read/write)"""
        return IlluminationMode(self._tem_illumination.Mode).name

    @mode.setter
    def mode(self, value):
        self._tem_illumination.Mode = value

    @property
    def dark_field(self):
        """ Dark field mode: cartesian, conical or off. (read/write)"""
        return DarkFieldMode(self._tem_illumination.DFMode).name

    @dark_field.setter
    def dark_field(self, value):
        self._tem_illumination.DFMode = value

    @property
    def condenser_mode(self):
        """ Mode of the illumination system: parallel or probe. (read/write)"""
        if self._tem.Configuration.CondenserLensSystem == CondenserLensSystem.THREE_CONDENSER_LENSES:
            return CondenserMode(self._tem_illumination.CondenserMode).name
        else:
            raise NotImplementedError("Condenser mode exists only on 3-condenser lens systems.")

    @condenser_mode.setter
    def condenser_mode(self, value):
        if self._tem.Configuration.CondenserLensSystem == CondenserLensSystem.THREE_CONDENSER_LENSES:
            self._tem_illumination.CondenserMode = value
        else:
            raise NotImplementedError("Condenser mode can be changed only on 3-condenser lens systems.")

    @property
    def beam_tilt(self):
        """ Dark field beam tilt relative to the origin stored at
        alignment time. Only operational if dark field mode is active.
        Units: mrad, either in Cartesian (x,y) or polar (conical)
        tilt angles. The accuracy of the beam tilt physical units
        depends on a calibration of the tilt angles. (read/write)
        """
        mode = self._tem_illumination.DFMode
        tilt = self._tem_illumination.Tilt
        if mode == DarkFieldMode.CONICAL:
            return tilt[0] * 1e3 * math.cos(tilt[1]), tilt[0] * 1e3 * math.sin(tilt[1])
        elif mode == DarkFieldMode.CARTESIAN:
            return tilt * 1e3
        else:
            return 0.0, 0.0  # Microscope might return nonsense if DFMode is OFF

    @beam_tilt.setter
    def beam_tilt(self, tilt):
        mode = self._tem_illumination.DFMode
        tilt[0] *= 1e-3
        tilt[1] *= 1e-3
        if tilt[0] == 0.0 and tilt[1] == 0.0:
            self._tem_illumination.Tilt = 0.0, 0.0
            self._tem_illumination.DFMode = DarkFieldMode.OFF
        elif mode == DarkFieldMode.CONICAL:
            self._tem_illumination.Tilt = math.sqrt(tilt[0] ** 2 + tilt[1] ** 2), math.atan2(tilt[1], tilt[0])
        elif mode == DarkFieldMode.OFF:
            self._tem_illumination.DFMode = DarkFieldMode.CARTESIAN
            self._tem_illumination.Tilt = tilt
        else:
            self._tem_illumination.Tilt = tilt


class Projection:
    """ Projection system functions. """
    def __init__(self, projection):
        self._tem_projection = projection
        #self.magnification_index = self._tem_projection.MagnificationIndex
        #self.camera_length_index = self._tem_projection.CameraLengthIndex

    @property
    def focus(self):
        """ Absolute focus value. (read/write)"""
        return self._tem_projection.Focus

    @focus.setter
    def focus(self, value):
        self._tem_projection.Focus = float(value)

    @property
    def magnification(self):
        """ The reference magnification value (screen up setting)."""
        return self._tem_projection.Magnification

    @property
    def camera_length(self):
        """ The reference camera length in m (screen up setting). """
        if self._tem_projection.Mode == ProjectionMode.DIFFRACTION:
            return self._tem_projection.CameraLength
        else:
            raise Exception("Microscope is not in diffraction mode.")

    @property
    def image_shift(self):
        """ Image shift in um. (read/write)"""
        return (self._tem_projection.ImageShift.X * 1e6,
                self._tem_projection.ImageShift.Y * 1e6)

    @image_shift.setter
    def image_shift(self, value):
        value[0] *= 1e-6
        value[1] *= 1e-6
        Vector.set(self._tem_projection, "ImageShift", value)

    @property
    def image_beam_shift(self):
        """ Image shift with beam shift compensation in um. (read/write)"""
        return (self._tem_projection.ImageBeamShift.X * 1e6,
                self._tem_projection.ImageBeamShift.Y * 1e6)

    @image_beam_shift.setter
    def image_beam_shift(self, value):
        value[0] *= 1e-6
        value[1] *= 1e-6
        Vector.set(self._tem_projection, "ImageBeamShift", value)

    @property
    def image_beam_tilt(self):
        """ Beam tilt with diffraction shift compensation in mrad. (read/write)"""
        return (self._tem_projection.ImageBeamTilt.X * 1e3,
                self._tem_projection.ImageBeamTilt.Y * 1e3)

    @image_beam_tilt.setter
    def image_beam_tilt(self, value):
        value[0] *= 1e-3
        value[1] *= 1e-3
        Vector.set(self._tem_projection, "ImageBeamTilt", value)

    @property
    def diffraction_shift(self):
        """ Diffraction shift in mrad. (read/write)"""
        return (self._tem_projection.DiffractionShift.X * 1e3,
                self._tem_projection.DiffractionShift.Y * 1e3)

    @diffraction_shift.setter
    def diffraction_shift(self, value):
        value[0] *= 1e-3
        value[1] *= 1e-3
        Vector.set(self._tem_projection, "DiffractionShift", value)

    @property
    def diffraction_stigmator(self):
        """ Diffraction stigmator. (read/write)"""
        return (self._tem_projection.DiffractionStigmator.X,
                self._tem_projection.DiffractionStigmator.Y)

    @diffraction_stigmator.setter
    def diffraction_stigmator(self, value):
        Vector.set(self._tem_projection, "DiffractionStigmator", value, range=(-1.0, 1.0))

    @property
    def objective_stigmator(self):
        """ Objective stigmator. (read/write)"""
        return (self._tem_projection.ObjectiveStigmator.X,
                self._tem_projection.ObjectiveStigmator.Y)

    @objective_stigmator.setter
    def objective_stigmator(self, value):
        Vector.set(self._tem_projection, "ObjectiveStigmator", value, range=(-1.0, 1.0))

    @property
    def defocus(self):
        """ Defocus value in um. (read/write)"""
        return self._tem_projection.Defocus * 1e6

    @defocus.setter
    def defocus(self, value):
        self._tem_projection.Defocus = float(value) * 1e-6

    @property
    def mode(self):
        """ Main mode of the projection system (either imaging or diffraction). (read/write)"""
        return ProjectionMode(self._tem_projection.Mode).name

    @mode.setter
    def mode(self, mode):
        self._tem_projection.Mode = mode

    @property
    def detector_shift(self):
        """ Detector shift. (read/write)"""
        return ProjectionDetectorShift(self._tem_projection.DetectorShift).name

    @detector_shift.setter
    def detector_shift(self, value):
        self._tem_projection.DetectorShift = value

    @property
    def detector_shift_mode(self):
        """ Detector shift mode. (read/write)"""
        return ProjDetectorShiftMode(self._tem_projection.DetectorShiftMode).name

    @detector_shift_mode.setter
    def detector_shift_mode(self, value):
        self._tem_projection.DetectorShiftMode = value

    @property
    def magnification_range(self):
        """ Submode of the projection system (either LM, M, SA, MH, LAD or D).
        The imaging submode can change when the magnification is changed.
        """
        return ProjectionSubMode(self._tem_projection.SubMode).name

    @property
    def image_rotation(self):
        """ The rotation of the image or diffraction pattern on the
        fluorescent screen with respect to the specimen. Units: mrad.
        """
        return self._tem_projection.ImageRotation * 1e3

    @property
    def is_eftem_on(self):
        """ Check if the EFTEM lens program setting is ON. """
        return LensProg(self._tem_projection.LensProgram) == LensProg.EFTEM

    def eftem_on(self):
        """ Switch on EFTEM. """
        self._tem_projection.LensProgram = LensProg.EFTEM

    def eftem_off(self):
        """ Switch off EFTEM. """
        self._tem_projection.LensProgram = LensProg.REGULAR

    def reset_defocus(self):
        """ Reset defocus value in the TEM user interface to zero.
        Does not change any lenses. """
        self._tem_projection.ResetDefocus()


class Apertures:
    """ Apertures and VPP controls. """
    def __init__(self, microscope):
        self._tem_vpp = microscope._tem_adv.PhasePlate
        self._tem_apertures = None

        try:
            self._tem_apertures = microscope._tem.ApertureMechanismCollection
        except:
            logging.info("Apertures interface is not available. Requires a separate license")

    def _find_aperture(self, name):
        """Find aperture object by name. """
        if self._tem_apertures is None:
            raise Exception("Apertures interface is not available. Requires a separate license")
        for ap in self._tem_apertures:
            if MechanismId(ap.Id).name == name.upper():
                return ap
        raise KeyError("No aperture with name %s" % name)

    @property
    def vpp_position(self):
        """ Returns the index of the current VPP preset position. """
        try:
            return self._tem_vpp.GetCurrentPresetPosition + 1
        except:
            raise Exception("Either no VPP found or it's not enabled and inserted.")

    def vpp_next_position(self):
        """ Goes to the next preset location on the VPP aperture. """
        try:
            self._tem_vpp.SelectNextPresetPosition()
        except:
            raise Exception("Either no VPP found or it's not enabled and inserted.")

    def enable(self, aperture):
        ap = self._find_aperture(aperture)
        ap.Enable()

    def disable(self, aperture):
        ap = self._find_aperture(aperture)
        ap.Disable()

    def retract(self, aperture):
        ap = self._find_aperture(aperture)
        if ap.IsRetractable:
            ap.Retract()

    def select(self, aperture, size):
        """ Select a specific aperture.

        :param aperture: Aperture name (C1, C2, C3, OBJ or SA)
        :type aperture: str
        :param size: Aperture size
        :type size: float
        """
        ap = self._find_aperture(aperture)
        if ap.State == MechanismState.DISABLED:
            ap.Enable()
        for a in ap.ApertureCollection:
            if a.Diameter == size:
                ap.SelectAperture(a)
                if ap.SelectedAperture.Diameter == size:
                    return
                else:
                    raise Exception("Could not select aperture!")

    @property
    def show_all(self):
        """ Returns a dict with apertures information. """
        if self._tem_apertures is None:
            raise Exception("Apertures interface is not available. Requires a separate license")
        result = {}
        for ap in self._tem_apertures:
            result[MechanismId(ap.Id).name] = {"retractable": ap.IsRetractable,
                                               "state": MechanismState(ap.State).name,
                                               "sizes": [a.Diameter for a in ap.ApertureCollection]
                                               }
        return result


class Gun:
    """ Gun functions. """
    def __init__(self, microscope):
        self._tem_gun = microscope._tem.Gun
        self._tem_gun1 = None
        self._tem_feg = None

        if hasattr(microscope._tem, "Gun1"):
            self._tem_gun1 = microscope._tem.Gun1
        else:
            logging.info("Gun1 interface is not available. Requires TEM Server 7.10+")

        try:
            self._tem_feg = microscope._tem_adv.Source
            _ = self._tem_feg.State
        except:
            logging.info("Source/FEG interface is not available.")

    @property
    def shift(self):
        """ Gun shift. (read/write)"""
        return (self._tem_gun.Shift.X, self._tem_gun.Shift.Y)

    @shift.setter
    def shift(self, value):
        Vector.set(self._tem_gun, "Shift", value, range=(-1.0, 1.0))

    @property
    def tilt(self):
        """ Gun tilt. (read/write)"""
        return (self._tem_gun.Tilt.X, self._tem_gun.Tilt.Y)

    @tilt.setter
    def tilt(self, value):
        Vector.set(self._tem_gun, "Tilt", value, range=(-1.0, 1.0))

    @property
    def voltage_offset(self):
        """ High voltage offset. (read/write)"""
        if self._tem_gun1 is None:
            raise Exception("Gun1 interface is not available.")
        return self._tem_gun1.HighVoltageOffset

    @voltage_offset.setter
    def voltage_offset(self, offset):
        if self._tem_gun1 is None:
            raise Exception("Gun1 interface is not available.")
        self._tem_gun1.HighVoltageOffset = offset

    @property
    def feg_state(self):
        """ FEG emitter status. """
        if self._tem_feg is None:
            raise Exception("Gun1 interface is not available.")
        return FegState(self._tem_feg.State).name

    @property
    def ht_state(self):
        """ High tension state: on, off or disabled.
        Disabling/enabling can only be done via the button on the
        system on/off-panel, not via script. When switching on
        the high tension, this function cannot check if and
        when the set value is actually reached. (read/write)
        """
        return HighTensionState(self._tem_gun.HTState).name

    @ht_state.setter
    def ht_state(self, value):
        self._tem_gun.State = value

    @property
    def voltage(self):
        """ The value of the HT setting as displayed in the TEM user
        interface. Units: kVolts. (read/write)
        """
        state = self._tem_gun.HTState
        if state == HighTensionState.ON:
            return self._tem_gun.HTValue * 1e-3
        else:
            return 0.0

    @voltage.setter
    def voltage(self, value):
        self._tem_gun.HTValue = float(value) * 1000

    @property
    def voltage_max(self):
        """ The maximum possible value of the HT on this microscope. Units: kVolts. """
        return self._tem_gun.HTMaxValue * 1e-3

    @property
    def voltage_offset_range(self):
        """ Returns the high voltage offset range. """
        if self._tem_gun1 is None:
            raise Exception("Gun1 interface is not available.")
        return self._tem_gun1.GetHighVoltageOffsetRange()

    @property
    def beam_current(self):
        """ Returns the beam current. """
        if self._tem_feg is None:
            raise Exception("Source/FEG interface is not available.")
        return self._tem_feg.BeamCurrent

    @property
    def extractor_voltage(self):
        """ Returns the extractor voltage. """
        if self._tem_feg is None:
            raise Exception("Source/FEG interface is not available.")
        return self._tem_feg.ExtractorVoltage

    @property
    def focus_index(self):
        """ Returns coarse and fine focus index. """
        if self._tem_feg is None:
            raise Exception("Source/FEG interface is not available.")
        focus_index = self._tem_feg.FocusIndex
        return (focus_index.Coarse, focus_index.Fine)

    def do_flashing(self, flash_type):
        """ Perform cold FEG flashing.

        :param flash_type: FEG flashing type (FegFlashingType enum)
        :type flash_type: IntEnum
        """
        if self._tem_feg is None:
            raise Exception("Source/FEG interface is not available.")
        if self._tem_feg.Flashing.IsFlashingAdvised(flash_type):
            self._tem_feg.Flashing.PerformFlashing(flash_type)
        else:
            raise Exception("Flashing type %s is not advised" % flash_type)


class LowDose:
    """ Low Dose functions. """
    def __init__(self, microscope):
        if microscope._lowdose is not None:
            self._tem_ld = microscope._lowdose
        else:
            logging.info("LowDose server is not available.")

    def _is_available(self):
        return self._tem_ld.LowDoseAvailable and self._tem_ld.IsInitialized

    @property
    def is_active(self):
        """ Check if the Low Dose is ON. """
        if self._is_available():
            return LDStatus(self._tem_ld.LowDoseActive) == LDStatus.IS_ON
        else:
            raise Exception("Low Dose is not available")

    @property
    def state(self):
        """ Low Dose state (LDState enum). (read/write) """
        if self._is_available() and self.is_active:
            return LDState(self._tem_ld.LowDoseState).name
        else:
            raise Exception("Low Dose is not available")

    @state.setter
    def state(self, state):
        if self._is_available():
            self._tem_ld.LowDoseState = state
        else:
            raise Exception("Low Dose is not available")

    def on(self):
        """ Switch ON Low Dose."""
        if self._is_available():
            self._tem_ld.LowDoseActive = LDStatus.IS_ON
        else:
            raise Exception("Low Dose is not available")

    def off(self):
        """ Switch OFF Low Dose."""
        if self._is_available():
            self._tem_ld.LowDoseActive = LDStatus.IS_OFF
        else:
            raise Exception("Low Dose is not available")


class Image(BaseImage):
    """ Acquired image object. """
    def __init__(self, obj, name=None, isAdvanced=False, **kwargs):
        super().__init__(obj, name, isAdvanced, **kwargs)

    def _get_metadata(self, obj):
        return {item.Key: item.ValueAsString for item in obj.Metadata}

    @property
    def width(self):
        """ Image width in pixels. """
        return self._img.Width

    @property
    def height(self):
        """ Image height in pixels. """
        return self._img.Height

    @property
    def bit_depth(self):
        """ Bit depth. """
        return self._img.BitDepth if self._isAdvanced else self._img.Depth

    @property
    def pixel_type(self):
        """ Image pixels type: uint, int or float. """
        if self._isAdvanced:
            return ImagePixelType(self._img.PixelType).name
        else:
            return ImagePixelType.SIGNED_INT.name

    @property
    def data(self):
        """ Returns actual image object as numpy int32 array. """
        from comtypes.safearray import safearray_as_ndarray
        with safearray_as_ndarray:
            data = self._img.AsSafeArray
        return data

    def save(self, filename, normalize=False):
        """ Save acquired image to a file.

        :param filename: File path
        :type filename: str
        :param normalize: Normalize image, only for non-MRC format
        :type normalize: bool
        """
        fmt = os.path.splitext(filename)[1].upper().replace(".", "")
        if fmt == "MRC":
            print("Convert to int16 since MRC does not support int32")
            import mrcfile
            with mrcfile.new(filename) as mrc:
                if self.metadata is not None:
                    mrc.voxel_size = float(self.metadata['PixelSize.Width']) * 1e10
                mrc.set_data(self.data.astype("int16"))
        else:
            # use scripting method to save in other formats
            if self._isAdvanced:
                self._img.SaveToFile(filename)
            else:
                try:
                    fmt = AcqImageFileFormat[fmt].value
                except KeyError:
                    raise NotImplementedError("Format %s is not supported" % fmt)
                self._img.AsFile(filename, fmt, normalize)