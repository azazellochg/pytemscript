# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# The code below is a modified version of: https://github.com/leginon-org/leginon/blob/myami-python3/pyscope/gatansocket.py
# This plugin needs the SERIALEMCCD plugin to be installed in DigitalMicrograph
# The instructions can be found at: https://bio3d.colorado.edu/SerialEM/hlp/html/setting_up_serialem.htm
#
# On the computer running DM, define environment variables:
# SERIALEMCCD_PORT=48890
# [optional] SERIALEMCCD_DEBUG=1

import logging
from typing import Tuple
import numpy as np

from pytemscript.plugins.serialem_ccd.utils import Message, logwrap, enum_gs
from pytemscript.plugins.serialem_ccd.base_socket import BaseSocket


class GatanSEMPlugin(BaseSocket):
    """ Main class that uses SerialEMCCD plugin of Digital Micrograph on Gatan PC.
    It creates a socket connection to that plugin.
    """
    def GetDMVersion(self) -> int:
        return self.get_long('GS_GetDMVersion')

    def GetNumberOfCameras(self) -> int:
        return self.get_long('GS_GetNumberOfCameras')

    def GetCameraName(self, camera_id: int) -> str:
        result = self.ExecuteCameraObjectFunction("CM_GetCameraName", camera_id)
        return result.array['longarray'].tobytes().decode('utf-8')

    def GetPluginVersion(self) -> int:
        return self.get_long('GS_GetPluginVersion')

    def IsCameraInserted(self, camera_id: int) -> bool:
        funcCode = enum_gs['GS_IsCameraInserted']
        message_send = Message(longargs=(funcCode, camera_id))
        message_recv = Message(longargs=(0,), boolargs=(0,))
        self.exchange_messages(message_send, message_recv)
        result = bool(message_recv.array['boolargs'][0])
        return result

    def InsertCamera(self, camera_id: int, state: int):
        funcCode = enum_gs['GS_InsertCamera']
        message_send = Message(longargs=(funcCode, camera_id), boolargs=(state,))
        message_recv = Message(longargs=(0,))
        self.exchange_messages(message_send, message_recv)

    def SetReadMode(self, mode: int, scaling: float = 1.0):
        funcCode = enum_gs['GS_SetReadMode']
        message_send = Message(longargs=(funcCode, mode), dblargs=(scaling,))
        message_recv = Message(longargs=(0,))
        self.exchange_messages(message_send, message_recv)

    def SetShutterNormallyClosed(self, camera_id: int, shutter: int):
        funcCode = enum_gs['GS_SetShutterNormallyClosed']
        message_send = Message(longargs=(funcCode, camera_id, shutter))
        message_recv = Message(longargs=(0,))
        self.exchange_messages(message_send, message_recv)

    @logwrap
    def SetK2Parameters(self,
                        readMode: int,
                        scaling: float = 1.0,
                        hardwareProc: int = 1,
                        doseFrac: bool = False,
                        frameTime: float = 0.25,
                        alignFrames: bool = False,
                        saveFrames: bool = False,
                        filt: str = '',
                        useCds: bool = False):
        funcCode = enum_gs['GS_SetK2Parameters2']
        # rotation and flip for non-frame saving image. It is the same definition
        # as in SetFileSaving2. If set to 0, it takes the value from GMS
        rotationFlip = 0
        self.save_frames = saveFrames

        flags = 0
        flags += int(useCds) * 2 ** 6
        # settings of unused flags
        # anti_alias
        reducedSizes = 0
        fullSizes = 0

        # filter name
        filt_str = filt + '\0'
        extra = len(filt_str) % 4
        if extra:
            npad = 4 - extra
            filt_str = filt_str + npad * '\0'
        longarray = np.frombuffer(bytes(filt_str, 'utf-8'), dtype=np.int32)

        longs = [
            funcCode,
            readMode,
            hardwareProc,
            rotationFlip,
            flags,
        ]
        bools = [
            doseFrac,
            alignFrames,
            saveFrames,
        ]
        doubles = [
            scaling,
            frameTime,
            reducedSizes,
            fullSizes,
            0.0,  # dummy3
            0.0,  # dummy4
        ]

        message_send = Message(longargs=longs, boolargs=bools, dblargs=doubles, longarray=longarray)
        message_recv = Message(longargs=(0,))  # just return code
        self.exchange_messages(message_send, message_recv)

    def setNumGrabSum(self, earlyReturnFrameCount: int, earlyReturnRamGrabs: int):
        # pack RamGrabs and earlyReturnFrameCount in one double
        self.num_grab_sum = 2**16 * earlyReturnRamGrabs + earlyReturnFrameCount

    def getNumGrabSum(self) -> int:
        return self.num_grab_sum

    @logwrap
    def SetupFileSaving(self,
                        rotationFlip,
                        dirname: str,
                        rootname: str,
                        filePerImage: int,
                        doEarlyReturn: bool = False,
                        earlyReturnFrameCount: int = 0,
                        earlyReturnRamGrabs: int = 0,
                        lzwtiff: bool = False) -> None:
        pixelSize = 1.0
        self.setNumGrabSum(earlyReturnFrameCount, earlyReturnRamGrabs)
        if self.save_frames and (doEarlyReturn or lzwtiff):
            # early return flag
            flag = 128 * int(doEarlyReturn) + 8 * int(lzwtiff)
            numGrabSum = self.getNumGrabSum()
            # set values to pass
            longs = [enum_gs['GS_SetupFileSaving2'], rotationFlip, flag, ]
            dbls = [pixelSize, numGrabSum, 0., 0., 0., ]
        else:
            longs = [enum_gs['GS_SetupFileSaving'], rotationFlip, ]
            dbls = [pixelSize, ]
        bools = [filePerImage, ]
        names_str = dirname + '\0' + rootname + '\0'
        extra = len(names_str) % 4
        if extra:
            npad = 4 - extra
            names_str = names_str + npad * '\0'
        longarray = np.frombuffer(bytes(names_str, 'utf-8'), dtype=np.int32)
        message_send = Message(longargs=longs, boolargs=bools, dblargs=dbls, longarray=longarray)
        message_recv = Message(longargs=(0, 0))
        self.exchange_messages(message_send, message_recv)

    def GetFileSaveResult(self) -> Tuple:
        #longs = [enum_gs['GS_GetFileSaveResult'], rotationFlip]
        message_send = Message(longargs=(enum_gs['GS_GetFileSaveResult'],))#, boolargs=bools, dblargs=dbls, longarray=longarray)
        message_recv = Message(longargs=(0, 0, 0))
        self.exchange_messages(message_send, message_recv)
        args = message_recv.array['longargs']
        numsaved = args[1]
        error = args[2]
        return numsaved, error

    def SelectCamera(self, camera_id: int):
        funcCode = enum_gs['GS_SelectCamera']
        message_send = Message(longargs=(funcCode, camera_id))
        message_recv = Message(longargs=(0,))
        self.exchange_messages(message_send, message_recv)

    def UpdateK2HardwareDarkReference(self, camera_id: int) -> int:
        function_name = 'K2_updateHardwareDarkReference'
        return self.ExecuteSendCameraObjectionFunction(function_name, camera_id)

    def PrepareDarkReference(self, camera_id: int) -> int:
        function_name = 'CM_PrepareDarkReference'
        return self.ExecuteSendCameraObjectionFunction(function_name, camera_id)

    def GetEnergyFilter(self) -> float:
        if 'GetEnergyFilter' not in self.filter_functions:
            return -1.0
        script = 'if ( %s() ) { Exit(1.0); } else { Exit(-1.0); }' % (self.filter_functions['GetEnergyFilter'],)
        return self.ExecuteGetDoubleScript(script)

    def SetEnergyFilter(self, value: bool = False) -> int:
        if 'SetEnergyFilter' not in self.filter_functions:
            return -1
        if value:
            i = 1
        else:
            i = 0
        script = '%s(%d); %s' % (self.filter_functions['SetEnergyFilter'], i, self.wait_for_filter)
        return self.ExecuteSendScript(script)

    def GetEnergyFilterWidthMax(self) -> float:
        if 'GetEnergyFilterWidthMax' not in self.filter_functions:
            return -1.0
        script = 'Exit(%s())' % (self.filter_functions['GetEnergyFilterWidthMax'],)
        return self.ExecuteGetDoubleScript(script)

    def GetEnergyFilterWidth(self) -> float:
        if 'GetEnergyFilterWidth' not in self.filter_functions:
            return -1.0
        script = 'Exit(%s())' % (self.filter_functions['GetEnergyFilterWidth'],)
        return self.ExecuteGetDoubleScript(script)

    def SetEnergyFilterWidth(self, value: float) -> int:
        if 'SetEnergyFilterWidth' not in self.filter_functions:
            return -1
        script = 'if ( %s(%f) ) { Exit(1.0); } else { Exit(-1.0); }' % (
        self.filter_functions['SetEnergyFilterWidth'], value)
        return self.ExecuteSendScript(script)

    def GetEnergyFilterOffset(self) -> float:
        if 'GetEnergyFilterOffset' not in self.filter_functions:
            return 0.0
        script = 'Exit(%s())' % (self.filter_functions['GetEnergyFilterOffset'],)
        return self.ExecuteGetDoubleScript(script)

    def SetEnergyFilterOffset(self, value: float) -> float:
        """
        wjr changing this to use the Gatan function IFSetEnergyOffset, which needs a technique and a value
        GMS 3.32,function apparently added in GMS 3.2. Later versions will need to be checked
        technique 0: instrument (not available)
        technique 1: prism offset (confusing because -10 is 10)
        technique 2: HT offset (has no effect on BioQuantum, but HT offset in DM will change)
        technique 3: drift tube ( this seems best since the value is consistent with direction)
        technique 4: prism adjust (confusing because -10 is 10, and it does not count when checking the energy loss value)
        note: the Gatan function being called is a void, so removed the boolean logic used for most other functions
        """
        technique = 3  # hard code to drift tube for now
        if 'SetEnergyFilterOffset' not in self.filter_functions:
            return -1.0
        script = '%s(%i,%f)' % (self.filter_functions['SetEnergyFilterOffset'], technique, value)
        self.ExecuteSendScript(script)
        #		return 1
        # or better to
        newvalue = self.GetEnergyFilterOffset()  # ? but wastes time
        if value == newvalue:
            return 1
        else:
            technique = 2  # reset the HT offset to 0, sometimes this gets set
            script = '%s(%i,%f)' % (self.filter_functions['SetEnergyFilterOffset'], technique, 0)
            self.ExecuteSendScript(script)
            newvalue = self.GetEnergyFilterOffset()
            if value == newvalue:
                return 1
            else:
                return -1

    def AlignEnergyFilterZeroLossPeak(self) -> float:
        script = ' if ( %s() ) { %s Exit(1.0); } else { Exit(-1.0); }' % (
        self.filter_functions['AlignEnergyFilterZeroLossPeak'], self.wait_for_filter)
        return self.ExecuteGetDoubleScript(script)

    @logwrap
    def GetImage(self,
                 processing: str,
                 height: int,
                 width: int,
                 binning: int,
                 top: int,
                 left: int,
                 bottom: int,
                 right: int,
                 exposure: float,
                 corrections: int,
                 shutter: int = 0,
                 shutterDelay: float = 0.0) -> np.ndarray:

        arrSize = width * height

        # TODO: need to figure out what these should be
        divideBy2 = 0
        settling = 0.0

        # prepare args for message
        if processing == 'dark':
            longargs = [enum_gs['GS_GetDarkReference']]
        else:
            longargs = [enum_gs['GS_GetAcquiredImage']]
        longargs.extend([
            arrSize,  # pixels in the image
            width, height,
        ])
        if processing == 'unprocessed':
            longargs.append(0)
        elif processing == 'dark subtracted':
            longargs.append(1)
        elif processing == 'gain normalized':
            longargs.append(2)
        longargs.extend([
            binning,
            top, left, bottom, right,
            shutter,
        ])
        if processing != 'dark':
            longargs.append(shutterDelay)
        longargs.extend([
            divideBy2,
            corrections,
        ])
        dblargs = [
            exposure,
            settling,
        ]

        message_send = Message(longargs=longargs, dblargs=dblargs)
        message_recv = Message(longargs=(0, 0, 0, 0, 0))
        self.exchange_messages(message_send, message_recv)

        longargs = message_recv.array['longargs'].tolist()
        logging.debug('GetImage longargs %s', longargs)
        if longargs[0] < 0:
            return 1 # FIXME
        arrSize = longargs[1]
        width = longargs[2]
        height = longargs[3]
        numChunks = longargs[4]
        bytesPerPixel = 2  # depends on the results formated =uint16
        numBytes = arrSize * bytesPerPixel
        chunkSize = (numBytes + numChunks - 1) // numChunks
        imArray = np.zeros((height * width,), np.uint16)
        received = 0
        remain = numBytes
        index = 0
        logging.debug('chunk size %d', chunkSize)
        for chunk in range(numChunks):
            recv_bytes = b''
            # send chunk handshake for all but the first chunk
            if chunk:
                message_send = Message(longargs=(enum_gs['GS_ChunkHandshake'],))
                self.exchange_messages(message_send)
            thisChunkSize = min(remain, chunkSize)
            chunkReceived = 0
            chunkRemain = thisChunkSize
            while chunkRemain:
                new_recv = self.recv_data(chunkRemain)
                len_recv = len(new_recv)
                recv_bytes += new_recv
                chunkReceived += len_recv
                chunkRemain -= len_recv
                remain -= len_recv
                received += len_recv
            last_index = int(index)
            logging.debug('chunk bytes length %d', len(recv_bytes))
            index = chunkSize * (chunk + 1) // bytesPerPixel
            logging.debug('array index range to fill %d:%d', last_index, index)
            imArray[last_index:index] = np.frombuffer(recv_bytes, dtype=np.uint16)
        imArray = imArray.reshape((height, width))
        return imArray
