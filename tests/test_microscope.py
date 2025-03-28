import argparse
from typing import Optional, List
from time import sleep
import sys

if sys.version_info >= (3, 5):
    from math import isclose
else:
    def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

from pytemscript.microscope import Microscope
from pytemscript.utils.enums import *


def test_projection(microscope: Microscope,
                    has_eftem: bool = False) -> None:
    """ Test projection module attrs.
    :param microscope: Microscope object
    :param has_eftem: If true, test EFTEM mode
    """
    print("\nTesting projection...")
    projection = microscope.optics.projection
    print("\tMode:", projection.mode)
    print("\tFocus:", projection.focus)
    print("\tDefocus:", projection.defocus)

    projection.defocus = -3.0
    assert isclose(projection.defocus, -3.0, abs_tol=1e-5)
    projection.focus = 0.1
    assert isclose(projection.focus, 0.1, abs_tol=1e-5)
    projection.eucentric_focus()

    print("\tObjective:", projection.objective)
    print("\tMagnification:", projection.magnification)
    print("\tMagnificationIndex:", projection.magnification_index)
    projection.magnification_index += 1
    projection.magnification_index -= 1

    projection.mode = ProjectionMode.DIFFRACTION
    print("\tCameraLength:", projection.camera_length)
    print("\tCameraLengthIndex:", projection.camera_length_index)
    projection.camera_length_index += 1
    projection.camera_length_index -= 1

    print("\tDiffractionShift:", projection.diffraction_shift)
    projection.diffraction_shift += (-0.02, 0.02)
    projection.diffraction_shift -= (-0.02, 0.02)

    print("\tDiffractionStigmator:", projection.diffraction_stigmator)
    projection.diffraction_stigmator += (-0.02, 0.02)
    projection.diffraction_stigmator -= (-0.02, 0.02)
    projection.mode = ProjectionMode.IMAGING

    print("\tImageShift:", projection.image_shift)
    projection.image_shift = (0,0)

    print("\tImageBeamShift:", projection.image_beam_shift)
    projection.image_beam_shift = [0,0]
    print("\tObjectiveStigmator:", projection.objective_stigmator)
    projection.objective_stigmator += (-0.02, 0.02)
    projection.objective_stigmator -= (-0.02, 0.02)

    print("\tSubMode:", projection.magnification_range)
    print("\tLensProgram:", projection.is_eftem_on)
    print("\tImageRotation:", projection.image_rotation)
    print("\tDetectorShift:", projection.detector_shift)
    print("\tDetectorShiftMode:", projection.detector_shift_mode)

    beam_tilt = projection.image_beam_tilt
    print("\tImageBeamTilt:", beam_tilt)
    projection.image_beam_tilt = [-0.02, 0.03]
    projection.image_beam_tilt = beam_tilt

    print("\tIsEftemOn:", projection.is_eftem_on)

    projection.reset_defocus()  # TODO: not working remotely?

    if has_eftem:
        print("\tToggling EFTEM mode...")
        projection.eftem_on()
        projection.eftem_off()


def test_acquisition(microscope: Microscope) -> None:
    """ Acquire test image on each camera.
    :param microscope: Microscope object
    """
    print("\nTesting acquisition...")
    acquisition = microscope.acquisition
    cameras = acquisition.cameras
    stem = microscope.stem

    print("\tFilm settings:", acquisition.film_settings)
    print("\tCameras:", cameras)
    acquisition.screen_position = ScreenPosition.UP

    for cam_name in cameras:
        image = acquisition.acquire_tem_image(cam_name,
                                              size=AcqImageSize.FULL,
                                              exp_time=0.25,
                                              binning=2)
        if image is not None:
            print("Metadata: ", image.metadata)
            image.save(fn="test_image_%s.mrc" % cam_name, overwrite=True)

    if stem.is_available:
        stem.enable()
        detectors = acquisition.stem_detectors
        print("\tSTEM detectors:", detectors)

        for det in detectors:
            image = acquisition.acquire_stem_image(det,
                                                   size=AcqImageSize.FULL,
                                                   dwell_time=1e-5,
                                                   binning=2)
            if image is not None:
                print("Metadata: ", image.metadata)
                image.save(fn="test_image_%s.mrc" % det, overwrite=True)

        stem.disable()


