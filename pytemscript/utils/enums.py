from enum import IntEnum


class TEMScriptingError(IntEnum):
    """ Scripting error codes. """
    E_NOT_OK = -2147155969              # 0x8004ffff
    E_VALUE_CLIP = -2147155970          # 0x8004fffe
    E_OUT_OF_RANGE = -2147155971        # 0x8004fffd
    E_NOT_IMPLEMENTED = -2147155972     # 0x8004fffc
    # The following are also mentioned in the manual
    E_UNEXPECTED = -2147418113          # 0x8000FFFF
    E_NOTIMPL = -2147467263             # 0x80004001
    E_INVALIDARG = -2147024809          # 0x80070057
    E_ABORT = -2147467260               # 0x80004004
    E_FAIL = -2147467259                # 0x80004005
    E_ACCESSDENIED = -2147024891        # 0x80070005


class VacuumStatus(IntEnum):
    """ Vacuum system status. """
    UNKNOWN = 1
    OFF = 2
    CAMERA_AIR = 3
    BUSY = 4
    READY = 5
    ELSE = 6


class GaugeStatus(IntEnum):
    """Vacuum gauge status. """
    UNDEFINED = 0
    UNDERFLOW = 1
    OVERFLOW = 2
    INVALID = 3
    VALID = 4


class GaugePressureLevel(IntEnum):
    """ Vacuum gauge pressure level. """
    UNDEFINED = 0
    LOW = 1
    LOW_MEDIUM = 2
    MEDIUM_HIGH = 3
    HIGH = 4


class StageStatus(IntEnum):
    """ Stage status. """
    READY = 0
    DISABLED = 1
    NOT_READY = 2
    GOING = 3
    MOVING = 4
    WOBBLING = 5


class MeasurementUnitType(IntEnum):
    """ Stage measurement units. """
    UNKNOWN = 0
    METERS = 1
    RADIANS = 2


class StageHolderType(IntEnum):
    """ Specimen holder type. """
    NONE = 0
    SINGLE_TILT = 1
    DOUBLE_TILT = 2
    INVALD = 4
    POLARA = 5
    DUAL_AXIS = 6
    ROTATION_AXIS = 7


class StageAxes(IntEnum):
    """ Stage axes. """
    NONE = 0
    X = 1
    Y = 2
    XY = 3
    Z = 4
    A = 8
    B = 16


class IlluminationNormalization(IntEnum):
    """ Normalization modes for condenser / objective lenses. """
    SPOTSIZE = 1 # C1
    INTENSITY = 2 # C2+C3
    CONDENSER = 3 # C1+C2+C3
    MINI_CONDENSER = 4
    OBJECTIVE = 5 # minicondenser + objective
    ALL = 6


class IlluminationMode(IntEnum):
    """ Illumination mode: nanoprobe or microprobe. """
    NANOPROBE = 0
    MICROPROBE = 1


class DarkFieldMode(IntEnum):
    """ Dark field mode. """
    OFF = 1
    CARTESIAN = 2
    CONICAL = 3


class CondenserMode(IntEnum):
    """ Condenser mode: parallel or probe. """
    PARALLEL = 0
    PROBE = 1


class ProjectionNormalization(IntEnum):
    """ Normalization modes for objective/projector lenses. """
    OBJECTIVE = 10
    PROJECTOR = 11 # Diffraction + Intermediate + P1 + P2
    ALL = 12


class ProjectionMode(IntEnum):
    """ Imaging or diffraction. """
    IMAGING = 1
    DIFFRACTION = 2


class ProjectionSubMode(IntEnum):
    """ Magnification range mode. """
    LM = 1
    M = 2
    SA = 3
    MH = 4
    LAD = 5
    D = 6


class LensProg(IntEnum):
    """ TEM or EFTEM mode. """
    REGULAR = 1
    EFTEM = 2


