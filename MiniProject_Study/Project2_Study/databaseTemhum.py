import smbus
import time
import pymysql

db = pymysql.connect(host="localhost", user="root", password="password", db="sensordb")

curs = db.cursor()

#ePin = 12
#pPin = 4
#nPin = 25

#GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)

sht20_addr = 0x40

SHT20_CMD_MEASURE_TEMP = 0xf3
SHT20_CMD_MEASURE_HUMI = 0xf5
SHT20_SOFT_RESET = 0xfe

bus = smbus.SMBus(1)

data = [0, 0]

try:
    bus.write_byte(sht20_addr, SHT20_SOFT_RESET)
    time.sleep(0.05)
    while True:
        bus.write_byte(sht20_addr, SHT20_CMD_MEASURE_TEMP)
        time.sleep(0.26)
        for i in range(2):
            data[i] = bus.read_byte(sht20_addr) # data[0]에 binary 값을 8bit 저장하고 다음 1번에 binary값 8bit 저장 
            print(bus.read_byte(sht20_addr))
            print(data[0], "/", data[1])
        value = data[0] << 8 | data[1]  # shift 시킨 후 value 값에 최종 binary값 저장(print로 찍으면 decimal값 저장)
        print(value)
        temp = - 46.84 + 175.72 / 65536 * int(value)

        bus.write_byte(sht20_addr, SHT20_CMD_MEASURE_HUMI)
        time.sleep(0.26)

        for i in range(2):
            data[i] = bus.read_byte(sht20_addr)
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
        curs.execute(sql)
        db.commit()

        # 터미널창에서 확인
        print("Temp : %.2fC\t Humi: %.2f %%" % (float(temp), float(humi)))

        # 10초마다 데이터베이스에 집어넣음
        time.sleep(10)
except KeyboardInterrupt:
    pass