def test_vacuum(microscope: Microscope,
                buffer_cycle: bool = False) -> None:
    """ Test vacuum module attrs.
    :param microscope: Microscope object
    :param buffer_cycle: If true, toggle column valves and run buffer cycle
    """
    print("\nTesting vacuum...")
    vacuum = microscope.vacuum
    print("\tStatus:", vacuum.status)
    print("\tPVPRunning:", vacuum.is_buffer_running)
    print("\tColumnValvesOpen:", vacuum.is_column_open)
    print("\tGauges:", vacuum.gauges)

    if buffer_cycle:
        print("\tToggling col.valves...")
        vacuum.column_open()
        assert vacuum.is_column_open is True
        vacuum.column_close()
        print("\tRunning buffer cycle...")
        vacuum.run_buffer_cycle()


def test_temperature(microscope: Microscope,
                     force_refill: bool = False) -> None:
    """ Test temperature module attrs.
    :param microscope: Microscope object
    :param force_refill: If true, force refill dewars
    """
    temp = microscope.temperature
    if temp.is_available:
        print("\nTesting TemperatureControl...")
        print("\tRefrigerantLevel (autoloader):",
              temp.dewar_level(RefrigerantDewar.AUTOLOADER_DEWAR))
        print("\tRefrigerantLevel (column):",
              temp.dewar_level(RefrigerantDewar.COLUMN_DEWAR))
        print("\tDewarsRemainingTime:", temp.dewars_time)
        print("\tDewarsAreBusyFilling:", temp.is_dewar_filling)

        if force_refill:
            print("\tRunning force LN refill...")
            try:
                temp.force_refill()
            except Exception as e:
                print(str(e))

        if microscope.family == ProductFamily.TITAN.name:
            print("\tDocker temperature:", temp.temp_docker)
            print("\tCassette temperature:", temp.temp_cassette)
            print("\tCartridge temperature:", temp.temp_cartridge)
            print("\tHolder temperature:", temp.temp_holder)


def test_autoloader(microscope: Microscope,
                    check_loading: bool = False,
                    slot: int = 1) -> None:
    """ Test autoloader module attrs.
    :param microscope: Microscope object
    :param check_loading: If true, test cartridge loading
    :param slot: slot number
    """
    al = microscope.autoloader
    if al.is_available:
        print("\nTesting Autoloader...")
        print("\tNumberOfCassetteSlots", al.number_of_slots)
        print("\tSlotStatus for #%d: %s" % (slot, al.slot_status(slot)))

        if check_loading:
            try:
                print("\tRunning inventory and trying to load cartridge #%d..." % slot)
                al.initialize()
                al.buffer_cycle()
                #al.undock_cassette()
                #al.dock_cassette()
                al.run_inventory()
                if al.slot_status(slot) == CassetteSlotStatus.OCCUPIED.name:
                    al.load_cartridge(slot)
                    assert al.slot_status(slot) == CassetteSlotStatus.EMPTY.name
                    al.unload_cartridge()
            except Exception as e:
                print(str(e))


def test_stage(microscope: Microscope) -> None:
    """ Test stage module attrs.
    :param microscope: Microscope object
    """
    stage = microscope.stage
    print("\nTesting stage...")
    pos = stage.position
    print("\tStatus:", stage.status)
    print("\tPosition:", pos)
    print("\tHolder:", stage.holder)
    print("\tLimits:", stage.limits)

    print("Testing stage movement...")
    print("\tGoto(x=1, y=-1)")
    stage.go_to(x=+1, y=-1, relative=True)
    sleep(1)
    print("\tPosition:", stage.position)
    print("\tGoto(x=-1, speed=0.25)")
    stage.go_to(x=-1, speed=0.25)
    sleep(1)
    print("\tPosition:", stage.position)
    print("\tMoveTo() to original position")
    stage.move_to(**pos)
    print("\tPosition:", stage.position)


def test_optics(microscope: Microscope) -> None:
    """ Test optics module attrs.
    :param microscope: Microscope object
    """
    print("\nTesting optics...")
    opt = microscope.optics
    print("\tInstrumentMode:", opt.instrument_mode)
    print("\tScreenCurrent:", opt.screen_current)
    print("\tBeamBlanked:", opt.is_beam_blanked)
    print("\tAutoNormalizeEnabled:", opt.is_autonormalize_on)
    print("\tShutterOverrideOn:", opt.is_shutter_override_on)
    opt.beam_blank()
    opt.beam_unblank()
    opt.normalize(ProjectionNormalization.OBJECTIVE)
    opt.normalize_all()


