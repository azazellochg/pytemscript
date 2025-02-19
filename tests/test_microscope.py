import argparse
from typing import Optional, List
from time import sleep

from pytemscript.microscope import Microscope
from pytemscript.modules import Vector
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

    orig_def = projection.defocus
    projection.defocus = -3.0
    assert projection.defocus == -3.0
    projection.defocus = orig_def

    print("\tMagnification:", projection.magnification)
    print("\tMagnificationIndex:", projection.magnification_index)

    # set first SA mag
    for key, value in projection.list_magnifications.items():
        if value[1] == ProjectionSubMode.SA.name:
            projection.magnification = key
            break

    projection.mode = ProjectionMode.DIFFRACTION
    print("\tCameraLength:", projection.camera_length)
    print("\tCameraLengthIndex:", projection.camera_length_index)
    print("\tDiffractionShift:", projection.diffraction_shift)
    print("\tDiffractionStigmator:", projection.diffraction_stigmator)
    projection.mode = ProjectionMode.IMAGING

    print("\tImageShift:", projection.image_shift)
    projection.image_shift = Vector(-0,0)

    print("\tImageBeamShift:", projection.image_beam_shift)
    print("\tObjectiveStigmator:", projection.objective_stigmator)
    print("\tSubMode:", projection.magnification_range)
    print("\tLensProgram:", projection.is_eftem_on)
    print("\tImageRotation:", projection.image_rotation)
    print("\tDetectorShift:", projection.detector_shift)
    print("\tDetectorShiftMode:", projection.detector_shift_mode)
    print("\tImageBeamTilt:", projection.image_beam_tilt)
    print("\tLensProgram:", projection.is_eftem_on)

    projection.reset_defocus()  # TODO: not working remotely? check _exec!

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
    cameras = microscope.detectors.cameras
    detectors = microscope.detectors.stem_detectors
    stem = microscope.stem

    for cam_name in cameras:
        image = acquisition.acquire_tem_image(cam_name,
                                              size=AcqImageSize.FULL,
                                              exp_time=0.25,
                                              binning=2)
        if image is not None:
            print("\tImage name:", image.name)
            print("\tImage size:", image.width, image.height)
            print("\tBit depth:", image.bit_depth)

            if image.metadata is not None:
                print("\tBinning:", image.metadata['Binning.Width'])
                print("\tExp time:", image.metadata['ExposureTime'])
                print("\tTimestamp:", image.metadata['TimeStamp'])

            fn = cam_name + ".mrc"
            print("Saving to ", fn)
            image.save(filename=fn, normalize=False, overwrite=True)

    if stem.is_available:
        stem.enable()
        for det in detectors:
            image = acquisition.acquire_stem_image(det,
                                                   size=AcqImageSize.FULL,
                                                   dwell_time=1e-5,
                                                   binning=2)
            if image is not None:
                fn = det + ".mrc"
                print("Saving to ", fn)
                image.save(filename=fn, normalize=False, overwrite=True)
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
                al.run_inventory()
                if al.slot_status(slot) == CassetteSlotStatus.OCCUPIED.name:
                    al.load_cartridge(slot)
                    assert al.slot_status(slot) == CassetteSlotStatus.EMPTY.name
                    al.unload_cartridge()
            except Exception as e:
                print(str(e))


def test_stage(microscope: Microscope,
               move_stage: bool = False) -> None:
    """ Test stage module attrs.
    :param microscope: Microscope object
    :param move_stage: If true, move stage around
    """
    stage = microscope.stage
    print("\nTesting stage...")
    pos = stage.position
    print("\tStatus:", stage.status)
    print("\tPosition:", pos)
    print("\tHolder:", stage.holder)
    print("\tLimits:", stage.limits)

    if not move_stage:
        return

    print("Testing stage movement...")
    print("\tGoto(x=1, y=-1)")
    stage.go_to(x=1, y=-1)
    sleep(1)
    print("\tPosition:", stage.position)
    print("\tGoto(x=-1, speed=0.5)")
    stage.go_to(x=-1, speed=0.5)
    sleep(1)
    print("\tPosition:", stage.position)
    print("\tMoveTo() to original position")
    stage.move_to(**pos)
    print("\tPosition:", stage.position)


def test_detectors(microscope: Microscope) -> None:
    """ Test all cameras / detectors.
    :param microscope: Microscope object
    """
    print("\nTesting cameras...")
    dets = microscope.detectors
    print("\tFilm settings:", dets.film_settings)
    print("\tCameras:", dets.cameras)

    stem = microscope.stem
    if stem.is_available:
        stem.enable()
        print("\tSTEM detectors:", dets.stem_detectors)
        stem.disable()


