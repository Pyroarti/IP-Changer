#!/usr/bin/env python
# File name   : server.py
# Production  : picar-b
# Website     : www.adeept.com
# Author      : devin

import time
import threading
import move
import os
import info
import RPIservo

import functions
import robotLight
import switch
import socket

# websocket
import asyncio
import websockets

import json
import app

OLED_connection = 0

functionMode = 0
speed_set = 100
rad = 0.5
turnWiggle = 60

scGear = RPIservo.ServoCtrl()
scGear.moveInit()

P_sc = RPIservo.ServoCtrl()
P_sc.start()

T_sc = RPIservo.ServoCtrl()
T_sc.start()

H1_sc = RPIservo.ServoCtrl()
H1_sc.start()

H2_sc = RPIservo.ServoCtrl()
H2_sc.start()

G_sc = RPIservo.ServoCtrl()
G_sc.start()

modeSelect = 'PT'

init_pwm0 = scGear.initPos[0]
init_pwm1 = scGear.initPos[1]
init_pwm2 = scGear.initPos[2]
init_pwm3 = scGear.initPos[3]
init_pwm4 = scGear.initPos[4]

fuc = functions.Functions()
fuc.setup()
fuc.start()

curpath = os.path.realpath(__file__)
thisPath = os.path.dirname(curpath)

direction_command = 'no'
turn_command = 'no'

def servoPosInit():
    scGear.initConfig(0, init_pwm0, 1)
    P_sc.initConfig(1, init_pwm1, 1)
    T_sc.initConfig(2, init_pwm2, 1)
    H1_sc.initConfig(3, init_pwm3, 1)
    H2_sc.initConfig(3, init_pwm3, 1)
    G_sc.initConfig(4, init_pwm4, 1)

def replace_num(initial, new_num):
    newline = ""
    str_num = str(new_num)
    with open(os.path.join(thisPath, "RPIservo.py"), "r") as f:
        for line in f.readlines():
            if line.startswith(initial):
                line = initial + "%s" % (str_num + "\n")
            newline += line
    with open(os.path.join(thisPath, "RPIservo.py"), "w") as f:
        f.writelines(newline)

def wifi_check():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.27.27.192", 80))
        ipaddr_check = s.getsockname()[0]
        s.close()
        print(ipaddr_check)
    except:
        ap_threading = threading.Thread(target=ap_thread)
        ap_threading.setDaemon(True)
        ap_threading.start()
        time.sleep(1)

async def main_logic(websocket, path):
    await check_permit(websocket)
    await recv_msg(websocket)

if __name__ == '__main__':
    switch.switchSetup()
    switch.set_all_switch_off()
    move.setup()
    WS2812_mark = None

    HOST = ''
    PORT = 10223
    BUFSIZ = 1024
    ADDR = (HOST, PORT)

    flask_app = app.webapp()
    flask_app.startthread()

    try:
        robotlight_check = robotLight.check_rpi_model()
        if robotlight_check == 5:
            print("WS2812 officially does not support Raspberry Pi 5 for now.")
            WS2812_mark = 0
        else:
            print("WS2812 success!")
            WS2812_mark = 1
            WS2812 = robotLight.RobotWS2812()
            WS2812.start()
            WS2812.breath(70, 70, 255)
    except Exception as e:
        print('Error initializing WS2812:', e)

    while True:
        wifi_check()
        try:
            print("Starting WebSocket server...")
            start_server = websockets.serve(main_logic, '0.0.0.0', 8888)
            asyncio.get_event_loop().run_until_complete(start_server)
            print('Waiting for connection...')
            break
        except Exception as e:
            print("Error starting WebSocket server:", e)
            if WS2812_mark:
                WS2812.setColor(0, 0, 0)
        try:
            if WS2812_mark == 1:
                WS2812.setColor(0, 80, 255)
        except Exception as e:
            print("WS2812 error:", e)

    try:
        asyncio.get_event_loop().run_forever()
    except Exception as e:
        print("Error in event loop:", e)
        if WS2812_mark:
            WS2812.setColor(0, 0, 0)
        move.destroy()
