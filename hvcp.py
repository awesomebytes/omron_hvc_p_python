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
    data, = struct.unpack("<I", bytes)
    return data

def readUInt8(bytes):
    if len(bytes) != 1:
        print "Wrong number of bytes (" + str(len(bytes)) + ") should be 1"
        return None
    data = int(bytes.encode('hex'), 16)
    return data

def readInt8(bytes):
    if len(bytes) != 1:
        print "Wrong number of bytes (" + str(len(bytes)) + ") should be 1"
        return None
    #data = int(bytes.encode('hex'), 16)
    data, = struct.unpack("<b", bytes)
    return data

def readUInt16LE(bytes):
    if len(bytes) != 2:
        print "Wrong number of bytes (" + str(len(bytes)) + ") should be 2"
        return None
    data = int(bytes[:1].encode('hex'), 16)
    data += (int(bytes[1:].encode('hex'), 16) * 10)
    return data

def readInt16LE(bytes):
    if len(bytes) != 2:
        print "Wrong number of bytes (" + str(len(bytes)) + ") should be 2"
        return None
    data, = struct.unpack("<h", bytes)
    return data

def writeUInt16LE(data):
    return struct.pack("<H", data)[0]

def writeUInt8(data):
    return struct.pack("B", data)[0]

def int_to_hex_le(number):
    """Given a number as an integer, transform into the string
    in hex with little endian encoding"""
    data = struct.pack('<h', number)
    return data