def test_illumination(microscope: Microscope) -> None:
    """ Test illumination module attrs.
    :param microscope: Microscope object
    """
    print("\nTesting illumination...")
    illum = microscope.optics.illumination
    print("\tMode:", illum.mode)
    illum.mode = IlluminationMode.NANOPROBE
    print("\tSpotsizeIndex:", illum.spotsize)

    illum.spotsize += 1
    illum.spotsize -= 1

    if microscope.condenser_system == CondenserLensSystem.TWO_CONDENSER_LENSES.name:
        print("\tIntensity:", illum.intensity)

        orig_int = illum.intensity
        illum.intensity = 0.44
        assert isclose(illum.intensity, 0.44, abs_tol=1e-5)
        illum.intensity = orig_int

        print("\tIntensityZoomEnabled:", illum.intensity_zoom)
        illum.intensity_zoom = False
        print("\tIntensityLimitEnabled:", illum.intensity_limit)
        illum.intensity_limit = False

    elif microscope.condenser_system == CondenserLensSystem.THREE_CONDENSER_LENSES.name:
        print("\tCondenserMode:", illum.condenser_mode)
        print("\tIntensityZoomEnabled:", illum.intensity_zoom)
        illum.intensity_zoom = False
        print("\tIlluminatedArea:", illum.illuminated_area)

        illum.condenser_mode = CondenserMode.PROBE
        print("\tProbeDefocus:", illum.probe_defocus)
        print("\tConvergenceAngle:", illum.convergence_angle)

        illum.condenser_mode = CondenserMode.PARALLEL
        print("\tC3ImageDistanceParallelOffset:", illum.C3ImageDistanceParallelOffset)
        illum.C3ImageDistanceParallelOffset += 0.01
        illum.C3ImageDistanceParallelOffset -= 0.01

        orig_illum = illum.illuminated_area
        illum.illuminated_area = 1.0
        assert isclose(illum.illuminated_area, 1.0, abs_tol=1e-5)
        illum.illuminated_area = orig_illum

    print("\tShift:", illum.beam_shift)

    illum.beam_shift = (0.5, 0.5)
    illum.beam_shift = [0, 0]

    print("\tCondenserStigmator:", illum.condenser_stigmator)
    print("\tRotationCenter:", illum.rotation_center)
    illum.rotation_center += (0.1, 0.2)
    illum.rotation_center -= (0.1, 0.2)

    if microscope.family != ProductFamily.TECNAI.name:
        print("\tTilt:", illum.beam_tilt)
        print("\tDFMode:", illum.dark_field)
        illum.dark_field = DarkFieldMode.CARTESIAN
        print("\tTilt (cartesian):", illum.beam_tilt)
        illum.dark_field = DarkFieldMode.CONICAL
        print("\tTilt (conical):", illum.beam_tilt)
        illum.dark_field = DarkFieldMode.OFF


def test_stem(microscope: Microscope) -> None:
    """ Test STEM module attrs.
    :param microscope: Microscope object
    """
    print("\nTesting STEM...")
    stem = microscope.stem
    print("\tStemAvailable:", stem.is_available)

    if stem.is_available:
        stem.enable()
        print("\tIllumination.StemMagnification:", stem.magnification)
        stem.magnification = 28000
        print("\tIllumination.StemRotation:", stem.rotation)
        stem.rotation = -89.0
        print("\tIllumination.StemFullScanFieldOfView:", stem.scan_field_of_view)
        stem.disable()


def test_gun(microscope: Microscope,
             has_cfeg: bool = False) -> None:
    """ Test gun module attrs.
    :param microscope: Microscope object
    :param has_cfeg: If true, test C-FEG interface
    """
    print("\nTesting gun...")
    gun = microscope.gun
    print("\tHTValue:", gun.voltage)
    print("\tHTMaxValue:", gun.voltage_max)
    print("\tShift:", gun.shift)
    gun.shift += (0.01, 0.02)
    gun.shift -= (0.01, 0.02)

    print("\tTilt:", gun.tilt)
    gun.tilt += (0.01, 0.02)
    gun.tilt -= (0.01, 0.02)

    try:
        print("\tHVOffset:", gun.voltage_offset)
        gun.voltage_offset += 0.1
        gun.voltage_offset -= 0.1
        print("\tHVOffsetRange:", gun.voltage_offset_range)
    except NotImplementedError:
        pass

    if has_cfeg:
        print("\tFegState:", gun.feg_state)
        print("\tHTState:", gun.ht_state)
        print("\tBeamCurrent:", gun.beam_current)
        print("\tGunLens:", gun.gun_lens)

        try:
            gun.is_flashing_advised(FegFlashingType.HIGH_T)
            gun.do_flashing(FegFlashingType.LOW_T)
            gun.do_flashing(FegFlashingType.HIGH_T)
        except Warning:
            pass


