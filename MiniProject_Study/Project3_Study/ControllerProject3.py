# coding: utf-8
import RPi.GPIO as GPIO
import smbus
import time
import datetime
from threading import *
import pymysql
import sys
import spidev
#import cv2
import os
from matplotlib import pyplot as plt
from matplotlib import animation
import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import ast

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation
import random

db = pymysql.connect(host="localhost", user="root", password="password", db="sensordb")
curs = db.cursor()
# settime error 
connect_timeout = 200
read_timeout = 200
write_timeout = 200
max_allowed_packet = 1073741824


# LED SENSOR SET
led1 = 20
led2 = 21

# MOTOR
enablePin = 12
positivePin = 4
negativePin = 25

# PIR
pPir = 24

# Piezo
Piezo = 13

# Buzzer
Melody = [1567, 1567, 1760, 1760, 1567, 1567, 1318, 1567, 1567, 1318, 1318, 1174, 
                1567, 1567, 1760, 1760, 1567, 1567, 1318, 1567, 1318, 1174, 1318, 1046]

# SERV M
Motor = 17

# ULTRA
trigger = 0
echo = 1
led = 20

# SET MODE
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(led1, GPIO.OUT)
GPIO.setup(led2, GPIO.OUT)
GPIO.setup(enablePin, GPIO.OUT)
GPIO.setup(positivePin, GPIO.OUT)
GPIO.setup(negativePin, GPIO.OUT)
GPIO.setup(pPir, GPIO.IN)
GPIO.setup(Piezo, GPIO.OUT)
GPIO.setup(Motor, GPIO.OUT)
GPIO.setup(trigger, GPIO.OUT)
GPIO.setup(echo, GPIO.IN)
GPIO.setup(led, GPIO.OUT)
pwm = GPIO.PWM(enablePin, 50)
buzz = GPIO.PWM(Piezo, 700)
pMotor = GPIO.PWM(Motor, 50)



# 8bit LED 주소
led_addr = 0x20
# 8bit LED 입력포트
IN_PORT0 = 0x00
IN_PORT1 = 0X01
# 8bit LED 출력포트
OUT_PORT0 = 0x02
OUT_PORT1 = 0x03
# 입력들어온값 반전(입력포트 극성반전)
POLARITY_IVE_PORT0 = 0x04
POLARITY_IVE_PORT1 = 0x05
# 초기화 시키는 포트(1:input, 0:output)
CONFIG_PORT0 = 0x06
CONFIG_PORT1 = 0x07

# STEPMOTOR SET
step_addr = 0x20

IN_PORT = 0x00
IN_PORT = 0x01
OUT_PORT0 = 0x02
OUT_PORT1 = 0x03
POLARITY_IVE_PORT0 = 0x04
POLARITY_IVE_PORT1 = 0x05
CONFIG_PORT0 = 0x06
CONFIG_PORT1 = 0x07

Phase_1 = [0x80, 0x40, 0x20, 0x10]

# 8bit LED 데이터
LedData = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80]

# TEMP, HUMI SENSOR SET
SHT20_ADDR = 0x40
SHT20_TEMP = 0xf3
SHT20_HUMI = 0xf5
SHT20_RESET = 0xfe
bus = smbus.SMBus(1)
data = [0, 0]

# 8bit LED 초기화
bus.write_byte_data(led_addr, CONFIG_PORT1, 0x00)
bitFlag = 0
stopFlag = 0
# STEP MOTOR 0x00
bus.write_byte_data(step_addr, CONFIG_PORT0, 0x00)
stopStep = 0
# SERV MOTOR 0
stopServ = 0

# SPI CDS
spi = spidev.SpiDev()
spi.open(0, 1)
spi.max_speed_hz = 1000000

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

# TemThread
class Worker(QThread):
    sig_strs = pyqtSignal(list)
    sig_strs_1 = pyqtSignal(int)
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
    # RUN
    def run(self):
        try:
            db1 = pymysql.connect(host="localhost", user="root", password="password", db="sensordb")
            curs1 = db1.cursor()
            while True:
                time.sleep(10)
                #TEMP
                bus.write_byte(SHT20_ADDR, SHT20_TEMP)
                time.sleep(0.26)
                for i in range(2):
                    data[i] = bus.read_byte(SHT20_ADDR)
                value = data[0] << 8 | data[1]
                temp = -46.84 + 175.72 / 65536 * int(value)
                #HUMI
                bus.write_byte(SHT20_ADDR, SHT20_HUMI)
                time.sleep(0.26)
                for i in range(2):
                    data[i] = bus.read_byte(SHT20_ADDR)
                value = data[0] << 8 | data[1]
                humi = -6.0 + 125.0 / 65536 * int(value)
                # 소수점 2번째 까지 출력을 위해 round함수 사용
                t = round(temp, 2)
                h = round(humi, 2)
                # float 변수를 string변수로 형태변환
                tempD = str(t)
                humiD = str(h)
                # DATABASE INSERT 쿼리문
                sql = "INSERT INTO temhumDB (Time, Temp, Hum) VALUES(default, "+tempD+", "+humiD+")"
                curs1.execute(sql)
                db1.commit()
                # 터미널창에서 확인
                print("Temp : %.2fC\t Humi: %.2f %%" % (float(temp), float(humi)))

                # 현재 온습도 상태 업데이트
                sql1 = "SELECT * FROM temhumDB ORDER BY TIME DESC limit 1"
                curs1.execute(sql1)
                rows = curs1.fetchall()
                sql2 = "SELECT COUNT(*) FROM temhumDB"
                curs1.execute(sql2)
                rows2 = curs1.fetchall()
                count = rows2[0][0]
                #tStr = rows[0][0].strftime('%Y-%m-%d %H:%M:%S') + " | TEM : " + rows[0][1] + "℃ | HUM : " + rows[0][2] + "%"
                strS = []
                #strS.append(tStr)
                strS.append(rows[0][0])
                strS.append(t)
                strS.append(h)
                strS.append(count)
                self.sig_strs.emit(strS)
        except KeyboardInterrupt:
            print('t keyboard interrupt')
            pass

