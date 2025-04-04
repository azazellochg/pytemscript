from pytemscript.plugins.serialem_ccd.plugin import GatanSEMPlugin


def main():
    g = GatanSEMPlugin(host="192.168.71.2", debug=True)
    print('Version', g.GetDMVersion())
    print('GetNumberOfCameras', g.GetNumberOfCameras())
    print('GetPluginVersion', g.GetPluginVersion())
    print("SelectCamera")
    g.SelectCamera(0)
    print("GetCameraName", g.GetCameraName(0))
    if not g.IsCameraInserted(0):
        print('InsertCamera')
        g.InsertCamera(0, True)
    print('IsCameraInserted', g.IsCameraInserted(0))

    k2params = {
        'readMode': 1,  # {'non-K2 cameras':-1, 'linear': 0, 'counting': 1, 'super resolution': 2}
        'scaling': 1.0,
        'hardwareProc': 1,  # {'none': 0, 'dark': 2, 'gain': 4, 'dark+gain': 6}
        'doseFrac': False,
        'frameTime': 0.25,
        'alignFrames': False,
        'saveFrames': False,
        'filt': 'None'
    }


    def getDMVersion(g):
        """ Return DM version details: version_long, major.minor.sub """
        version_long = g.GetDMVersion()
        if version_long < 40000:
            major = 1
            minor = None
            sub = None
            if version_long >= 31100:
                # 2.3.0 gives an odd number of 31100
                major = 2
                minor = 3
                sub = 0
                version_long = 40300
        elif version_long == 40000:
            # minor version can be 0 or 1 in this case
            # but likely 1 since we have not used this module until k2 is around
            major = 2
            minor = 1
            sub = 0
        else:
            major = version_long // 10000 - 2
            remainder = version_long - (major + 2) * 10000
            minor = remainder // 100
            sub = remainder % 100

        return version_long, '%d.%d.%d' % (major, minor, sub)


    def getCorrectionFlags(g):
        """
        Binary Correction flag sum in GMS. See Feature #8391.
        GMS 3.3.2 has pre-counting correction which is superior.
        SerialEM always does this correction.
        David M. said SerialEM default is 49 for K2 and 1 for K3.
        1 means defect correction only.
        49 means defect, bias, and quadrant (to be the same as Ultrascan).
        I don't think the latter two need applying in counting.
        """
        version_id, version_string = getDMVersion(g)
        isDM332orUp = version_id >= 50302
        return 1 if isDM332orUp else 0


    acqparams = {
        'processing': 'unprocessed',  # dark, dark subtracted, gain normalized
        'height': 2048,
        'width': 2048,
        'binning': 1,
        'top': 0,
        'left': 0,
        'bottom': 2048,
        'right': 2048,
        'exposure': 1.0,
        'corrections': getCorrectionFlags(g),
        'shutter': 0,
        'shutterDelay': 0.0,
    }

    # g.SetK2Parameters(**k2params)
    g.SetReadMode(-1)
    image = g.GetImage(**acqparams)
    print("Got image array:", image.dtype, image.shape)


if __name__ == '__main__':
    main()
