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
import functools
import socket
from typing import Tuple, Optional
import numpy as np

# enum function codes as in https://github.com/mastcu/SerialEMCCD/blob/master/SocketPathway.cpp
# need to match exactly both in number and order
enum_gs = [
    'GS_ExecuteScript',
    'GS_SetDebugMode',
    'GS_SetDMVersion',
    'GS_SetCurrentCamera',
    'GS_QueueScript',
    'GS_GetAcquiredImage',
    'GS_GetDarkReference',
    'GS_GetGainReference',
    'GS_SelectCamera',
    'GS_SetReadMode',
    'GS_GetNumberOfCameras',
    'GS_IsCameraInserted',
    'GS_InsertCamera',
    'GS_GetDMVersion',
    'GS_GetDMCapabilities',
    'GS_SetShutterNormallyClosed',
    'GS_SetNoDMSettling',
    'GS_GetDSProperties',
    'GS_AcquireDSImage',
    'GS_ReturnDSChannel',
    'GS_StopDSAcquisition',
    'GS_CheckReferenceTime',
    'GS_SetK2Parameters',
    'GS_ChunkHandshake', # deleted in the new plugin?
    'GS_SetupFileSaving',
    'GS_GetFileSaveResult',
    'GS_SetupFileSaving2',
    'GS_GetDefectList',
    'GS_SetK2Parameters2',
    'GS_StopContinuousCamera',
    'GS_GetPluginVersion',
    'GS_GetLastError',
    'GS_FreeK2GainReference',
    'GS_IsGpuAvailable',
    'GS_SetupFrameAligning',
    'GS_FrameAlignResults',
    'GS_ReturnDeferredSum',
    'GS_MakeAlignComFile',
    'GS_WaitUntilReady',
    'GS_GetLastDoseRate',
    'GS_SaveFrameMdoc',
    'GS_GetDMVersionAndBuild',
    'GS_GetTiltSumProperties',
]
# lookup table of function name to function code, starting with 1
enum_gs = {item: index for index, item in enumerate(enum_gs, 1)}

## C "long" -> numpy "int32"
ARGS_BUFFER_SIZE = 1024
MAX_LONG_ARGS = 16
MAX_DBL_ARGS = 8
MAX_BOOL_ARGS = 8
sArgsBuffer = np.zeros(ARGS_BUFFER_SIZE, dtype=np.byte)


class Message:
    """ Information packet to send and receive on the socket. """
    def __init__(self,
                 longargs=(), boolargs=(), dblargs=(),
                 longarray=np.array([], dtype=np.int32)):
        """ Initialize with the sequences of args (longs, bools, doubles)
        and optional long array. """

        if len(longarray):
            longargs = (*longargs, len(longarray))

        self.dtype = [
            ('size', np.intc, (1,)),
            ('longargs', np.int32, (len(longargs),)),
            ('boolargs', np.int32, (len(boolargs),)),
            ('dblargs', np.double, (len(dblargs),)),
            ('longarray', np.int32, (len(longarray),)),
        ]
        self.array = np.empty((), dtype=self.dtype)
        self.array['size'] = np.array([self.array.nbytes], dtype=np.intc)
        self.array['longargs'] = np.array(longargs, dtype=np.int32)
        self.array['boolargs'] = np.array(boolargs, dtype=np.int32)
        self.array['dblargs'] = np.array(dblargs, dtype=np.double)
        self.array['longarray'] = longarray

    def pack(self) -> memoryview:
        """ Serialize the data. """
        packed = self.array.nbytes
        if packed > ARGS_BUFFER_SIZE:
            raise RuntimeError('Message packet size %d is larger than maximum %d' % (packed, ARGS_BUFFER_SIZE))
        return self.array.data

    def unpack(self, buf: bytes) -> None:
        """ Unpack buffer into our data structure. """
        self.array = np.frombuffer(buf, dtype=self.dtype)[0]


def logwrap(func):
    """ Decorator to log socket send and recv calls. """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.debug('%s\t%r\t%r', func.__name__, args, kwargs)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error('EXCEPTION: %s', e)
            raise

    return wrapper