class ProjectionDetectorShift(IntEnum):
    """ Sets the extra shift that projects the image/diffraction
    pattern onto a detector. """
    ON_AXIS = 0
    NEAR_AXIS = 1
    OFF_AXIS = 2


class ProjDetectorShiftMode(IntEnum):
    """ This property determines whether the chosen DetectorShift
    is changed when the fluorescent screen is moved down. """
    AUTO_IGNORE = 1
    MANUAL = 2
    ALIGNMENT = 3


class HighTensionState(IntEnum):
    """ High Tension status. """
    DISABLED = 1
    OFF = 2
    ON = 3


class InstrumentMode(IntEnum):
    """ TEM or STEM mode. """
    TEM = 0
    STEM = 1


class AcqShutterMode(IntEnum):
    """ Shutter mode. """
    PRE_SPECIMEN = 0
    POST_SPECIMEN = 1
    BOTH = 2


class AcqImageSize(IntEnum):
    """ Image size. """
    FULL = 0
    HALF = 1
    QUARTER = 2


class AcqImageCorrection(IntEnum):
    """ Image correction: unprocessed or corrected (gain/bias). """
    UNPROCESSED = 0
    DEFAULT = 1


class AcqExposureMode(IntEnum):
    """ Exposure mode. """
    NONE = 0
    SIMULTANEOUS = 1
    PRE_EXPOSURE = 2
    PRE_EXPOSURE_PAUSE = 3


class AcqImageFileFormat(IntEnum):
    """ Image file format. """
    TIFF = 0
    JPG = 1
    PNG = 2
    RAW = 3
    SER = 4
    MRC = 5


class ProductFamily(IntEnum):
    """ Microscope product family. """
    TECNAI = 0
    TITAN = 1
    TALOS = 2


class CondenserLensSystem(IntEnum):
    """ Two or three-condenser lens system. """
    TWO_CONDENSER_LENSES = 0
    THREE_CONDENSER_LENSES = 1


class ScreenPosition(IntEnum):
    """ Fluscreen position. """
    UNKNOWN = 1
    UP = 2
    DOWN = 3


class PlateLabelDateFormat(IntEnum):
    """ Date format for film. """
    NO_DATE = 0
    DDMMYY = 1
    MMDDYY = 2
    YYMMDD = 3


class RefrigerantDewar(IntEnum):
    """ Nitrogen dewar. """
    AUTOLOADER_DEWAR = 0
    COLUMN_DEWAR = 1
    HELIUM_DEWAR = 2


class CassetteSlotStatus(IntEnum):
    """ Cassette slot status. """
    UNKNOWN = 0
    OCCUPIED = 1
    EMPTY = 2
    ERROR = 3


class ImagePixelType(IntEnum):
    """ Image type: uint, int or float. """
    UNSIGNED_INT = 0
    SIGNED_INT = 1
    FLOAT = 2


class MechanismId(IntEnum):
    """ Aperture name. """
    UNKNOWN = 0
    C1 = 1
    C2 = 2
    C3 = 3
    OBJ = 4
    SA = 5


class MechanismState(IntEnum):
    """ Aperture state. """
    DISABLED = 0
    INSERTED = 1
    MOVING = 2
    RETRACTED = 3
    ARBITRARY = 4
    HOMING = 5
    ALIGNING = 6
    ERROR = 7


class ApertureType(IntEnum):
    """ Aperture type. """
    UNKNOWN = 0
    CIRCULAR = 1
    BIPRISM = 2
    ENERGY_SLIT = 3
    FARADAY_CUP = 4


class HatchState(IntEnum):
    """ User door hatch state. """
    UNKNOWN = 0
    OPEN = 1
    OPENING = 2
    CLOSED = 3
    CLOSING = 4


class FegState(IntEnum):
    """ FEG state. """
    NOT_EMITTING = 0
    EMITTING = 1


class FegFlashingType(IntEnum):
    """ Cold FEG flashing type. """
    LOW_T = 0
    HIGH_T = 1