def test_apertures(microscope: Microscope,
                   has_license: bool = False) -> None:
    """ Test aperture module attrs.
    :param microscope: Microscope object
    :param has_license: If true, test apertures, otherwise test only VPP
    """
    print("\nTesting apertures...")
    aps = microscope.apertures

    try:
        print("\tGetCurrentPresetPosition", aps.vpp_position)
        aps.vpp_next_position()
    except Exception as e:
        print(str(e))

    if has_license:
        aps.show()
        aps.enable(MechanismId.C2)
        aps.select(MechanismId.C2, 50)
        aps.retract(MechanismId.OBJ)


def test_energy_filter(microscope: Microscope) -> None:
    """ Test energy filter module attrs.
    :param microscope: Microscope object
    """
    if hasattr(microscope, "energy_filter"):
        try:
            print("\nTesting energy filter...")
            ef = microscope.energy_filter

            print("\tZLPShift: ", ef.zlp_shift)
            ef.zlp_shift += 10
            ef.zlp_shift -= 10

            print("\tHTShift: ", ef.ht_shift)
            ef.ht_shift += 10
            ef.ht_shift -= 10

            ef.insert_slit(10)
            print("\tSlit width: ", ef.slit_width)
            ef.slit_width = 20
            ef.retract_slit()
        except:
            pass


def test_lowdose(microscope: Microscope) -> None:
    """ Test LowDose module attrs.
    :param microscope: Microscope object
    """
    if hasattr(microscope, "low_dose") and microscope.low_dose.is_available:
        print("\nTesting Low Dose...")
        ld = microscope.low_dose
        print("\tLowDose state: ", ld.state)
        ld.on()
        ld.off()


def test_general(microscope: Microscope,
                 check_door: bool = False) -> None:
    """ Test general attrs.
    :param microscope: Microscope object
    :param check_door: If true, check the door
    """
    print("\nTesting configuration...")
    print("\tConfiguration.ProductFamily:", microscope.family)
    print("\tCondenser system:", microscope.condenser_system)

    if microscope.family == ProductFamily.TITAN.name:
        assert microscope.condenser_system == CondenserLensSystem.THREE_CONDENSER_LENSES.name
    else:
        assert microscope.condenser_system == CondenserLensSystem.TWO_CONDENSER_LENSES.name

    if check_door and hasattr(microscope, "user_door"):
        print("\tUser door:", microscope.user_door.state)
        microscope.user_door.open()
        microscope.user_door.close()


def main(argv: Optional[List] = None) -> None:
    """ Test all aspects of the microscope interface. """
    parser = argparse.ArgumentParser(
        description="This test can use local or remote client. If using socket client, "
                    "pytemscript-server must be already running",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-t", "--type", type=str,
                        choices=["direct", "socket", "utapi"],
                        default="direct",
                        help="Connection type: direct, socket or utapi")
    parser.add_argument("-p", "--port", type=int, default=39000,
                        help="Specify port on which the server is listening")
    parser.add_argument("--host", type=str, default='127.0.0.1',
                        help="Specify host address on which the server is listening")
    parser.add_argument("-d", "--debug", dest="debug",
                        default=False, action='store_true',
                        help="Enable debug mode")
    args = parser.parse_args(argv)

    microscope = Microscope(connection=args.type, host=args.host,
                            port=args.port, debug=args.debug)

    print("Starting microscope tests, connection: %s" % args.type)

    test_projection(microscope, has_eftem=False)
    test_vacuum(microscope, buffer_cycle=False)
    test_autoloader(microscope, check_loading=False, slot=1)
    test_temperature(microscope, force_refill=False)
    test_stage(microscope)
    test_optics(microscope)
    test_illumination(microscope)
    test_gun(microscope, has_cfeg=False)
    test_acquisition(microscope)
    test_stem(microscope)
    test_apertures(microscope, has_license=False)
    test_energy_filter(microscope)
    test_lowdose(microscope)
    test_general(microscope, check_door=False)

    microscope.disconnect()


if __name__ == '__main__':
    main()


"""
Notes for Tecnai F20:
- DF element not found -> no DF mode or beam tilt. Python 32-bit issue?
- Userbuttons not found
"""