# TimeThread
class Worker2(QThread):
    sig_strs2 = pyqtSignal(str)
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
    # RUN
    def run(self):
        try:
            while True:
                time.sleep(1)
                str = time.strftime('%c', time.localtime(time.time()))
                self.sig_strs2.emit(str)
        except KeyboardInterrupt:
            print('ti Keyboard interrupt')
            pass

# 8BIT LED Thread
class Worker3(QThread):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
    # RUN
    def run(self):
        try:
            global bitFlag
            global stopFlag
            while True:
                # 8bit LED 정지버튼 누르면
                if stopFlag == 1:
                    bus.write_byte_data(led_addr, OUT_PORT1, 0x00)
                    self.do_run = False
                    break
                if bitFlag == 2:
                    for i in range(0, 8):
                        bus.write_byte_data(led_addr, OUT_PORT1, LedData[i])
                        #if stopFlag == 1:
                        #    bus.write_byte_data(led_addr, OUT_PORT1, 0x00)
                        #    self.do_run = False
                else:
                    bus.write_byte_data(led_addr, OUT_PORT1, 0x00)
        except KeyboardInterrupt:
            print('l keyboard interrupt')
            bus.write_byte_data(led_addr, OUT_PORT1, 0x00)
            pass

# PIRThread
class Worker4(QThread):
    sig_strs4 = pyqtSignal(list)
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
    def run(self):
        try:
            db2 = pymysql.connect(host="localhost", user="root", password="password", db="sensordb")
            curs2 = db2.cursor()
            while True:
                if GPIO.input(pPir) == False:
                    # DATABASE INSERT 쿼리문
                    sql = "INSERT INTO pirDB (Time, Det) VALUES(default, 'Detected')"
                    curs2.execute(sql)
                    db2.commit()
                    # 현재 PIR 업데이트
                    sql = "SELECT * FROM pirDB ORDER BY TIME DESC limit 1"
                    curs2.execute(sql)
                    rows = curs2.fetchall()
                    sql2 = "SELECT COUNT(*) FROM pirDB"
                    curs2.execute(sql2)
                    rows2 = curs2.fetchall()
                    count = rows2[0][0]
                    pStr = rows[0][0].strftime('%Y-%m-%d %H:%M:%S') + " | Detected"
                    str = []
                    str.append(pStr)
                    str.append(count)
                    self.sig_strs4.emit(str)
                    """#Buzzer close
                    buzz.start(50)
                    for i in range(24):
                        buzz.ChangeFrequency(Melody[i])
                        time.sleep(0.3)
                        if GPIO.input(pPir) == True:
                            break;
                    """
                else:
                    buzz.stop()
        except KeyboardInterrupt:
            print('p Keyboard interrupt')
            pass

# STEP M Thread
class Worker5(QThread):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
    def run(self):
        try:
            while True:
                global stopStep
                bus.write_byte_data(step_addr, OUT_PORT1, 0x00) # LED 불 끔
                if stopStep == 0:
                    for i in range(4):
                        if i == 3:
                            if stopStep == 1:
                                print("step stop")
                                bus.write_byte_data(step_addr, OUT_PORT1, 0x00)
                                break
                            bus.write_byte_data(step_addr, OUT_PORT0, Phase_1[3] + Phase_1[0])
                            time.sleep(0.01)
                            break
                        bus.write_byte_data(step_addr, OUT_PORT0, Phase_1[i] + Phase_1[i+1])
                        time.sleep(0.01)
                else:
                    self.do_run = False
                    break
        except KeyboardInterrupt:
            pass
        
# SERV M Thread
class Worker6(QThread):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
    def run(self):
        try:
            global stopServ
            while True:
                pMotor.start(4.9)
                if stopServ == 0:
                    pMotor.ChangeDutyCycle(1.8)  # 0.7ms/20ms * 100를 기준으로 
                    if stopServ == 1:
                        pMotor.stop()
                        continue
                    time.sleep(2)
                    pMotor.ChangeDutyCycle(4.9)  # 1.5
                    if stopServ == 1:
                        pMotor.stop()
                        continue
                    time.sleep(2)
                    pMotor.ChangeDutyCycle(9.5)  # 2.3
                    if stopServ == 1:
                        pMotor.stop()
                        continue
                    time.sleep(2)
                else:
                    pMotor.stop()
                    self.do_run = False
                    break
        except KeyboardInterrupt:
            GPIO.cleanup()

