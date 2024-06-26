import serial
import binascii  # 在BIN(二进制)和ASCII之间转换
import struct  # 将数据作为完整的结构传输，用struct模块进行处理
from binascii import *
from crcmod import *
import time
from serial_package import offical_Judge_Handler
import numpy as np
import copy
import threading
import random
from datetime import datetime

from macro import home_test, position_alarm, enemy, receiver_id
from common.common import is_inside


class ReadUART(object):
    _progress = np.ones(6, dtype=int) * -1  # 初始化雷达标记进度
    sb_location = [1, 0., 0., 2, 0., 0., 3, 0., 0., 4, 0., 0., 5, 0., 0., 7, 0., 0.]  # 位置记录提供给哨兵决策
    _Doubling_times = -1  # 翻倍机会次数
    _HP = np.ones(16, dtype=int) * -1  # 初始化机器人血量
    _Now_Stage = -1  # 当前比赛阶段
    _Game_Start_Flag = False  # 比赛开始标志
    _Game_End_Flag = False  # 比赛结束标志
    Remain_time = -1  # 剩余时间
    record_flag = False  # 计时标志

    _bytes2int = lambda x: (0x0000 | x[0]) | (x[1] << 8)
    _byte2int = lambda x: x

    @staticmethod
    def read(ser):
        bufferCount = 0
        buffer = [0]
        buffer *= 1000
        cmdID = 0

        while True:
            s = ser.read(1)
            s = int().from_bytes(s, 'big')

            if bufferCount > 50:
                bufferCount = 0

            buffer[bufferCount] = s

            if bufferCount == 0:
                if buffer[bufferCount] != 0xa5:
                    bufferCount = 0
                    continue

            if bufferCount == 5:
                if offical_Judge_Handler.myVerify_CRC8_Check_Sum(id(buffer), 5) == 0:
                    bufferCount = 0
                    if buffer[bufferCount] == 0xa5:
                        bufferCount = 1
                    continue

            if bufferCount == 7:
                cmdID = (0x0000 | buffer[5]) | (buffer[6] << 8)

            if bufferCount == 10 and cmdID == 0x020E:
                if offical_Judge_Handler.myVerify_CRC16_Check_Sum(id(buffer), 10):

                    # 雷达易伤机会
                    ReadUART._Doubling_times = ((buffer[7] << 6) & 0b11000000)

                    bufferCount = 0
                    if buffer[bufferCount] == 0xa5:
                        bufferCount = 1
                    continue

            if bufferCount == 15 and cmdID == 0x020C:
                if offical_Judge_Handler.myVerify_CRC16_Check_Sum(id(buffer), 15):

                    # 雷达标记进度
                    ReadUART._progress = np.array([ReadUART._byte2int(buffer[i]) for i in range(7, 13)], dtype=int)

                    bufferCount = 0
                    if buffer[bufferCount] == 0xa5:
                        bufferCount = 1
                    continue

            if bufferCount == 20 and cmdID == 0x0001:
                if offical_Judge_Handler.myVerify_CRC16_Check_Sum(id(buffer), 20):

                    # 比赛阶段信息
                    if ReadUART._Now_Stage < 2 and ((buffer[7] >> 4) == 2 or (buffer[7] >> 4) == 3 or (buffer[7] >> 4) == 4):
                        ReadUART._Game_Start_Flag = True
                    if ReadUART._Now_Stage < 5 and (buffer[7] >> 4) == 5:
                        ReadUART._Game_End_Flag = True

                    ReadUART._Now_Stage = buffer[7] >> 4
                    ReadUART.Remain_time = ReadUART._bytes2int((buffer[8], buffer[9]))

                    bufferCount = 0
                    if buffer[bufferCount] == 0xa5:
                        bufferCount = 1
                    continue

            if bufferCount == 41 and cmdID == 0x0003:
                if offical_Judge_Handler.myVerify_CRC16_Check_Sum(id(buffer), 41):

                    # 各车血量
                    ReadUART._HP = np.array([ReadUART._bytes2int((buffer[i * 2 - 1], buffer[i * 2])) for i in range(4, 20)], dtype=int)

                    bufferCount = 0
                    if buffer[bufferCount] == 0xa5:
                        bufferCount = 1
                    continue

            bufferCount += 1


