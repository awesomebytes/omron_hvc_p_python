#!/usr/bin/env python

"""
This file translates the javascript implementation
of hvc-p sensor to python.

Javascript implementation source:
https://github.com/thorikawa/node-omron-hvc-p

Thanks Takahiro "Poly" Horikawa!

"""

import serial
import struct
import sys

BLUE = '\033[94m'
GREEN = '\033[92m'
ORANGE = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'

def readUInt32LE(bytes):
    if len(bytes) != 4:
        print "Wrong number of bytes (" + str(len(bytes)) + ") should be 4"
        return None
    data = int(bytes[:2].encode('hex'), 16)
    data += (int(bytes[2:].encode('hex'), 16) * 10) # * 10


    data, = struct.unpack("<I", bytes)
    return data

def readUInt8(bytes):
    if len(bytes) != 1:
        print "Wrong number of bytes (" + str(len(bytes)) + ") should be 1"
        return None
    data = int(bytes.encode('hex'), 16)
    return data

def readUInt16LE(bytes):
    if len(bytes) != 2:
        print "Wrong number of bytes (" + str(len(bytes)) + ") should be 2"
        return None
    data = int(bytes[:1].encode('hex'), 16)
    data += (int(bytes[1:].encode('hex'), 16) * 10)
    return data

def writeUInt16LE(data):
    return struct.pack("<H", data)[0]

def writeUInt8(data):
    return struct.pack("B", data)[0]


commands_dict = {'00': "  model / version read ",
                 '01': " set camera orientation",
                 '02': " get camera orientation",
                 '03': "  detection execution  ",
                 '05': "     set thresholds    ",
                 '06': "     get thresholds    ",
                 '07': "   set detection size  ",
                 '08': "   get detection size  ",
                 '09': "set face detection angle",
                 '0a': "get face detection angle"
                 }

response_codes_dict = {'00': "OK",
                       'ff': "UNDEFINED COMMAND",
                       'fe': "INTERNAL ERROR",
                       'fd': "ILLEGAL COMMAND",
                       'fa': "COMMUNICATION ERROR",
                       'fb': "COMMUNICATION ERROR",
                       'fc': "COMMUNICATION ERROR",
                       'f0': "DEVICE ERROR",
                       'f1': "DEVICE ERROR",
                       'f2': "DEVICE ERROR",
                       'f3': "DEVICE ERROR",
                       'f4': "DEVICE ERROR",
                       'f5': "DEVICE ERROR",
                       'f6': "DEVICE ERROR",
                       'f7': "DEVICE ERROR",
                       'f8': "DEVICE ERROR",
                       'f9': "DEVICE ERROR"
                       }

def print_datagram_send(command):
    print RED + "===========>"
    print "Sending datagram:"
    print "header     command_code       data_len  payload"
    encoded = command.encode('hex')
    h = encoded[:2]
    c = encoded[2:4]
    d = encoded[4:8]
    p = encoded[8:]
    if len(p) == 0:
        p = "None"
    print "  " + h + "            " + c + "              " + d + "      " + p
    print ("    [" + commands_dict.get(c, "     unknown     ") + "] (" +
           str(readUInt16LE(command[2:4])) + " bytes)   " + p.encode('utf-8') )
    print "===========>" + ENDC