class GatanSocket:
    def __init__(self, host: str = "127.0.0.1", port: int = 48890):
        self.sock = None
        self.host = host
        self.port = port
        self.save_frames = False
        self.num_grab_sum = 0
        self.connect()

        script_functions = [
            ('AFGetSlitState', 'GetEnergyFilter'),
            ('AFSetSlitState', 'SetEnergyFilter'),
            ('AFGetSlitWidth', 'GetEnergyFilterWidth'),
            ('AFSetSlitWidth', 'SetEnergyFilterWidth'),
            ('AFDoAlignZeroLoss', 'AlignEnergyFilterZeroLossPeak'),
            ('IFCGetSlitState', 'GetEnergyFilter'),
            ('IFCSetSlitState', 'SetEnergyFilter'),
            ('IFCGetSlitWidth', 'GetEnergyFilterWidth'),
            ('IFCSetSlitWidth', 'SetEnergyFilterWidth'),
            ('IFCDoAlignZeroLoss', 'AlignEnergyFilterZeroLossPeak'),
            ('IFGetSlitIn', 'GetEnergyFilter'),
            ('IFSetSlitIn', 'SetEnergyFilter'),
            ('IFGetEnergyLoss', 'GetEnergyFilterOffset'),
            ('IFSetEnergyOffset', 'SetEnergyFilterOffset'),  # wjr this was IFSetEnergyLoss
            ('IFGetMaximumSlitWidth', 'GetEnergyFilterWidthMax'),
            ('IFGetSlitWidth', 'GetEnergyFilterWidth'),
            ('IFSetSlitWidth', 'SetEnergyFilterWidth'),
            ('GT_CenterZLP', 'AlignEnergyFilterZeroLossPeak'),
        ]
        self.filter_functions = {}
        for name, method_name in script_functions:
            if self.hasScriptFunction(name):
                self.filter_functions[method_name] = name
        if ('SetEnergyFilter' in self.filter_functions.keys() and
                self.filter_functions['SetEnergyFilter'] == 'IFSetSlitIn'):
            self.wait_for_filter = 'IFWaitForFilter();'
        else:
            self.wait_for_filter = ''

    def hasScriptFunction(self, name: str) -> bool:
        script = 'if ( DoesFunctionExist("%s") ) { Exit(1.0); } else { Exit(-1.0); }' % name
        result = self.ExecuteGetDoubleScript(script)
        return result > 0.0

    def connect(self) -> None:
        # recommended by Gatan to use localhost IP to avoid using tcp
        self.sock = socket.create_connection((self.host, self.port))

    def disconnect(self) -> None:
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def reconnect(self) -> None:
        self.disconnect()
        self.connect()

    @logwrap
    def send_data(self, data: memoryview) -> None:
        self.sock.sendall(data)

    @logwrap
    def recv_data(self, n: int) -> bytes:
        return self.sock.recv(n)

    def ExchangeMessages(self, message_send: Message,
                         message_recv: Optional[Message] = None):
        self.send_data(message_send.pack())
        if message_recv is None:
            return
        recv_buffer = message_recv.pack()
        recv_len = recv_buffer.nbytes
        total_recv = 0
        parts = []
        while total_recv < recv_len:
            remain = recv_len - total_recv
            new_recv = self.recv_data(remain)
            parts.append(new_recv)
            total_recv += len(new_recv)
        buf = b''.join(parts)
        message_recv.unpack(buf)
        ## log the error code from received message
        sendargs = message_send.array['longargs']
        recvargs = message_recv.array['longargs']
        logging.debug('Func: %d, Code: %d', sendargs[0], recvargs[0])

    def GetLong(self, funcName: str) -> int:
        """ Common class of function that gets a single long """
        funcCode = enum_gs[funcName]
        message_send = Message(longargs=(funcCode,))
        # First recieved message longargs is error code
        message_recv = Message(longargs=(0, 0))
        self.ExchangeMessages(message_send, message_recv)
        result = int(message_recv.array['longargs'][1])
        return result

    def SendLongGetLong(self, funcName: str, longarg) -> int:
        """ Common class of function with one long arg that returns a single long """
        funcCode = enum_gs[funcName]
        message_send = Message(longargs=(funcCode, longarg))
        # First recieved message longargs is error code
        message_recv = Message(longargs=(0, 0))
        self.ExchangeMessages(message_send, message_recv)
        result = int(message_recv.array['longargs'][1])
        return result

    def GetDMVersion(self) -> int:
        return self.GetLong('GS_GetDMVersion')

    def GetNumberOfCameras(self) -> int:
        return self.GetLong('GS_GetNumberOfCameras')

    def GetCameraName(self, camera_id: int) -> str:
        result = self.ExecuteCameraObjectFunction("CM_GetCameraName", camera_id)
        return result.array['longarray'].tobytes().decode('utf-8')

    def GetPluginVersion(self) -> int:
        return self.GetLong('GS_GetPluginVersion')

    def IsCameraInserted(self, camera_id: int) -> bool:
        funcCode = enum_gs['GS_IsCameraInserted']
        message_send = Message(longargs=(funcCode, camera_id))
        message_recv = Message(longargs=(0,), boolargs=(0,))
        self.ExchangeMessages(message_send, message_recv)
        result = bool(message_recv.array['boolargs'][0])
        return result

    def InsertCamera(self, camera_id: int, state: int):
        funcCode = enum_gs['GS_InsertCamera']
        message_send = Message(longargs=(funcCode, camera_id), boolargs=(state,))
        message_recv = Message(longargs=(0,))
        self.ExchangeMessages(message_send, message_recv)

    def SetReadMode(self, mode: int, scaling: float = 1.0):
        funcCode = enum_gs['GS_SetReadMode']
        message_send = Message(longargs=(funcCode, mode), dblargs=(scaling,))
        message_recv = Message(longargs=(0,))
        self.ExchangeMessages(message_send, message_recv)

    def SetShutterNormallyClosed(self, camera_id: int, shutter: int):
        funcCode = enum_gs['GS_SetShutterNormallyClosed']
        message_send = Message(longargs=(funcCode, camera_id, shutter))
        message_recv = Message(longargs=(0,))
        self.ExchangeMessages(message_send, message_recv)

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
        self.ExchangeMessages(message_send, message_recv)

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
        self.ExchangeMessages(message_send, message_recv)

    def GetFileSaveResult(self) -> Tuple:
        #longs = [enum_gs['GS_GetFileSaveResult'], rotationFlip]
        message_send = Message(longargs=(enum_gs['GS_GetFileSaveResult'],))#, boolargs=bools, dblargs=dbls, longarray=longarray)
        message_recv = Message(longargs=(0, 0, 0))
        self.ExchangeMessages(message_send, message_recv)
        args = message_recv.array['longargs']
        numsaved = args[1]
        error = args[2]
        return numsaved, error

    def SelectCamera(self, camera_id: int):
        funcCode = enum_gs['GS_SelectCamera']
        message_send = Message(longargs=(funcCode, camera_id))
        message_recv = Message(longargs=(0,))
        self.ExchangeMessages(message_send, message_recv)

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
        technique 3: drift tube ( this seems best since the value is consistant with direction)
        technique 4: prism adjust (confusing because -10 is 10 and it does not count when checking the energy loss value)
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
            technique = 2  # reset the HT offfset to 0, sometimes this gets set
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
        self.ExchangeMessages(message_send, message_recv)

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
                self.ExchangeMessages(message_send)
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

    def ExecuteSendCameraObjectionFunction(self,
                                           function_name: str,
                                           camera_id: int = 0) -> int:
        # first longargs is error code. Error if > 0
        return self.ExecuteGetLongCameraObjectFunction(function_name, camera_id)

    def ExecuteGetLongCameraObjectFunction(self,
                                           function_name: str,
                                           camera_id: int = 0) -> int:
        """ Execute DM script function that requires camera object
        as input and output one long integer.
        """
        recv_longargs_init = (0,)
        result = self.ExecuteCameraObjectFunction(function_name, camera_id,
                                                  recv_longargs_init=recv_longargs_init)
        if result is False:
            return 1
        return int(result.array['longargs'][0])

    def ExecuteGetDoubleCameraObjectFunction(self,
                                           function_name: str,
                                           camera_id: int = 0) -> float:
        """ Execute DM script function that requires camera object
        as input and output double floating point number.
        """
        result = self.ExecuteCameraObjectFunction(function_name, camera_id)
        if result is False:
            return -999.0
        return float(result.array['dblargs'][0])

    def ExecuteCameraObjectFunction(self,
                                    function_name: str,
                                    camera_id: int = 0,
                                    recv_longargs_init: Tuple = (0,),
                                    recv_dblargs_init: Tuple = (0.0,)) -> Message:
        """ Execute DM script function that requires camera object as input.
        See examples at http://www.dmscripting.com/files/CameraScriptDocumentation.txt
        and http://www.dmscripting.com/tutorial_microscope_commands.html
        """
        if not self.hasScriptFunction(function_name):
            raise NotImplementedError(function_name)
        fullcommand = ["Object manager = CM_GetCameraManager();",
                       "Object cameraList = CM_GetCameras(manager);",
                       "Object camera = ObjectAt(cameraList,%d);" % camera_id,
                       "%s(camera);" % function_name
                       ]
        fullcommand = "\n".join(fullcommand)
        result = self.ExecuteScript(fullcommand, camera_id, recv_longargs_init,
                                    recv_dblargs_init)
        return result

    def ExecuteSendScript(self,
                          command_line: str,
                          select_camera: int = 0) -> int:
        recv_longargs_init = (0,)
        result = self.ExecuteScript(command_line, select_camera, recv_longargs_init)
        # first longargs is error code. Error if > 0
        return int(result.array['longargs'][0])

    def ExecuteGetLongScript(self,
                          command_line: str,
                          select_camera: int = 0) -> int:
        """ Execute DM script and return the result as integer. """
        return int(self.ExecuteGetDoubleScript(command_line, select_camera))

    def ExecuteGetDoubleScript(self,
                          command_line: str,
                          select_camera: int = 0) -> float:
        """ Execute DM script that gets one double float number. """
        result = self.ExecuteScript(command_line, select_camera)
        return float(result.array['dblargs'][0])

    def ExecuteScript(self,
                      command_line: str,
                      select_camera: int = 0,
                      recv_longargs_init: Tuple = (0,),
                      recv_dblargs_init: Tuple = (0.0,)) -> Message:
        funcCode = enum_gs['GS_ExecuteScript']
        cmd_str = command_line + '\0'
        extra = len(cmd_str) % 4
        if extra:
            npad = 4 - extra
            cmd_str = cmd_str + npad * '\0'
        # send the command string as 1D long array
        longarray = np.frombuffer(bytes(cmd_str, 'utf-8'), dtype=np.int32)
        message_send = Message(longargs=(funcCode,), boolargs=(select_camera,), longarray=longarray)
        message_recv = Message(longargs=recv_longargs_init, dblargs=recv_dblargs_init)
        self.ExchangeMessages(message_send, message_recv)
        return message_recv


if __name__ == '__main__':
    g = GatanSocket(host="192.168.71.2")
    print(g)
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
        'readMode': 1, # {'non-K2 cameras':-1, 'linear': 0, 'counting': 1, 'super resolution': 2}
        'scaling': 1.0,
        'hardwareProc': 1, #{'none': 0, 'dark': 2, 'gain': 4, 'dark+gain': 6}
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
        'processing': 'unprocessed', # dark, dark subtracted, gain normalized
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

    #g.SetK2Parameters(**k2params)
    g.SetReadMode(-1)
    image = g.GetImage(**acqparams)
    print("Got image array:", image.dtype, image.shape)
