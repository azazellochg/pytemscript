from instrument2 import GetInstrument


def test_projection(instrument):
    print("Testing projection...")
    projection = instrument.Projection
    print("Projection.Mode:", projection.Mode)
    print("Projection.Focus:", projection.Focus)
    print("Projection.Magnification:", projection.Magnification)
    print("Projection.MagnificationIndex:", projection.MagnificationIndex)
    print("Projection.CameraLengthIndex:", projection.CameraLengthIndex)
    print("Projection.ImageShift:", projection.ImageShift)
    print("Projection.ImageBeamShift:", projection.ImageBeamShift)
    print("Projection.DiffractionShift:", projection.DiffractionShift)
    print("Projection.DiffractionStigmator:", projection.DiffractionStigmator)
    print("Projection.ObjectiveStigmator:", projection.ObjectiveStigmator)
    print("Projection.SubModeString:", projection.SubModeString)
    print("Projection.SubMode:", projection.SubMode)
    print("Projection.SubModeMinIndex:", projection.SubModeMinIndex)
    print("Projection.SubModeMaxIndex:", projection.SubModeMaxIndex)
    print("Projection.ObjectiveExcitation:", projection.ObjectiveExcitation)
    print("Projection.ProjectionIndex:", projection.ProjectionIndex)
    print("Projection.LensProgram:", projection.LensProgram)
    print("Projection.ImageRotation:", projection.ImageRotation)
    print("Projection.DetectorShift:", projection.DetectorShift)
    print("Projection.DetectorShiftMode:", projection.DetectorShiftMode)
    print("Projection.ImageBeamTilt:", projection.ImageBeamTilt)
    print()


def test_acquisition(instrument, actual_acquisition=False):
    camera_name = None

    print("Testing acquisition...")
    acquisition = instrument.Acquisition
    cameras = acquisition.Cameras
    for n, camera in enumerate(cameras):
        print("Acquisition.Camera[%d]:" % n)
        info = camera.Info
        if not camera_name:
            camera_name = info.Name
        print("\tInfo.Name:", info.Name)
        print("\tInfo.Width:", info.Width)
        print("\tInfo.Height:", info.Height)
        print("\tInfo.PixelSize:", info.PixelSize)
        print("\tInfo.ShutterMode:", info.ShutterMode)
        print("\tInfo.ShutterModes:", info.ShutterModes)
        print("\tInfo.Binnings:", info.Binnings)
        params = camera.AcqParams
        print("\tAcqParams.ImageSize:", params.ImageSize)
        print("\tAcqParams.ExposureTime:", params.ExposureTime)
        print("\tAcqParams.Binning:", params.Binning)
        print("\tAcqParams.ImageCorrection:", params.ImageCorrection)
        print("\tAcqParams.ExposureMode:", params.ExposureMode)
        print("\tAcqParams.MinPreExposureTime:", params.MinPreExposureTime)
        print("\tAcqParams.MaxPreExposureTime:", params.MaxPreExposureTime)
        print("\tAcqParams.PreExposureTime:", params.PreExposureTime)
        print("\tAcqParams.MinPreExposurePauseTime:", params.MinPreExposurePauseTime)
        print("\tAcqParams.MaxPreExposurePauseTime:", params.MaxPreExposurePauseTime)
        print("\tAcqParams.PreExposurePauseTime:", params.PreExposurePauseTime)

    detectors = acquisition.Detectors
    for n, det in enumerate(detectors):
        print("Acquisition.Detector[%d]:" % n)
        info = det.Info
        print("\tInfo.Name:", info.Name)
        print("\tInfo.Brightness:", info.Brightness)
        print("\tInfo.Contrast:", info.Contrast)
        print("\tInfo.Binnings:", info.Binnings)

    params = acquisition.StemAcqParams
    print("Acquisition.StemAcqParams.ImageSize:", params.ImageSize)
    #Raises exception?
    #print("Acquisition.StemAcqParams.DwellTime:", params.DwellTime)
    print("Acquisition.StemAcqParams.Binning:", params.Binning)
    print()

    if not actual_acquisition or not camera_name:
        return

    print("Testing actual acquisition (%s)" % camera_name)
    acquisition.RemoveAllAcqDevices()
    acquisition.AddAcqDeviceByName(camera_name)
    images = acquisition.AcquireImages()
    for n, image in enumerate(images):
        print("Acquisition.AcquireImages()[%d]:" % n)
        print("\tAcqImage.Name:", image.Name)
        print("\tAcqImage.Width:", image.Width)
        print("\tAcqImage.Height:", image.Height)
        print("\tAcqImage.Depth:", image.Depth)
        array = image.Array
        print("\tAcqImage.Array.dtype:", array.dtype)
        print("\tAcqImage.Array.shape:", array.shape)
    print()


# for testing on the Titan microscope PC
print("Starting Test...")

instrument = GetInstrument()
test_projection(instrument)
test_acquisition(instrument)