def print_datagram_read(header, data_len, response_code, payload):
    print GREEN + "<========================="
    print "Read datagram:"
    print "header   response_code     data_len     payload"
    if header:
        h = header.encode('hex')
    else:
        print "  None      None         None         None"
        print "<=========================" + ENDC
        return

    if response_code:
        r = response_code.encode('hex')

    if data_len:
        d = data_len.encode('hex')
        data_len_bytes = readUInt32LE(data_len)
    else:
        print "  " + h + "      " + r + "   None         None"
        print "       " + response_codes_dict.get(r, "UNKNOWN_CODE")
        print "<=========================" + ENDC
        return

    if payload:
        p = payload.encode('hex')
        try:
            payload_encoded_unicode = unicode(payload)#payload.encode('unicode')
        except UnicodeDecodeError:
            payload_encoded_unicode = "[ can't encode in unicode ]"
    else:
        p = "None"
        payload_encoded_unicode = "None"

    print ("  " + h + "          " + r + "           " + d + "     " + p)
    print ("              " + (response_codes_dict.get(r, "UNKNOWN_CODE")) + "           (" +
           str(data_len_bytes) + " bytes)   '" + payload_encoded_unicode + "'" )
    # print ("        (" + str(data_len_bytes) + " bytes)     "
    #        +  + "       '" + payload_encoded_unicode + "'")
    print "<=========================" + ENDC