def show_image_opencv(width, height, image):
    import cv2
    import numpy as np
    image_np = np.fromstring(image, dtype='B')
    print "image_np shape:"
    print image_np.shape
    image_reshaped = image_np.reshape(height, width)
    print "new shape:"
    print image_reshaped.shape
    cv2.imwrite("image.jpg", image_reshaped)
    cv2.imshow("Image:", image_reshaped)

    key = cv2.waitKey(0)
    if key == 27 or key == 1048603:
        return



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
        # Better not spam the screen if the payload is very big
        if len(payload) > 20:
            newp = payload[:10]
            p = newp.encode('hex')
            p += " ... "
            newp = payload[-10:]
            p += newp.encode('hex')
            p += "   (payload too long)"

        else:
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
    def __init__(self, tty="/dev/ttyUSB0", baudrate=921600, timeout=5):
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
        version_dict["major_version"] = readInt8(data[12:13])
        version_dict["minor_version"] = readInt8(data[13:14])
        version_dict["release_version"] = readInt8(data[14:15])
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

    def detection_execution(self, eyes_closed=True, gaze=True,
                            gender=True, age=True, face_orientation=True,
                            face_detection=True, hand_detection=True,
                            human_body_detection=True,
                            facial_expression=True,
                            image_bit=False,
                            image_bit_small=False,
                            show_image=True):
        """
        Sets the detection to execute once
        :return:
        """
        command = '\xfe\x03\x03\x00'
        # 2 bytes: things to run
        # 1 byte: reserved
        # The bytes are configured by bits, byte_config_1:
        # byte 7 6 5 4 3 2 1 0
        # eye_closed, line_of_sight, gender, age, face_orientation, face_detection, hand_detection, human_body_detection
        # byte_config_2:
        # 0, 0, 0, 0, 0, 0, 0, facial_expression [all 0's but the last]
        # byte_config_3:
        # 0, 0, 0, 0, 0, 0, 0, 0 [Fixed 0's]
        #                   |__|    <- the last bits enable getting grayscale image!
        #        little_image     big_image
        bitmask_1 = int('00000000', 2)
        bitmask_2 = int('00000000', 2)
        bitmask_3 = int('00000000', 2)
        if eyes_closed:
            bitmask_1 |= int('10000000', 2)
        if gaze:
            bitmask_1 |= int('01000000', 2)
        if gender:
            bitmask_1 |= int('00100000', 2)
        if age:
            bitmask_1 |= int('00010000', 2)
        if face_orientation:
            bitmask_1 |= int('00001000', 2)
        if face_detection:
            bitmask_1 |= int('00000100', 2)
        if hand_detection:
            bitmask_1 |= int('00000010', 2)
        if human_body_detection:
            bitmask_1 |= int('00000001', 2)

        if facial_expression:
            bitmask_2 |= int('00000001', 2)

        image_bit=True
        if image_bit:
            bitmask_3 |= int('00000001', 2)
        #image_bit_small=True
        if image_bit_small:
            bitmask_3 |= int('00000010', 2)

        command = command + chr(bitmask_1) + chr(bitmask_2) + chr(bitmask_3)
        #command = command + byte_config_1 + byte_config_2 + byte_config_3
        self.send_command_hex(command)
        #self.send_command(command)
        response_code, data = self.read_data()

        # header human_body[0-35], hand detection[0-35], face detection[0-35], reserved [0 fixed]
        header_offset = 4
        header = data[:header_offset]
        body_n = readInt8(header[0])
        hand_n = readInt8(header[1])
        face_n = readInt8(header[2])
        # reserved is useless
        detection_dict = {}
        detection_dict["body"] = {"num_detections": body_n}
        detection_dict["hand"] = {"num_detections": hand_n}
        detection_dict["face"] = {"num_detections": face_n}

        def get_results(bytes):
            coord_x = readInt16LE(bytes[0:2])
            coord_y = readInt16LE(bytes[2:4])
            detect_size = readInt16LE(bytes[4:6])
            reliability = readInt16LE(bytes[6:8])
            result_dict = {"coord_x": coord_x,
                           "coord_y": coord_y,
                           "detect_size": detect_size,
                           "reliability": reliability}
            return result_dict


        for body_idx in range(body_n):
            # bodies stuff body_n x 8 bytes
            init_offset = header_offset + body_idx*8
            end_offset = header_offset + body_idx*8 + 8
            result_dict = get_results(data[init_offset:end_offset])
            detection_dict["body"].update(result_dict)

        # hands stuff hand_n x 8 bytes
        for hand_idx in range(hand_n):
            # hand stuff hand x 8 bytes
            init_offset = header_offset + hand_idx*8
            end_offset = header_offset + hand_idx*8 + 8
            result_dict = get_results(data[init_offset:end_offset])
            detection_dict["hand"].update(result_dict)

        end_offset = header_offset
        # faces stuff face_n x 2~31 bytes
        for face_idx in range(face_n):
            # 8 byte Face detection
            if face_detection:
                init_offset = header_offset + face_idx*8
                end_offset = header_offset + face_idx*8 + 8
                result_dict = get_results(data[init_offset:end_offset])
                detection_dict["face"].update(result_dict)

            # 8 byte Face direction estimation
            if face_orientation:
                init_offset = end_offset
                end_offset = init_offset + 8
                detection_dict["face"].update({
                    "face_orientation": {
                                    "left_and_right_direction": readInt16LE(data[init_offset:init_offset+2]),
                                    "vertical_angle": readInt16LE(data[init_offset+2:init_offset+4]),
                                    "face_inclination_angle": readInt16LE(data[init_offset+4:init_offset+6]),
                                    "reliability": readInt16LE(data[init_offset+6:end_offset])
                                    }
                    })

            # 3 byte Age estimation
            if age:
                init_offset = end_offset
                end_offset = init_offset + 3
                detection_dict["face"].update({
                    "age_estimation": {
                                    "age": readInt8(data[init_offset:init_offset+1]),
                                    "reliability": readInt16LE(data[init_offset+1:end_offset])
                                    }
                    })

            # 3 byte Gender estimation
            if gender:
                init_offset = end_offset
                end_offset = init_offset + 3
                gender = readInt8(data[init_offset:init_offset+1])
                if gender == 0:
                    gender = "woman"
                elif gender == 1:
                    gender = "man"
                detection_dict["face"].update({
                    "gender_estimation": {
                                    "gender": gender,
                                    "reliability": readInt16LE(data[init_offset+1:end_offset])
                                    }
                    })

            # 2 byte Gaze estimation
            if gaze:
                init_offset = end_offset
                end_offset = init_offset + 2
                left_and_right_angle = readInt8(data[init_offset:init_offset+1])
                up_and_down_angle = readInt8(data[init_offset+1:end_offset])
                detection_dict["face"].update({
                    "gaze_estimation": {
                                    "left_and_right_angle": left_and_right_angle,
                                    "up_and_down_angle": up_and_down_angle
                                    }
                    })

            # 4 byte Eye closed
            if eyes_closed:
                init_offset = end_offset
                end_offset = init_offset + 4
                eyes_head_left = readInt16LE(data[init_offset:init_offset+2])
                eyes_head_right = readInt16LE(data[init_offset+2:end_offset])
                detection_dict["face"].update({
                    "eyes_estimation": {
                                    "eyes_head_left": eyes_head_left,
                                    "eyes_head_right": eyes_head_right
                                    }
                    })

            # 3 byte Facial expression estimation
            if facial_expression:
                init_offset = end_offset
                end_offset = init_offset + 3
                expression = readInt8(data[init_offset:init_offset+1])
                # 1 = expressionless, 2 = joy, 3 = surprise, 4 = anger, 5 = sadness
                if expression == 1:
                    expression_str = "expressionless"
                elif expression == 2:
                    expression_str = "joy"
                elif expression == 3:
                    expression_str = "surprise"
                elif expression == 4:
                    expression_str = "anger"
                elif expression == 5:
                    expression_str = "sadness"
                else:
                    expression_str = "unknown"
                top_score = readInt8(data[init_offset+1:init_offset+2])
                neg_pos_degree = readInt8(data[init_offset+2:end_offset])
                detection_dict["face"].update({
                    "facial_expression": {
                                    "expression": expression_str,
                                    "top_score": top_score,
                                    "neg_pos_degree": neg_pos_degree
                                    }
                    })

        if image_bit:
            # 76800 size (+4 of width and height))
            width = readInt16LE(data[end_offset:end_offset+2])
            height = readInt16LE(data[end_offset+2:end_offset+4])
            image = data[end_offset+4:]
            print "Got a big image of width, height: " + str((width, height))
            print "With image size: " + str(len(image))

        if image_bit_small:
            # 19200 size (+4 of width and height)
            width = readInt16LE(data[end_offset:end_offset+2])
            height = readInt16LE(data[end_offset+2:end_offset+4])
            image = data[end_offset+4:]
            print "Got a tiny image of width, height: " + str((width, height))
            print "With image size: " + str(len(image))

        if show_image and (image_bit or image_bit_small):
            show_image_opencv(width, height, image)

        return detection_dict

    def thresholds_read(self):
        """
        Reads the thresholds set for human body, hand and face detectors
        {'human_body': 254, 'face': 254, 'reserved': 254, 'hand': 254}
        :return:
        """
        self.send_command('fe060000')
        response_code, data = self.read_data()
        thresholds_dict = {}
        thresholds_dict["human_body"] = readInt16LE(data[0:2])
        thresholds_dict["hand"]       = readInt16LE(data[2:4])
        thresholds_dict["face"]       = readInt16LE(data[4:6])
        thresholds_dict["reserved"]   = readInt16LE(data[6:8])
        return thresholds_dict


    def thresholds_set(self, human_body, hand, face):
        """
        Set the thresholds on detecting bodies, hands and faces. Scale 1-1000, default 500.
        :param human_body: int
        :param hand: int
        :param face: int
        """
        command = '\xfe\x05\x08\x00'
        command += int_to_hex_le(human_body)
        command += int_to_hex_le(hand)
        command += int_to_hex_le(face)
        command += int_to_hex_le(0)
        self.send_command_hex(command)
        self.read_data()


    def detection_size_read(self):
        """
        Get the detection size configurations (max and min): human_body size,
        hand size and face size:
        {'human_body_min': 30, 'hand_min': 40, 'hand_max': 8192, 'face_min': 64, 'face_max': 8192, 'human_body_max': 8192}
        :return: dict
        """
        self.send_command('fe080000')
        response_code, data = self.read_data()
        detection_size_dict = {}
        detection_size_dict["human_body_min"] = readInt16LE(data[0:2])
        detection_size_dict["human_body_max"] = readInt16LE(data[2:4])
        detection_size_dict["hand_min"]       = readInt16LE(data[4:6])
        detection_size_dict["hand_max"]       = readInt16LE(data[6:8])
        detection_size_dict["face_min"]       = readInt16LE(data[8:10])
        detection_size_dict["face_max"]       = readInt16LE(data[10:12])
        return detection_size_dict

    def detection_size_set(self, human_body_min, human_body_max,
                           hand_min, hand_max, face_min, face_max):
        """
        Set the detection size settings, range 20-8192, defaults here:S
        :param human_body_min: int (30)
        :param human_body_max: int (8192)
        :param hand_min: int (40)
        :param hand_max: int (8192)
        :param face_min: int (64)
        :param face_max: int (8192)
        :return:
        """
        command = '\xfe\x07\x0c\x00'
        command += int_to_hex_le(human_body_min)
        command += int_to_hex_le(human_body_max)
        command += int_to_hex_le(hand_min)
        command += int_to_hex_le(hand_max)
        command += int_to_hex_le(face_min)
        command += int_to_hex_le(face_max)
        self.send_command_hex(command)
        self.read_data()


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

    def face_inclination_angle_set(self, face_direction, face_inclination):
        """
        Set the face inclination parameter. Note, seems to ignore face_inclination
        :param face_direction: str of: "front", "diagonal", "profile"
        :param face_inclination: str "15", "45"
        :return:
        """
        command = '\xfe\x09\x02\x00'
        if face_direction == "front":
            command += int_to_hex_le(0)
        elif face_direction == "diagonal":
            command += int_to_hex_le(1)
        elif face_direction == "profile":
            command += int_to_hex_le(2)
        else:
            print "Error: input for face_inclination_angle_set face_direction can only be 'front', 'diagonal, 'profile''"
            return

        if face_inclination == "15":
            command += int_to_hex_le(0)
        elif face_inclination == "45":
            command += int_to_hex_le(1)
        else:
            print "Error input for face_inclination_angle_set face_inclination can only be '15', '45' (as string)"
            return

        self.send_command_hex(command)
        self.read_data()


    def test_requests(self, num_of_codes_to_try=50):
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
    #
    # deg_to_set_camera = 0
    # print "Setting camera orientation to " + str(deg_to_set_camera) + " deg"
    # sensor.set_camera_orientation(deg_to_set_camera)
    # print "Getting camera orientation, degrees are: " + str(sensor.get_camera_orientation())
    # deg_to_set_camera = 90
    # print "Setting camera orientation to " + str(deg_to_set_camera) + " deg"
    # sensor.set_camera_orientation(deg_to_set_camera)
    # print "Getting camera orientation, degrees are: " + str(sensor.get_camera_orientation())
    # deg_to_set_camera = 180
    # print "Setting camera orientation to " + str(deg_to_set_camera) + " deg"
    # sensor.set_camera_orientation(deg_to_set_camera)
    # print "Getting camera orientation, degrees are: " + str(sensor.get_camera_orientation())
    # deg_to_set_camera = 270
    # print "Setting camera orientation to " + str(deg_to_set_camera) + " deg"
    # sensor.set_camera_orientation(deg_to_set_camera)
    # print "Getting camera orientation, degrees are: " + str(sensor.get_camera_orientation())
    # print "\n\n"

    # print "Setting thresholds: "
    # sensor.thresholds_set(500, 500, 500)
    #
    # print "Reading thresholds settings: " + str(sensor.thresholds_read())
    # print "\n\n"

    # print "Setting detection size:"
    # sensor.detection_size_set(30, 8192, 40, 8192, 64, 8192)
    #
    # print "Reading detection size settings: " + str(sensor.detection_size_read())
    # print "\n\n"

    print "Setting face angle:"
    sensor.face_inclination_angle_set("front", '45')

    print "Reading face angle settings: " + str(sensor.face_detection_angle_read())
    print "\n\n"

    # print "Detection execution: " + str(sensor.detection_execution())
    # print "\n\n"

    # print "Testing requests:"
    # sensor.test_requests()