# ---------------- Low Dose enums ---------------------------------------------
class LDStatus(IntEnum):
    """ Low Dose status: on or off. """
    IS_OFF = 0
    IS_ON = 1


class LDState(IntEnum):
    """ Low Dose state. """
    SEARCH = 0
    FOCUS1 = 1
    FOCUS2 = 2
    EXPOSURE = 3

# ---------------- FEI Tecnai CCD enums ---------------------------------------
class AcqSpeed(IntEnum):
    """ CCD acquisition mode for TecnaiCCD plugin. """
    TURBO = 0
    CONTINUOUS = 1
    SINGLEFRAME = 2


class AcqMode(IntEnum):
    """ CCD acquisition preset for TecnaiCCD plugin."""
    SEARCH = 0
    FOCUS = 1
    RECORD = 2

# ----------------- CalGetter enums -------------------------------------------
class CalibrationStatus(IntEnum):
    """ Calgetter calibratino status. """
    NOT_CALIBRATED = 0
    INVALID_CALIBRATION = 1
    CALIBRATED = 2


class CalibrationTypes(IntEnum):
    """ Calgetter calibration types. """
    MAGNIFICATION = 1
    BEAM_SHIFT = 2
    BEAM_TILT = 3
    IMAGE_SHIFT = 4
    DIFFRACTION_SHIFT = 5
    STAGE_SHIFT = 6
    FOCUS_STIGMATOR = 7
    ILLUMINATED_AREA = 8
    COUNT_TO_ELECTRONS = 9
    STAGE_TILT = 10
    FULL_STAGEX_LINEARIZATION = 11
    STEM_CALIBRATION = 12
    STEM_FOCUS_CALIBRATION = 13
    BEAM_TILT_AZIMUTH = 14
    STEM_HARDWARE_CORRECTION = 15


class ModeTypes(IntEnum):
    """ Illumination mode used by Calgetter. """
    LM = 1
    MICROPROBE = 2
    NANOPROBE = 3
    LAD = 4
    MICROPROBE_D = 5
    NANOPROBE_D = 6
    LM_STEM = 7
    MICROPROBE_STEM = 8
    NANOPROBE_STEM = 9


class LensSeriesTypes(IntEnum):
    """ Projection mode used by Calgetter: normal (zoom) or EFTEM. """
    ZOOM = 1
    EFTEM = 2


class LorentzTypes(IntEnum):
    """ Lorentz lens status used by Calgetter. """
    OFF = 1
    ON = 2


class ActualMagnificationElements(IntEnum):
    """ Details of calibrated magnification from Calgetter. """
    NOMINAL_MAGNIFICATION = 0
    CALIBRATED_MAGNIFICATION = 1
    MAGNIFICATION_INDEX = 2
    MAGNIFICATION_MODE = 3
    MAGNIFICATION_ROTATION = 4
    CERTIFIED = 5
    YEAR = 6
    MONTH = 7
    DAY = 8
    HOUR = 9
    MINUTE = 10
    SECOND = 11
    TOOLMATCH = 12
    BASE_MAGNIFICATION = 13


class TransformTypes(IntEnum):
    """ Calgetter transform types. """
    BEAM_SHIFT_LOG = 0
    BEAM_SHIFT_PHYS = 1
    BEAM_TILT_LOG = 2
    BEAM_TILT_PHYS = 3
    IMAGE_SHIFT_LOG = 4
    IMAGE_SHIFT_PHYS = 5
    DIFFRACTION_SHIFT_LOG = 6
    DIFFRACTION_SHIFT_PHYS = 7
    STAGE = 8
    STAGE_AS_SHIFT = 9
    STAGE_AS_TILT = 10