def test_optics(microscope: Microscope) -> None:
    """ Test optics module attrs.
    :param microscope: Microscope object
    """
    print("\nTesting optics...")
    opt = microscope.optics
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
    print("\tSpotsizeIndex:", illum.spotsize)

    orig_spot = illum.spotsize
    illum.spotsize = 5
    assert illum.spotsize == 5
    illum.spotsize = orig_spot

    print("\tIntensity:", illum.intensity)

    orig_int = illum.intensity
    illum.intensity = 0.44
    assert illum.intensity == 0.44
    illum.intensity = orig_int

    print("\tIntensityZoomEnabled:", illum.intensity_zoom)
    print("\tIntensityLimitEnabled:", illum.intensity_limit)
    print("\tShift:", illum.beam_shift)

    illum.beam_shift = Vector(0.5, 0.5)
    illum.beam_shift = Vector(0, 0)

    #print("\tTilt:", illum.beam_tilt)
    print("\tRotationCenter:", illum.rotation_center)
    print("\tCondenserStigmator:", illum.condenser_stigmator)
    #print("\tDFMode:", illum.dark_field)

    if microscope.condenser_system == CondenserLensSystem.THREE_CONDENSER_LENSES:
        print("\tCondenserMode:", illum.condenser_mode)
        print("\tIlluminatedArea:", illum.illuminated_area)
        print("\tProbeDefocus:", illum.probe_defocus)
        print("\tConvergenceAngle:", illum.convergence_angle)
        print("\tC3ImageDistanceParallelOffset:", illum.C3ImageDistanceParallelOffset)

        orig_illum = illum.illuminated_area
        illum.illuminated_area = 1.0
        assert illum.illuminated_area == 1.0
        illum.illuminated_area = orig_illum


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
        print("\tIllumination.StemRotation:", stem.rotation)
        print("\tIllumination.StemFullScanFieldOfView:", stem.scan_field_of_view)
        stem.disable()


def test_gun(microscope: Microscope,
             has_gun1: bool = False,
             has_feg: bool = False) -> None:
    """ Test gun module attrs.
    :param microscope: Microscope object
    :param has_gun1: If true, test GUN1 interface
    :param has_feg: If true, test C-FEG interface
    """
    print("\nTesting gun...")
    gun = microscope.gun
    print("\tHTValue:", gun.voltage)
    print("\tHTMaxValue:", gun.voltage_max)
    print("\tShift:", gun.shift)
    print("\tTilt:", gun.tilt)

    if has_gun1:
        print("\tHighVoltageOffsetRange:", gun.voltage_offset_range)
        print("\tHighVoltageOffset:", gun.voltage_offset)

    if has_feg:
        print("\tFegState:", gun.feg_state)
        print("\tHTState:", gun.ht_state)
        print("\tBeamCurrent:", gun.beam_current)
        print("\tFocusIndex:", gun.focus_index)

        gun.do_flashing(FegFlashingType.LOW_T)


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
        aps.disable("C2")
        aps.enable("C2")
        aps.select("C2", 50)


def test_user_buttons(microscope: Microscope) -> None:
    """ Test user button module attrs.
    :param microscope: Microscope object
    """
    print("\nTesting user buttons...")
    buttons = microscope.user_buttons
    print("Buttons: %s" % buttons.show())
    import comtypes.client

    def eventHandler():
        def Pressed():
            print("L1 button was pressed!")

    buttons.L1.Assignment = "My function"
    comtypes.client.GetEvents(buttons.L1, eventHandler)
    # Simulate L1 press
    buttons.L1.Pressed()
    # Clear the assignment
    buttons.L1.Assignment = ""


def test_general(microscope: Microscope,
                 check_door: bool = False) -> None:
    """ Test general attrs.
    :param microscope: Microscope object
    :param check_door: If true, check the door
    """
    print("\nTesting configuration...")
    print("\tConfiguration.ProductFamily:", microscope.family)
    print("\tBlankerShutter.ShutterOverrideOn:",
          microscope.optics.is_shutter_override_on)
    print("\tCondenser system:", microscope.condenser_system)

    if microscope.family == ProductFamily.TITAN:
        assert microscope.condenser_system == CondenserLensSystem.THREE_CONDENSER_LENSES.name
    else:
        assert microscope.condenser_system == CondenserLensSystem.TWO_CONDENSER_LENSES.name

    if check_door:
        print("\tUser door:", microscope.user_door.state)
        microscope.user_door.open()
        microscope.user_door.close()


def main(argv: Optional[List] = None) -> None:
    """ Test all aspects of the microscope interface. """
    parser = argparse.ArgumentParser(
        description="This test can use local or remote client. In the latter case "
                    "pytemscript-server must be already running",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-t", "--type", type=str,
                        choices=["direct", "socket", "zmq", "grpc"],
                        default="direct",
                        help="Connection type: direct, socket, zmq or grpc")
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

    full_test = False
    test_projection(microscope, has_eftem=False)
    test_detectors(microscope)
    test_vacuum(microscope, buffer_cycle=full_test)
    test_autoloader(microscope, check_loading=full_test, slot=1)
    test_temperature(microscope, force_refill=full_test)
    test_stage(microscope, move_stage=full_test)
    test_optics(microscope)
    test_illumination(microscope)
    test_gun(microscope, has_gun1=False, has_feg=False)
    if microscope.family != ProductFamily.TECNAI.name and args.type == "direct":
        test_user_buttons(microscope)
    test_general(microscope, check_door=False)

    if full_test:
        test_acquisition(microscope)
        test_stem(microscope)
        test_apertures(microscope, has_license=False)

    microscope.disconnect()


if __name__ == '__main__':
    main()


"""
Notes for Tecnai F20:
- DF element not found -> no DF mode or beam tilt. Check if python is 32-bit?
- Userbuttons not found
"""