class HvcP(object):
    def __init__(self, tty="/dev/ttyUSB0", baudrate=921600, timeout=2):
        print "Connecting to '" + tty + "' at baudrate " + str(baudrate)
        self.ser = serial.Serial(port=tty, baudrate=baudrate, timeout=timeout)
        if self.ser.isOpen():
            print "Succesfully opened serial connection."
        else:
            print "Serial connection failed."
            sys.exit(-1)

    def clear_input(self):
        """
        Clear input buffer of serial connection
        """
        self.ser.flushInput()

    def clear_output(self):
        """
        Clear output buffer of serial connection
        """
        self.ser.flushOutput()

    def clear_input_output(self):
        """
        Clear input and output buffer of serial connection
        """
        self.ser.flush()

    def send_command(self, str_command):
        """
        :param str_command: str
        """
        self.send_command_hex(str_command.decode('hex'))

    def send_command_hex(self, hex_command):
        """
        :param hex_command: str that is already hex
        """
        print_datagram_send(hex_command)
        self.ser.write(hex_command)

    def read(self, size):
        bytes_read = self.ser.read(size)
        if len(bytes_read) != size:
            print "Warning: asked to read " + str(size) + " bytes but read " + str(len(bytes_read))
            return None
        return bytes_read

    def read_data(self, size=None):
        """
        Read the data coming from the board
        :param size: bytes to read (forcing, not using data_len from the protocol)
        :return: response_code (0 if all went well), data
                 None, None if something went wrong
        """
        response_header_bytes, data_len_bytes, response_code_bytes = None, None, None
        response_code, payload_bytes = None, None
        # Check header
        response_header_bytes = self.read(1)
        if response_header_bytes:
            if response_header_bytes != '\xfe':
                print "Error: Invalid response header, clearing input"
                self.clear_input()
            else:
                response_code_bytes = self.read(1)
                if response_code_bytes:
                    response_code = readUInt8(response_code_bytes)
                    if response_code_bytes == '\x00': # If all is OK
                        # Check data len, Little Endian Unsigned Int 32bits (4 bytes)
                        data_len_bytes = self.read(4)
                        if data_len_bytes:
                            data_len = readUInt32LE(data_len_bytes)
                            # total length = header + data_length_header + response_code + data_len
                            response_len = 1 + 4 + 1 + data_len
                            # Set the bytes to read as payload, contemplate the forced case
                            data_bytes_to_read = data_len
                            if size is not None:
                                data_bytes_to_read = size
                                print "Forcing to read " + str(data_bytes_to_read) + " bytes instead of " + str(data_len)
                            #print "Reading " + str(data_bytes_to_read) + " bytes as payload"
                            payload_bytes = self.read(data_bytes_to_read)
                    else:
                        print "Response code not OK, cleaning buffer"
                        # Read zeros
                        zeros = self.read(4)


        print_datagram_read(response_header_bytes, data_len_bytes, response_code_bytes, payload_bytes)
        return response_code, payload_bytes


    def get_version(self):
        """
        Get version info, e.g.:
        {'release_version': 10,
        'model': 'HVC-P       ',
        'major_version': 1,
        'revision': '7b040000',
        'minor_version': 0}
        :return: Dictionary with model, major_version, minor_version, release_version, revision
        """
        # Type string (12 characters): "HVC-C1B"
        # Major version (1 byte HEX): it will update at the time of large-scale change
        # Minor version (1 byte HEX): I will update when small change
        # Release version (1 byte HEX): I will update when minor modifications
        # Revision number (4 bytes HEX): use it for internal management

        self.send_command('fe000000')
        response_code, data = self.read_data()
        version_dict = {}
        version_dict["model"] = data[0:12]
        version_dict["major_version"] = readUInt8(data[12:13])
        version_dict["minor_version"] = readUInt8(data[13:14])
        version_dict["release_version"] = readUInt8(data[14:15])
        version_dict["revision"] = data[15:19].encode('hex')
        return version_dict


    def set_camera_orientation(self, angle):
        """
        Set the camera mounting orientation.
        :param angle: 0, 90, 180, 270
        :return:
        """
        angle_code = '00'
        if angle == 0:
            angle_code = '00'
        elif angle == 90:
            angle_code = '01'
        elif angle == 180:
            angle_code = '02'
        elif angle == 270:
            angle_code = '03'

        buf = 'fe' # sync header
        buf += '01' # command
        buf += '0100' # data len
        buf += angle_code # payload
        self.send_command(buf)
        response_code, data = self.read_data()
        # The datasheet says it should give back info about how it went
        # but in my case it does not work

    def get_camera_orientation(self):
        """
        Get the camera mounting orientation
        :return: 0, 90, 180, 270 as degrees of orientation
        and the config setting
        """
        self.send_command('fe020000')
        response_code, data = self.read_data()

        if data == '\x00':
            return 0
        elif data == '\x01':
            return 90
        elif data == '\x02':
            return 180
        elif data == '\x03':
            return 270
        return None, None

    def detection_execution(self):
        """
        Sets the detection to execute once
        :return:
        """
        command = 'fe030300'
        # 2 bytes: things to run
        # 1 byte: reserved
        # The bytes are configured by bits, byte_config_1:
        # byte 7 6 5 4 3 2 1 0
        # eye_closed, line_of_sight, sex, age, face_orientation, face_detection, hand_detection, human_body_detection
        # byte_config_2:
        # 0, 0, 0, 0, 0, 0, 0, facial_expression [all 0's but the last]
        # byte_config_3:
        # 0, 0, 0, 0, 0, 0, 0, 0 [Fixed 0's]

        # 04 = face_detection
        byte_config_1 = '04'
        byte_config_2 = '00'
        byte_config_3 = '00'
        command = command + byte_config_1 + byte_config_2 + byte_config_3
        self.send_command(command)
        response_code, data = self.read_data()
        if data is not None:
            print "detection execution data: " + str(data.encode('hex'))

    def thresholds_read(self):
        """
        Reads the thresholds set for human body, hand and face detectors
        {'human_body': 254, 'face': 254, 'reserved': 254, 'hand': 254}
        :return:
        """
        self.send_command('fe060000')
        response_code, data = self.read_data()
        thresholds_dict = {}
        thresholds_dict["human_body"] = readUInt16LE(data[0:2])
        thresholds_dict["hand"]       = readUInt16LE(data[2:4])
        thresholds_dict["face"]       = readUInt16LE(data[4:6])
        thresholds_dict["reserved"]   = readUInt16LE(data[6:8])
        return thresholds_dict


    def detection_size_read(self):
        """
        Get the detection size configurations (max and min): human_body size,
        hand size and face size:
        {'human_body_min': 30, 'hand_min': 40, 'hand_max': 320, 'face_min': 64, 'face_max': 320, 'human_body_max': 320}
        :return: dict
        """
        self.send_command('fe080000')
        response_code, data = self.read_data()
        detection_size_dict = {}
        detection_size_dict["human_body_min"] = readUInt16LE(data[0:2])
        detection_size_dict["human_body_max"] = readUInt16LE(data[2:4])
        detection_size_dict["hand_min"]       = readUInt16LE(data[4:6])
        detection_size_dict["hand_max"]       = readUInt16LE(data[6:8])
        detection_size_dict["face_min"]       = readUInt16LE(data[8:10])
        detection_size_dict["face_max"]       = readUInt16LE(data[10:12])
        return detection_size_dict

    def face_detection_angle_read(self):
        """
        Face orientation left and right, face is the configuration of the slope (each 1 byte)
        whatever that means.
        {'face_inclination': '+-15', 'face_direction': 'front_face (+-30)'}
        :return:
        """
        self.send_command('fe0a0000')
        response_code, data = self.read_data()
        face_angle_dict = {}
        if data[:1] == '\x00':
            face_angle_dict["face_direction"] = "front_face (+-30)"
        elif data[:1] == '\x01':
            face_angle_dict["face_direction"] = "diagonal_face (+-60)"
        elif data[:1] == '\x02':
            face_angle_dict["face_direction"] = "profile_face (+-90)"
        else:
            face_angle_dict["face_direction"] = "unknown_setting (" + data[:1].encode('hex') + ")"

        if data[1:2] == '\x00':
            face_angle_dict["face_inclination"] = "+-15"
        elif data[1:2] == '\x01':
            face_angle_dict["face_inclination"] = "+-45"
        else:
            face_angle_dict["face_inclination"] = "unknown_setting (" + data[1:2].encode('hex') + ")"

        return face_angle_dict


    def test_requests(self, num_of_codes_to_try=10):
        for i in range(num_of_codes_to_try):
            i_str_hex_enconded = str(hex(i))[2:4]
            #print "i_str_hex_enconded: " + i_str_hex_enconded
            if len(i_str_hex_enconded) == 1:
                i_str_hex_enconded = '0' + i_str_hex_enconded
            command = 'fe' + i_str_hex_enconded + '0000'
            print "\n\n~~~~~~~~~~~~~~~~~"
            print "Command # " + str(i)
            print "Sending command: '" + command + "'"
            self.send_command(command)
            print "Command sent, reading data:"
            response_code, data = self.read_data()
            print "~~~~~~~~~~~~~~~~~~~~\n\n"


