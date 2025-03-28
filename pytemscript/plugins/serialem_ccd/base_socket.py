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

import logging
import socket
import numpy as np
from typing import Tuple, Optional

from pytemscript.plugins.serialem_ccd.utils import Message, logwrap, enum_gs
from pytemscript.utils.misc import setup_logging


class BaseSocket:
    def __init__(self,
                 host: str = "127.0.0.1",
                 port: int = 48890,
                 debug: bool = False):
        self.sock = None
        self.host = host
        self.port = port
        self.save_frames = False
        self.num_grab_sum = 0

        setup_logging("semccd_socket_client.log", prefix="[SEMCCD]", debug=debug)
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
            if self.has_script_function(name):
                self.filter_functions[method_name] = name
        if ('SetEnergyFilter' in self.filter_functions.keys() and
                self.filter_functions['SetEnergyFilter'] == 'IFSetSlitIn'):
            self.wait_for_filter = 'IFWaitForFilter();'
        else:
            self.wait_for_filter = ''

    def has_script_function(self, name: str) -> bool:
        script = 'if ( DoesFunctionExist("%s") ) { Exit(1.0); } else { Exit(-1.0); }' % name
        result = self.ExecuteGetDoubleScript(script)
        return result > 0.0

    def connect(self) -> None:
        # recommended by Gatan to use localhost IP to avoid using tcp
        try:
            self.sock = socket.create_connection((self.host, self.port))
        except Exception as e:
            raise RuntimeError("Error communicating with SerialEMCCD socket server: %s" % e)

    def disconnect(self) -> None:
        """ Disconnect from the remote server. """
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

    def exchange_messages(self, message_send: Message,
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

    def get_long(self, funcName: str) -> int:
        """ Common class of function that gets a single long """
        funcCode = enum_gs[funcName]
        message_send = Message(longargs=(funcCode,))
        # First recieved message longargs is error code
        message_recv = Message(longargs=(0, 0))
        self.exchange_messages(message_send, message_recv)
        result = int(message_recv.array['longargs'][1])
        return result

    def send_long_get_long(self, funcName: str, longarg) -> int:
        """ Common class of function with one long arg that returns a single long """
        funcCode = enum_gs[funcName]
        message_send = Message(longargs=(funcCode, longarg))
        # First recieved message longargs is error code
        message_recv = Message(longargs=(0, 0))
        self.exchange_messages(message_send, message_recv)
        result = int(message_recv.array['longargs'][1])
        return result

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
        if not self.has_script_function(function_name):
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
        self.exchange_messages(message_send, message_recv)
        return message_recv