class StaticUART:
    if home_test:
        home_width = 28
        home_height = 15
    else:
        home_width = 28
        home_height = 15
    real_width = 28
    real_height = 15
    specific_color = {0: [1, 2, 3, 4, 5, 7], 1: [101, 102, 103, 104, 105, 107]}
    _lock = threading.Lock()
    stop_flag = False
    robot_location = None

    alarm_flag = 0
    alarm_location = None
    alarm_enemy = ['enemy_is_red', 'enemy_is_blue'][enemy]

    send_id = 9 if enemy else 109
    sb_id = 7 if enemy else 107
    referee_system_receiver_id = 0x8080

    car_data_id = 0x020F  # 车间通信的子内容ID
    lidar_data_id = 0x0121  # 雷达自主决策的子内容ID
    auto_data = 0  # 发布数据（累加）
    auto_numbers = 0  # 使用次数

    receiver = receiver_id[enemy]

    @staticmethod
    def create_SOF(datalen):
        """
        创建一个帧头（SOF），其中包含了长度信息、校验和等数据，以便用于数据传输
        """
        buffer = [0]
        buffer = buffer * 5
        buffer[0] = 0xa5
        buffer[1] = datalen
        buffer[2] = 0
        buffer[3] = 0
        buffer[4] = offical_Judge_Handler.myGet_CRC8_Check_Sum(id(buffer), 4, 0xff)  # 校验值

        return bytes(bytearray(buffer))

    @staticmethod
    def push_loc(location):
        """
        将传入的位置信息 location 深复制到类变量 Static_UART.robot_location 中
        """
        # StaticUART._lock.acquire()
        # 如果不适用深复制（或许浅复制也行），那么多进程时可能反而会更慢
        StaticUART.robot_location = copy.deepcopy(location)
        # StaticUART._lock.release()

    @staticmethod
    def push_alarm(location):
        """
        将传入的位置信息 location 深复制到类变量 Static_UART.alarm_location 中
        """
        StaticUART.alarm_location = copy.deepcopy(location)
        StaticUART.alarm_flag = 1

    @staticmethod
    def radar_between_car(data: list, datalenth: int, receiver_ID, ser):
        """
        将指定的数据通过串口 ser 传输给雷达设备
        :param data:只能传输int类型的数据
        """
        SOF = StaticUART.create_SOF(datalenth + 6)  # dataLength 指要发的数据长度，前面还有6位的字节漂移
        CMDID = (b'\x01' b'\x03')
        data = bytes(bytearray(data))  # 将列表转换为字节流
        dataid_sender_receiver = struct.pack('<3H', StaticUART.car_data_id, StaticUART.send_id, receiver_ID)
        data_sum = SOF + CMDID + dataid_sender_receiver + data
        decodeData = binascii.b2a_hex(data_sum).decode('utf-8')  # 将 data_sum 转换为十六进制表示，并通过 decode('utf-8') 将其解码为字符串
        data_last, hexer = offical_Judge_Handler.crc16Add(decodeData)
        # data_last: 附加了 CRC-16 校验码后的完整数据
        # hexer: 附加了 CRC-16 校验码的完整数据的二进制表示
        ser.write(hexer)

    @staticmethod
    def autonomous_lidar(data: int, datalenth: int, ser):
        """
        将指定的数据通过串口 ser 传输给雷达设备
        """
        SOF = StaticUART.create_SOF(datalenth + 6)  # dataLength 指要发的数据长度，前面还有6位的字节漂移
        CMDID = (b'\x01' b'\x03')
        data = bytes(bytearray(data))
        dataid_sender_receiver = struct.pack('<3H', StaticUART.lidar_data_id, StaticUART.send_id, StaticUART.referee_system_receiver_id)
        data_sum = SOF + CMDID + dataid_sender_receiver + data
        decodeData = binascii.b2a_hex(data_sum).decode('utf-8')
        data_last, hexer = offical_Judge_Handler.crc16Add(decodeData)
        ser.write(hexer)

    @staticmethod
    def auto_lidar(data, ser):
        SOF = StaticUART.create_SOF(7)
        CMDID = (b'\x01' b'\x03')
        data = struct.pack("<4H", StaticUART.lidar_data_id,
                           StaticUART.send_id, StaticUART.referee_system_receiver_id, data)
        data3 = SOF + CMDID + data
        decodeData = binascii.b2a_hex(data3).decode('utf-8')  # 转换为16进制表示，又将其解码成字符串
        _, hexer = offical_Judge_Handler.crc16Add(decodeData)
        ser.write(hexer)

    @staticmethod
    def random_receiver(whether_random):
        """
        根据 whether_random 参数来决定是否随机选择接收者
        """
        if whether_random:
            return random.choice(StaticUART.receiver)
        else:
            return StaticUART.receiver[0]

    @staticmethod
    def radar_map(ID, X, Y):
        Z = 1
        try:
            SOF = StaticUART.create_SOF(14)
            CMDID = (b'\x05' b'\x03')
            data = struct.pack("<1H3f", ID, X, Y, Z)  # 按照格式 "<1H3f"打包为二进制数据
            data1 = SOF + CMDID + data
            decodeData = binascii.b2a_hex(data1).decode('utf-8')  # 转换为16进制表示，又将其解码成字符串
            _, hexer = offical_Judge_Handler.crc16Add(decodeData)
            # hexer: 附加了 CRC-16 校验码的完整数据的二进制表示
            return hexer

        except Exception as e:
            print("serial write data has ERROR: \033[0m", e)

    @staticmethod
    def xy_check(x: float, y: float, ):
        """
        将传入坐标（x,y）转换为相对于真实场地的坐标值x,y
        """
        new_x = x * StaticUART.real_width / StaticUART.home_width
        new_y = y * StaticUART.real_height / StaticUART.home_height

        return new_x, new_y

    @staticmethod
    def alarm_xy_check(numpy_xy):
        """
        将传入坐标（numpy）转换为相对于真实场地的坐标值(numpy)
        """
        new_x = numpy_xy[0] * StaticUART.real_width / StaticUART.home_width
        new_y = numpy_xy[1] * StaticUART.real_height / StaticUART.home_height
        return np.array([new_x, new_y])

    @staticmethod
    def robot_data_transmit_map(ser):
        """
        通过串口传输位置信息，并且判断是否报警以及进行自主决策
        """
        try:
            while 1:
                for row in StaticUART.robot_location:
                    target_id = int(row[0])
                    if target_id in StaticUART.specific_color[enemy]:
                        x, y = float(row[1]), float(row[2])
                        x, y = StaticUART.xy_check(x, y)
                        hexer = StaticUART.radar_map(target_id, x, y)
                        ser.write(hexer)  # 将生成的数据 hexer（包含id,坐标）通过串口 ser 进行传输

                        ReadUART.sb_location[StaticUART.handle_id(target_id) * 3 - 2] = x
                        ReadUART.sb_location[StaticUART.handle_id(target_id) * 3 - 1] = y

                        # for alarm in position_alarm[StaticUART.alarm_enemy]:
                        #     # 检查当前目标ID是否在报警相关数据中
                        #     if target_id in alarm[0] and is_inside(np.array(alarm[1]),
                        #                                            StaticUART.alarm_xy_check(row[1:3])):
                        #         data = StaticUART.handle_id(target_id) + StaticUART.handle_id(alarm[-1])
                        #
                        #         StaticUART.radar_between_car(data, datalenth=4,
                        #                                       receiver_ID=StaticUART.random_receiver(
                        #                                           104 if home_test else True), ser=ser)
                        time.sleep(0.09)

                    if ReadUART._Now_Stage in [2, 3, 4] and ReadUART.record_flag is False:
                        start_time = datetime.now()
                        ReadUART.record_flag = True
                    else:
                        start_time = None

                    StaticUART.sb_communicate(ser)

                    if ReadUART._Doubling_times > 0:
                        if start_time is not None:
                            if int((datetime.now() - start_time).total_seconds()) > 200 and StaticUART.auto_numbers == 0:
                                StaticUART.auto_data += 1
                                StaticUART.auto_lidar(StaticUART.auto_data, ser=ser)
                                StaticUART.auto_numbers += 1
                                time.sleep(0.03)
                            elif int((datetime.now() - start_time).total_seconds()) > 320 and StaticUART.auto_numbers == 1:
                                StaticUART.auto_data += 1
                                StaticUART.auto_lidar(StaticUART.auto_data, ser=ser)
                                StaticUART.auto_numbers += 1
                                time.sleep(0.03)
                        elif np.sum(ReadUART._progress > 100) >= 3:
                            StaticUART.auto_data += 1
                            StaticUART.auto_lidar(StaticUART.auto_data, ser=ser)
                            StaticUART.auto_numbers += 1
                            time.sleep(0.03)

        except:
            time.sleep(0.1)

    @staticmethod
    def handle_id(target_id):
        if target_id > 100:
            target_id -= 100
        # if target_id == 1:
        #     target_id = [1, 0]
        # if target_id == 2:
        #     target_id = [2, 0]
        # if target_id == 3:
        #     target_id = [2, 1]
        # if target_id == 4:
        #     target_id = [2, 2]
        # if target_id == 5:
        #     target_id = [3, 2]

        return target_id

    @staticmethod
    def advanced_loop(ser):
        while 1:
            StaticUART.robot_data_transmit_map(ser)
            if StaticUART.stop_flag:
                break

    @staticmethod
    def sb_communicate(ser):
        """
        将场上车辆坐标按顺序发送给哨兵
        """
        SOF = StaticUART.create_SOF(48 + 6)
        CMDID = (b'\x01' b'\x03')
        indices = [1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17]
        data = struct.pack("<3H12f", StaticUART.car_data_id,
                           StaticUART.send_id, StaticUART.sb_id,
                           *tuple(ReadUART.sb_location[i] for i in indices))
        data2 = SOF + CMDID + data
        decodeData = binascii.b2a_hex(data2).decode('utf-8')  # 转换为16进制表示，又将其解码成字符串
        _, hexer = offical_Judge_Handler.crc16Add(decodeData)
        ser.write(hexer)
        time.sleep(0.03)

    @staticmethod
    def test_communicate(ser):
        """
        测试串口通信
        """
        try:
            while 1:
                x = 10
                y = 10
                hexer = StaticUART.radar_map(104, x, y)
                ser.write(hexer)
                time.sleep(0.1)
        except:
            time.sleep(0.1)