class BasicTransformTypes(IntEnum):
    """ Calgetter transforms from one coordinate system to another. """
    PIXEL_TO_BEAMSHIFT = 0
    BEAMSHIFT_TO_PIXEL = 1
    BEAMSHIFT_LOG_TO_PHYS = 2
    BEAMSHIFT_PHYS_TO_LOG = 3
    PIXEL_TO_BEAMTILT = 4
    BEAMTILT_TO_PIXEL = 5
    BEAMTILT_LOG_TO_PHYS = 6
    BEAMTILT_PHYS_TO_LOG = 7
    PIXEL_TO_IMAGESHIFT = 8
    IMAGESHIFT_TO_PIXEL = 9
    IMAGESHIFT_LOG_TO_PHYS = 10
    IMAGESHIFT_PHYS_TO_LOG = 11
    PIXEL_TO_STAGESHIFT = 12
    STAGESHIFT_TO_PIXEL = 13
    IMAGESHIFT_TO_STAGESHIFT = 14
    STAGESHIFT_TO_IMAGESHIFT = 15
    PIXEL_TO_DIFFRACTIONSHIFT = 16
    DIFFRACTIONSHIFT_TO_PIXEL = 17
    DIFFRACTIONSHIFT_LOG_TO_PHYS = 18
    DIFFRACTIONSHIFT_PHYS_TO_LOG = 19
    BEAMSHIFT_TO_STAGESHIFT = 20
    STAGESHIFT_TO_BEAMSHIFT = 21
    PIXEL_TO_STAGETILT = 22
    STAGETILT_TO_PIXEL = 23
    BEAMTILT_TO_STAGETILT = 24
    STAGETILT_TO_BEAMTILT = 25
    DIFFRACTIONSHIFT_TO_STAGETILT = 26
    STAGETILT_TO_DIFFRACTIONSHIFT = 27
    PHYSICALPIXEL_TO_BEAMSHIFT = 28
    BEAMSHIFT_TO_PHYSICALPIXEL = 29
    PHYSICALPIXEL_TO_BEAMTILT = 30
    BEAMTILT_TO_PHYSICALPIXEL = 31
    PHYSICALPIXEL_TO_IMAGESHIFT = 32
    IMAGESHIFT_TO_PHYSICALPIXEL = 33
    PHYSICALPIXEL_TO_STAGESHIFT = 34
    STAGESHIFT_TO_PHYSICALPIXEL = 35
    PHYSICALPIXEL_TO_DIFFRACTIONSHIFT = 36
    DIFFRACTIONSHIFT_TO_PHYSICALPIXEL = 37
    PHYSICALPIXEL_TO_STAGETILT = 38
    STAGETILT_TO_PHYSICALPIXEL = 39
    BEAMSHIFT_TO_IMAGESHIFT = 40
    IMAGESHIFT_TO_BEAMSHIFT = 41
    BEAMTILT_TO_DIFFRACTIONSHIFT = 42
    DIFFRACTIONSHIFT_TO_BEAMTILT = 43
    CONDENSERSTIGMATOR_TO_PHYSICAL = 44
    PHYSICAL_TO_CONDENSERSTIGMATOR = 45
    OBJECTIVESTIGMATOR_TO_PHYSICAL = 46
    PHYSICAL_TO_OBJECTIVESTIGMATOR = 47
    DIFFRACTIONSTIGMATOR_TO_PHYSICAL = 48
    PHYSICAL_TO_DIFFRACTIONSTIGMATOR = 49
    PIXEL_TO_ALIGNBEAMSHIFT = 50
    ALIGNBEAMSHIFT_TO_PIXEL = 51
    ALIGNBEAMSHIFT_LOG_TOPHYS = 52
    ALIGNBEAMSHIFT_PHYS_TO_LOG = 53
    ALIGNBEAMSHIFT_TO_STAGESHIFT = 54
    STAGESHIFT_TO_ALIGNBEAMSHIFT = 55
    PHYSICALPIXEL_TO_ALIGNBEAMSHIFT = 56
    ALIGNBEAMSHIFT_TO_PHYSICALPIXEL = 57
    ALIGNBEAMSHIFT_TO_IMAGESHIFT = 58
    IMAGESHIFT_TO_ALIGNBEAMSHIFT = 59