if __name__ == '__main__':
    sensor = HvcP()
    print "Getting version:"
    print sensor.get_version()
    print "\n\n"

    deg_to_set_camera = 0
    print "Setting camera orientation to " + str(deg_to_set_camera) + " deg"
    sensor.set_camera_orientation(deg_to_set_camera)
    print "Getting camera orientation: " + str(sensor.get_camera_orientation())
    deg_to_set_camera = 90
    print "Setting camera orientation to " + str(deg_to_set_camera) + " deg"
    sensor.set_camera_orientation(deg_to_set_camera)
    print "Getting camera orientation: " + str(sensor.get_camera_orientation())
    deg_to_set_camera = 180
    print "Setting camera orientation to " + str(deg_to_set_camera) + " deg"
    sensor.set_camera_orientation(deg_to_set_camera)
    print "Getting camera orientation: " + str(sensor.get_camera_orientation())
    deg_to_set_camera = 270
    print "Setting camera orientation to " + str(deg_to_set_camera) + " deg"
    sensor.set_camera_orientation(deg_to_set_camera)
    print "Getting camera orientation: " + str(sensor.get_camera_orientation())
    print "\n\n"

    print "Reading thresholds settings: " + str(sensor.thresholds_read())
    print "\n\n"

    print "Reading detection size settings: " + str(sensor.detection_size_read())
    print "\n\n"

    print "Reading face angle settings: " + str(sensor.face_detection_angle_read())
    print "\n\n"

    print "Detection execution: " + str(sensor.detection_execution())
    print "\n\n"

    print "Testing requests:"
    sensor.test_requests()
