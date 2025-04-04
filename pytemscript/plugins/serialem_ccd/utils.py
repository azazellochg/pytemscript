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

import functools
import numpy as np
import logging

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