# ULTRA THREAD
class Worker7(QThread):
    sig_strs7 = pyqtSignal(list)
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
    def run(self):
        try:
            db3 = pymysql.connect(host="localhost", user="root", password="password", db="sensordb")
            curs3 = db3.cursor()
            while True:
                time.sleep(1)
                # DISTANCE
                dis1 = self.dis()
                # 소수점 2번째 까지 출력을 위해 round함수 사용
                dis2 = round(dis1, 2)
                # float 변수를 string변수로 형태변환
                disData = repr(dis2)
                # DATABASE INSERT 쿼리문
                if dis2 < 5:
                    sql = "INSERT INTO ultraDB (Time, Dis) VALUES(default, " +disData+")"
                    curs3.execute(sql)
                    db3.commit()
                    sql1 = "SELECT * FROM ultraDB ORDER BY TIME DESC limit 1"
                    curs3.execute(sql1)
                    rows = curs3.fetchall()
                    sql2 = "SELECT COUNT(*) FROM ultraDB"
                    curs3.execute(sql2)
                    rows1 = curs3.fetchall()
                    count = rows1[0][0]
                    uStr = rows[0][0].strftime('%Y-%m-%d %H:%M:%S') + " | DISTANCE : " + rows[0][1]
                    str = []
                    str.append(uStr)
                    str.append(count)
                    self.sig_strs7.emit(str)
 
        except KeyboardInterrupt:
            GPIO.cleanup()
    # Distance Calcul
    def dis(self):
        GPIO.output(trigger, True)
        time.sleep(0.00001)         # 10us
        GPIO.output(trigger, False)
        while GPIO.input(echo) == False:    # 출발시간
            start = time.time()
        while GPIO.input(echo) == True:     # 도착시간
            end = time.time()
        distance = ((end - start) * 34000) / 2
        return distance

# ULTRA THREAD
class Worker8(QThread):
    sig_strs8 = pyqtSignal(list)
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
    def run(self):
        try:
            while True:
                val = self.ReadData(0)
                if val < 450:
                    for i in range(8):
                        bus.write_byte_data(led_addr, OUT_PORT1, LedData[i])
                elif val < 500:
                    for i in range(0, 7, 1):
                        bus.write_byte_data(led_addr, OUT_PORT1, LedData[i])
                elif val < 550:
                    for i in range(0, 6, 1):
                        bus.write_byte_data(led_addr, OUT_PORT1, LedData[i])
                elif val < 580:
                    for i in range(0, 5, 1):
                        bus.write_byte_data(led_addr, OUT_PORT1, LedData[i])
                elif val < 610:
                    for i in range(0, 4, 1):
                        bus.write_byte_data(led_addr, OUT_PORT1, LedData[i])
                elif val < 640:
                    for i in range(0, 3, 1):
                        bus.write_byte_data(led_addr, OUT_PORT1, LedData[i])
                elif val < 680:
                    for i in range(0, 2, 1):
                        bus.write_byte_data(led_addr, OUT_PORT1, LedData[i])
                elif val < 720:
                    for i in range(0, 1, 1):
                        bus.write_byte_data(led_addr, OUT_PORT1, LedData[i])
                else:
                    bus.write_byte_data(led_addr, OUT_PORT1, 0x00)
        except KeyboardInterrupt:
            pass
    def ReadData(self, channel):
        adc = spi.xfer2([1, 0, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data

# GUI
class Window(QWidget):
    def __init__(self):
        super().__init__()
        # Title Set
        self.setWindowTitle('Controller')
        # LED 정보 부분
        sbox = QHBoxLayout()
        gb = QGroupBox()
        sbox.addWidget(gb)
        box = QVBoxLayout()
        gb.setStyleSheet("QGroupBox  {"
                                    "border: 1px solid gray;"
                                    "border-color:" #FF17365D;
                                    "margin-top27px;"
                                    "font-size: 14px;"
                                    "border-radius: 15px;"
                                    "}")
        gb1box = QVBoxLayout()
        gb1 = QGroupBox("LED STATUS")
        # LED LIST
        self.llist = QListWidget()
        self.llist.setStyleSheet(
                    "QListWidget{"
                               "color: red;"
                               "font: 13pt Comic Sans MS;"
                               "}"
                    "QListWidget::item {"
                                "padding: 2px;"
                                "}"
                    "QListWidget::item:selected {"
                            "background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #369, stop:1 #147);"
                            "color: white;"
                    "}")
        
        gb1box.addWidget(self.llist)
        # LED ON/OFF 버튼 부분
        gb1bbox = QHBoxLayout()
        self.onBtn = QPushButton('LED ON')
        self.offBtn = QPushButton('LED OFF')
        self.onBtn.setStyleSheet("color: red;"
                             "background-color: white;"
                             "border-style: solid;"
                             "border-width: 2px;"
                             "border-color: yellow ;"
                             "border-radius: 3px")
        self.offBtn.setStyleSheet("color: blue;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-width: 3px;"
                              "border-color: yellow")
        gb1bbox.addWidget(self.onBtn)
        gb1bbox.addWidget(self.offBtn)
        gb1box.addLayout(gb1bbox)
        # LED 현 상태 부분
        gb1sbox = QHBoxLayout()
        ledLabel = QLabel('LED STATE')
        gb1sbox.addWidget(ledLabel)
        self.ledLabel2 = QLabel()
        gb1sbox.addWidget(self.ledLabel2)
        gb1box.addLayout(gb1sbox)
        ledLabel.setStyleSheet("color: blue;"
                              "background-color: white;"
                              "border-style: dashed;"
                              "border-width: 3px;"
                              "border-color: yellow")
        
        self.ledLabel2.setStyleSheet("color: red;"
                              "background-color: white;"
                              "border-style: dashed;"
                              "border-width: 3px;"
                              "border-color: yellow")        
        
        # STEP MOTOR
        stepbox = QHBoxLayout()
        gb2 = QGroupBox('STEP MOTOR')
        # STEP M ON/OFF 버튼 부분
        self.sonBtn = QPushButton('STEP MOTOR ON')
        self.sonBtn.setStyleSheet("color: green;"
                             "background-color: white;"
                             "border-style: solid;"
                             "border-radius: 6px;"
                             "border-width: 2px;"
                             "border-color: #1E90FF;")
        self.soffBtn = QPushButton('STEP MOTOR OFF')
        self.soffBtn.setStyleSheet("color: red;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-radius: 6px;"
                              "border-width: 2px;"
                              "border-color: #1E90FF;")
        stepbox.addWidget(self.sonBtn)
        stepbox.addWidget(self.soffBtn)
        
        # ULTRA SENSOR
        ubox = QVBoxLayout()
        gb3 = QGroupBox('ULTRA SENSOR DATA')
        
        # ULTRA SENSOR 리스트 가져오기
        self.uList = QListWidget()
        self.uList.setStyleSheet(
                    "QListWidget{"
                               "font: 13pt Comic Sans MS;"
                               "}"
                    "QListWidget::item {"
                                "padding: 2px;"
                                "}"
                    "QListWidget::item:selected {"
                                    "background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #369, stop:1 #147);"
                                    "color: white;"
                    "}")
        ubox.addWidget(self.uList)

        # GB LAYOUT 배치
        gb1.setLayout(gb1box)
        box.addWidget(gb1)

        gb2.setLayout(stepbox)
        box.addWidget(gb2)
        
        gb3.setLayout(ubox)
        box.addWidget(gb3)
        gb.setLayout(box)
#------------------------------layout
        # 온도/습도 부분
        gb = QGroupBox()
        sbox.addWidget(gb)
        box = QVBoxLayout()
        gb.setStyleSheet("QGroupBox  {"
                            "border: 1px solid gray;"
                            "border-color:" #FF17365D;
                            "margin-top27px;"
                            "font-size: 14px;"
                            "border-radius: 15px;"
                            "}")
        pbox = QVBoxLayout()
        gb1 = QGroupBox("TEM/HUM STATUS")
        
        # 온/습도 리스트 가져오기
        self.tList = QListWidget()
        self.tList.setStyleSheet(
                    "QListWidget{"
                               "color: green;"
                               "font: 15pt Comic Sans MS;"
                               "}"
                    "QListWidget::item {"
                                "padding: 2px;"
                                "}"
                    "QListWidget::item:selected {"
                                "background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #369, stop:1 #147);"
                                "color: white;"
                                "}")
        pbox.addWidget(self.tList)

        # 현재시간
        tibox = QHBoxLayout()
        tiLabel = QLabel('NOW TIME')
        tibox.addWidget(tiLabel)
        self.tiLabel2 = QLabel()
        tibox.addWidget(self.tiLabel2)
        tiLabel.setStyleSheet("color: blue;"
                              "background-color: white;"
                             "border-style: dashed;"
                              "border-width: 3px;"
                              "border-color: blue")
        self.tiLabel2.setStyleSheet("color: dark;"
                              "background-color: white;"
                              "border-style: dashed;"
                              "border-width: 3px;"
                              "border-color: blue")
        pbox.addLayout(tibox)
        
        # MOTOR 작동
        mbox = QVBoxLayout()
        gb2 = QGroupBox("MOTOR")
        mbbox = QHBoxLayout()
        self.pBtn = QPushButton('M 순방향')
        self.nBtn = QPushButton('M 역방향')
        self.sBtn = QPushButton('M 정지')
        self.pBtn.setStyleSheet("color: green;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-radius: 6px;"
                              "border-width: 2px;"
                              "border-color: green;")
        self.nBtn.setStyleSheet("color: blue;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-radius: 6px;"
                              "border-width: 2px;"
                              "border-color: green;")
        self.sBtn.setStyleSheet("color: red;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-radius: 6px;"
                              "border-width: 2px;"
                              "border-color: green;")
        mbbox.addWidget(self.pBtn)
        mbbox.addWidget(self.nBtn)
        mbbox.addWidget(self.sBtn)
        mbox.addLayout(mbbox)
        
        # SERV MOTOR
        sevbox = QVBoxLayout()
        gb3 = QGroupBox('SERV MOTOR')
        # SERV M ON/OFF 버튼 부분
        sebox = QHBoxLayout()
        self.svonBtn = QPushButton('SERV MOTOR ON')
        self.svoffBtn = QPushButton('SERV MOTOR OFF')
        self.svonBtn.setStyleSheet("color: green;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-radius: 6px;"
                              "border-width: 2px;"
                              "border-color: blue;")
        self.svoffBtn.setStyleSheet("color: red;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-radius: 6px;"
                              "border-width: 2px;"
                              "border-color: blue;")
        sebox.addWidget(self.svonBtn)
        sebox.addWidget(self.svoffBtn)
        sevbox.addLayout(sebox)
        
        # TEMP LAYOUT
        gb1.setLayout(pbox)
        box.addWidget(gb1)
        
        gb2.setLayout(mbox)
        box.addWidget(gb2)
        
        gb3.setLayout(sevbox)
        box.addWidget(gb3)
    
        gb.setLayout(box)
#------------------------------layout
         # 8bit LED, PIF 센서
        gb = QGroupBox()
        sbox.addWidget(gb)
        box = QVBoxLayout()
        gb.setStyleSheet("QGroupBox  {"
                            "border: 1px solid gray;"
                            "border-color:" #FF17365D;
                            "margin-top27px;"
                            "font-size: 14px;"
                            "border-radius: 15px;"
                            "}")
        lpbox = QVBoxLayout()
        gb0 = QGroupBox('8Bit Led Controller')
        
        # 8bit LED
        lbox = QHBoxLayout()
        self.useBtn = QPushButton('BIT 사용')
        self.noBtn = QPushButton('BIT 정지')
        abox = QHBoxLayout()
        self.lonBtn = QPushButton('8BIT ON')
        self.loffBtn = QPushButton('8BIT OFF')
        self.useBtn.setStyleSheet("color: green;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-radius: 6px;"
                              "border-width: 2px;"
                              "border-color: puple;")
        self.noBtn.setStyleSheet("color: red;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-radius: 6px;"
                              "border-width: 2px;"
                              "border-color: puple;")
        self.lonBtn.setStyleSheet("color: green;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-radius: 6px;"
                              "border-width: 2px;"
                              "border-color: puple;")
        self.loffBtn.setStyleSheet("color: red;"
                              "background-color: white;"
                              "border-style: solid;"
                              "border-radius: 6px;"
                              "border-width: 2px;"
                              "border-color: puple;")

        # 사용버튼 먼저 누르고 Start
        self.noBtn.setEnabled(False)
        self.lonBtn.setEnabled(False)
        self.loffBtn.setEnabled(False)
        lbox.addWidget(self.useBtn)
        lbox.addWidget(self.noBtn)
        abox.addWidget(self.lonBtn)
        abox.addWidget(self.loffBtn)
        lpbox.addLayout(lbox)
        lpbox.addLayout(abox)

        # PIR 감지센서
        pibox = QVBoxLayout()
        gb1 = QGroupBox('감지 Sensor ')
        self.pList = QListWidget()
        self.pList.setStyleSheet(
                    "QListWidget{"
                               "font: 11pt Comic Sans MS;"
                               "}"
                    "QListWidget::item {"
                                "padding: 2px;"
                                "}"
                    "QListWidget::item:selected {"
                                "background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #369, stop:1 #147);"
                                "color: white;"
                    "}")
        pibox.addWidget(self.pList)

        # MOTOR LIST
        dbox = QVBoxLayout()
        gb2 = QGroupBox('MOTOR LIST ')
        self.mList = QListWidget()
        self.mList.setStyleSheet(
                    "QListWidget{"
                               "font: 8pt Comic Sans MS;"
                               "}"
                    "QListWidget::item {"
                                "padding: 2px;"
                                "}"
                    "QListWidget::item:selected {"
                                "background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #369, stop:1 #147);"
                                "color: white;"
                    "}")
        dbox.addWidget(self.mList)
        # MOTOR 현 상태 부분
        qbox = QHBoxLayout()
        mLabel = QLabel('MOTOR STATE : ')
        qbox.addWidget(mLabel)
        self.mLabel2 = QLabel()
        qbox.addWidget(self.mLabel2)
        mLabel.setStyleSheet("color: green;"
                              "background-color: white;"
                              "border-style: dashed;"
                              "border-width: 3px;"
                              "border-color: green")
        self.mLabel2.setStyleSheet("color: green;"
                              "background-color: white;"
                              "border-style: dashed;"
                              "border-width: 3px;"
                              "border-color: green")
        dbox.addLayout(qbox)
        
        # add
        gb0.setLayout(lpbox)
        box.addWidget(gb0)
 
        gb1.setLayout(pibox)
        box.addWidget(gb1)
 
        gb2.setLayout(dbox)
        box.addWidget(gb2)
        
        gb.setLayout(box)

#----------------------------------------layout
        
        gb = QGroupBox()
        sbox.addWidget(gb)
        box = QVBoxLayout()
        gb.setStyleSheet("QGroupBox  {"
                            "border: 1px solid gray;"
                            "border-color:" #FF17365D;
                            "margin-top27px;"
                            "font-size: 14px;"
                            "border-radius: 15px;"
                            "}")

        vabox = QVBoxLayout()
        self.canvas = MyMplCanvas(self, width=10, height=8, dpi=100)
        vabox.addWidget(self.canvas)
        self.setLayout(vabox)

        self.x = np.arange(50)
        self.y = np.ones(50, dtype=np.float)*np.nan
        self.line, = self.canvas.axes.plot(self.x, self.y, animated=True, lw=2)

        self.x2 = np.arange(50)
        self.y2 = np.ones(50, dtype=np.float)*np.nan
        self.line2, = self.canvas.axes2.plot(self.x2, self.y2, animated=True,color='red', lw=2)
        self.ani = animation.FuncAnimation(self.canvas.figure, self.update_line, blit=True, interval=1000)
        self.ani2 = animation.FuncAnimation(self.canvas.figure, self.update_line2, blit=True, interval=1000)

        gb.setLayout(vabox)

#--------------------------

        # 전체 배치
        vbox = QVBoxLayout()
        vbox.addLayout(sbox)
        self.setLayout(vbox)

    # TEMP ADD LIST
    @pyqtSlot(list)
    def updateTe(self, status):
        tempD = str(status[1])
        humiD = str(status[2])
        tStr = status[0].strftime('%Y-%m-%d %H:%M:%S') + " | TEM : " + tempD + "℃ | HUM : " + humiD + "%"
        self.tList.addItem(QListWidgetItem(tStr))
        self.tList.setCurrentRow(status[3]-1)
    # NOW TIME
    @pyqtSlot(str)
    def updateTi(self, status):
        self.tiLabel2.setText(status)
    # PIR ADD LIST
    @pyqtSlot(list)
    def updatePi(self, status):
        self.pList.addItem(QListWidgetItem(status[0]))
        self.pList.setCurrentRow(status[1]-1)
    # ULTRA ADD LIST
    @pyqtSlot(list)
    def updateUl(self, status):
        self.uList.addItem(QListWidgetItem(status[0]))
        self.uList.setCurrentRow(status[1]-1)
    #Graph
    def update_line(self, i):
        sql = "SELECT * FROM temhumDB ORDER BY TIME DESC limit 1"
        curs.execute(sql)
        row = curs.fetchall()
        db.commit()
        y = float(row[0][1])
        old_y = self.line.get_ydata()
        new_y = np.r_[old_y[1:], y]
        self.line.set_ydata(new_y)
        #self.line.set_ydata(y)
        return [self.line]
    #Graph
    def update_line2(self, i):
        sql = "SELECT * FROM temhumDB ORDER BY TIME DESC limit 1"
        curs.execute(sql)
        row = curs.fetchall()
        db.commit()
        y2 = float(row[0][2])
        old_y2 = self.line2.get_ydata()
        new_y2 = np.r_[old_y2[1:], y2]
        self.line2.set_ydata(new_y2)
        return [self.line2]
        # self.line.set_ydata(y)

# Graph GUI
class MyMplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.axes = fig.add_subplot(211, xlim=(0, 200), ylim=(0, 30))
        self.axes2 = fig.add_subplot(212, xlim=(0, 200), ylim=(0, 100))
        self.axes.set(title='TEM', ylabel='℃')
        self.axes2.set(title='HUM', ylabel='%')

        self.compute_initial_figure()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
    def compute_initial_figure(self):
        pass

# Operator
class CWidget(QObject):
    sig_str = pyqtSignal()
    send_sig = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        # 객체 생성
        self.gui = Window()
        # LED LIST
        lList = self.ledList()
        lCount = self.ledCount()
        if lCount > 0:
            for i in range(0, lCount):
                self.gui.llist.addItem(QListWidgetItem(lList[i]))

        # LED Label
        lS = self.ledState()
        self.gui.ledLabel2.setText(lS)

        # TEMP LIST
        str = self.temList()
        tlCount = self.tCount()
        if tlCount > 0:
            for i in range(0, tlCount):
                self.gui.tList.addItem(QListWidgetItem(str[i]))

        # PIR LIST
        str3 = self.pirList()
        count3 = self.pirCount()
        if count3 > 0:
            for i in range(0, count3):
                self.gui.pList.addItem(QListWidgetItem(str3[i]))

        # ULTRA LIST
        str4 = self.uList()
        ulCount = self.uCount()
        if ulCount > 0:
            for i in range(0, ulCount):
                self.gui.uList.addItem(QListWidgetItem(str4[i]))

        # MOTOR LIST
        str5 = self.mList()
        mlCount = self.mCount()
        if mlCount > 0:
            for i in range(0, mlCount):
                self.gui.mList.addItem(QListWidgetItem(str5[i]))

        # MOTOR Label
        mS = self.mState()
        self.gui.mLabel2.setText(mS)

        # TEMP Thread
        self.worker = Worker()
        self.worker.start()
        # TIME THREAD
        self.worker2 = Worker2()
        self.worker2.start()
        # PIR THREAD
        self.worker4 = Worker4()
        self.worker4.start()
        # ULTRA THREAD
        self.worker7 = Worker7()
        self.worker7.start()
        # spiCds
        self.worker8 = Worker8()
        self.worker8.start()

        # Signal
        self._connectSignals()
        # View
        self.gui.show()

    def _connectSignals(self):
        # LED
        self.gui.onBtn.clicked.connect(self.ledOn)
        self.gui.offBtn.clicked.connect(self.ledOff)
        # TEMP
        self.worker.sig_strs.connect(self.gui.updateTe)
        # MOTOR
        self.gui.pBtn.clicked.connect(self.mP)
        self.gui.nBtn.clicked.connect(self.mN)
        self.gui.sBtn.clicked.connect(self.mS)
        # TIME
        self.worker2.sig_strs2.connect(self.gui.updateTi)
        # 8BIT LED
        self.gui.useBtn.clicked.connect(self.bitUse)
        self.gui.noBtn.clicked.connect(self.bitNo)
        self.gui.lonBtn.clicked.connect(self.bitOn)
        self.gui.loffBtn.clicked.connect(self.bitOff)
        # PIR
        self.worker4.sig_strs4.connect(self.gui.updatePi)
        # STEP MOTOR
        self.gui.sonBtn.clicked.connect(self.sonBt)
        self.gui.soffBtn.clicked.connect(self.soffBt)
        # SERV MOTOR
        self.gui.svonBtn.clicked.connect(self.svonBt)
        self.gui.svoffBtn.clicked.connect(self.svoffBt)
        # ULTRA
        self.worker7.sig_strs7.connect(self.gui.updateUl)

    # Led 켜기
    def ledOn(self):
        GPIO.output(led1, GPIO.HIGH)
        GPIO.output(led2, GPIO.HIGH)
        sql = "INSERT INTO ledDB (Time, led) VALUES(default, 'ON')"
        curs.execute(sql)
        self.gui.onBtn.setEnabled(False)
        self.gui.offBtn.setEnabled(True)
        # 버튼 선택시 LED 추가로 띄우기
        sql2 = "SELECT * FROM ledDB ORDER BY TIME DESC limit 1"
        curs.execute(sql2)
        rows = curs.fetchall()
        lStr = rows[0][0].strftime('%Y-%m-%d %H:%M:%S') + " | LED State : " + rows[0][1]
        self.updateLed(lStr)
        db.commit()
    # Led 끄기
    def ledOff(self):
        GPIO.output(led1, GPIO.LOW)
        GPIO.output(led2, GPIO.LOW)
        sql = "INSERT INTO ledDB (Time, led) VALUES(default, 'OFF')"
        curs.execute(sql)
        self.gui.offBtn.setEnabled(False)
        self.gui.onBtn.setEnabled(True)
        # 버튼 선택시 LED 추가로 띄우기
        sql2 = "SELECT * FROM ledDB ORDER BY TIME DESC limit 1"
        curs.execute(sql2)
        rows = curs.fetchall()
        lStr = rows[0][0].strftime('%Y-%m-%d %H:%M:%S') + " | LED State : " + rows[0][1]
        self.updateLed(lStr)
        db.commit()
    # Led 리스트
    def ledList(self):
        sql = "SELECT * FROM ledDB"
        curs.execute(sql)
        rows = curs.fetchall()
        count = self.ledCount()
        str = []
        for i in range(0, count):
            if rows[i][1] == "ON":
                str.append(rows[i][0].strftime('%Y-%m-%d %H:%M:%S') + " | LED State : " + rows[i][1])
            else:
                str.append(rows[i][0].strftime('%Y-%m-%d %H:%M:%S') + " | LED State : " + rows[i][1])
        return str
    # Led 정보 갯수
    def ledCount(self):
        sql = "SELECT COUNT(*) FROM ledDB"
        curs.execute(sql)
        count = curs.fetchall()
        return count[0][0]
    # Led 현 상태
    def ledState(self):
        # LED 현 상태 부분
        sql = "SELECT * FROM ledDB ORDER BY TIME DESC limit 1"
        curs.execute(sql)
        rows = curs.fetchall()
        if rows[0][1] == "ON":
            self.gui.onBtn.setEnabled(False)
            return "ON"
        else:
            self.gui.offBtn.setEnabled(False)
            return "OFF"
    # Led 리스트 업데이트
    def updateLed(self, state):
        #추가한 값 뿌려주기
        self.gui.llist.addItem(QListWidgetItem(state))
        self.gui.llist.setCurrentRow(self.ledCount()-1)
        ledSt = self.ledState()
        self.gui.ledLabel2.setText(ledSt) 
    
    # 온습도 리스트
    def temList(self):
        sql11 = "SELECT * FROM temhumDB"
        curs.execute(sql11)
        rows1 = curs.fetchall()
        sql22 = "SELECT COUNT(*) FROM temhumDB"
        curs.execute(sql22)
        count1 = curs.fetchall()
        str1 = []
        for i in range(0, count1[0][0]):
            str1.append(rows1[i][0].strftime('%Y-%m-%d %H:%M:%S') + " | TEM : " + rows1[i][1] + "℃ | HUM : " + rows1[i][2] + "%")
        return str1
    # 온습도 정보 갯수
    def tCount(self):
        sql = "SELECT COUNT(*) FROM temhumDB"
        curs.execute(sql)
        count = curs.fetchall()
        return count[0][0]
    
    # M순방향
    def mP(self):
        sql = "INSERT INTO motorDB (Time, motor) VALUES(default, '순방향')"
        curs.execute(sql)
        sql2 = "SELECT * FROM motorDB ORDER BY TIME DESC limit 1"
        curs.execute(sql2)
        rows = curs.fetchall()
        mStr = rows[0][0].strftime('%Y-%m-%d %H:%M:%S') + " | M 상태 : " + rows[0][1]
        self.updateM(mStr)
        db.commit()
        self.gui.pBtn.setEnabled(False)
        self.gui.nBtn.setEnabled(False)
        pwm.start(0)
        pwm.ChangeDutyCycle(30)
        GPIO.output(negativePin, GPIO.LOW)
        GPIO.output(positivePin, GPIO.HIGH)
    # M역방향
    def mN(self):
        sql = "INSERT INTO motorDB (Time, motor) VALUES(default, '역방향')"
        curs.execute(sql)
        sql2 = "SELECT * FROM motorDB ORDER BY TIME DESC limit 1"
        curs.execute(sql2)
        rows = curs.fetchall()
        mStr = rows[0][0].strftime('%Y-%m-%d %H:%M:%S') + " | M 상태 : " + rows[0][1]
        self.updateM(mStr)
        db.commit()
        self.gui.pBtn.setEnabled(False)
        self.gui.nBtn.setEnabled(False)
        pwm.start(0)
        pwm.ChangeDutyCycle(30)
        GPIO.output(positivePin, GPIO.LOW)
        GPIO.output(negativePin, GPIO.HIGH)
    # M정지
    def mS(self):
        sql = "INSERT INTO motorDB (Time, motor) VALUES(default, '정지')"
        curs.execute(sql)
        sql2 = "SELECT * FROM motorDB ORDER BY TIME DESC limit 1"
        curs.execute(sql2)
        rows = curs.fetchall()
        mStr = rows[0][0].strftime('%Y-%m-%d %H:%M:%S') + " | M 상태 : " + rows[0][1]
        self.updateM(mStr)
        db.commit()
        self.gui.pBtn.setEnabled(True)
        self.gui.nBtn.setEnabled(True)
        GPIO.output(negativePin, GPIO.LOW)
        GPIO.output(positivePin, GPIO.LOW)
        pwm.stop()

    # 8Bit Led ON
    def bitOn(self):
        global bitFlag
        bitFlag = 2
        self.gui.lonBtn.setEnabled(False)
        self.gui.loffBtn.setEnabled(True)
        self.gui.noBtn.setEnabled(False)
    # 8bit Led OFF
    def bitOff(self):
        global bitFlag
        bitFlag = 3
        self.gui.loffBtn.setEnabled(False)
        self.gui.lonBtn.setEnabled(True)
        self.gui.noBtn.setEnabled(True)
    # 8bit LED 사용버튼
    def bitUse(self):
        global stopFlag
        self.worker3 = Worker3()
        stopFlag = 0
        if stopFlag == 0:
            self.worker3.start()
        self.gui.useBtn.setEnabled(False)
        self.gui.noBtn.setEnabled(True)
        self.gui.lonBtn.setEnabled(True)
    # 8 bit LED 미사용버튼
    def bitNo(self):
        global stopFlag
        stopFlag = 1
        self.gui.useBtn.setEnabled(True)
        self.gui.noBtn.setEnabled(False)
        self.gui.lonBtn.setEnabled(False)
        self.gui.loffBtn.setEnabled(False)
        return stopFlag
    
    # PIR COUNT
    def pirCount(self):
        sql = "SELECT COUNT(*) FROM pirDB"
        curs.execute(sql)
        count = curs.fetchall()
        return count[0][0]
    # PIR 감지리스트
    def pirList(self):
        sql = "SELECT * FROM pirDB"
        curs.execute(sql)
        row = curs.fetchall()
        count = self.pirCount()
        str = []
        for i in range(0, count):
            str.append(row[i][0].strftime('%Y-%m-%d %H:%M:%S') + " | " + row[i][1])
        return str
    
    # STEP ON
    def sonBt(self):
        global stopStep
        self.worker5 = Worker5()
        stopStep = 0
        if stopStep == 0:
            self.worker5.start()
        self.gui.sonBtn.setEnabled(False)
        self.gui.soffBtn.setEnabled(True)
    # STEP M OFF
    def soffBt(self):
        global stopStep
        stopStep = 1
        self.gui.sonBtn.setEnabled(True)
        self.gui.soffBtn.setEnabled(False)
    
    # SERV ON
    def svonBt(self):
        global stopServ
        self.worker6 = Worker6()
        stopServ = 0
        if stopServ == 0:
            self.worker6.start()
        self.gui.svonBtn.setEnabled(False)
        self.gui.svoffBtn.setEnabled(True)
    # SERV M OFF
    def svoffBt(self):
        global stopServ
        stopServ = 1
        self.gui.svonBtn.setEnabled(True)
        self.gui.svoffBtn.setEnabled(False)
        
    # ULTRA COUNT
    def uCount(self):
        sql = "SELECT COUNT(*) FROM ultraDB"
        curs.execute(sql)
        count = curs.fetchall()
        return count[0][0]
    # ULTRA 감지리스트
    def uList(self):
        sql = "SELECT * FROM ultraDB"
        curs.execute(sql)
        row = curs.fetchall()
        count = self.uCount()
        str = []
        for i in range(0, count):
            str.append(row[i][0].strftime('%Y-%m-%d %H:%M:%S') + " | DISTANCE : " + row[i][1])
        return str    
        
    # Motor 리스트
    def mList(self):
        sql = "SELECT * FROM motorDB"
        curs.execute(sql)
        rows = curs.fetchall()
        count = self.mCount()
        str = []
        for i in range(0, count):
            str.append(rows[i][0].strftime('%Y-%m-%d %H:%M:%S') + " | M 상태 : " + rows[i][1])
        return str
    # Motor 정보 갯수
    def mCount(self):
        sql = "SELECT COUNT(*) FROM motorDB"
        curs.execute(sql)
        count = curs.fetchall()
        return count[0][0]
    # Motor 현 상태
    def mState(self):
        sql = "SELECT * FROM motorDB ORDER BY TIME DESC limit 1"
        curs.execute(sql)
        rows = curs.fetchall()
        if rows[0][1] == "순방향":
            return "순방향"
        elif rows[0][1] == "역방향":
            return "역방향"
        else:
            return "정지"
    # Motor 리스트 업데이트
    def updateM(self, state):
        #추가한 값 뿌려주기
        self.gui.mList.addItem(QListWidgetItem(state))
        self.gui.mList.setCurrentRow(self.mCount()-1)
        mSt = self.mState()
        self.gui.mLabel2.setText(mSt)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    example = CWidget(app)
#    w = CWidget()
#    w.show()
    sys.exit(app.exec_())
