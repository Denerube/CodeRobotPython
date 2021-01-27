import logging
from threading import Thread
from queue import Queue 
from time import time, sleep
import time
import atexit
import threading
import math
import sys
import json
import requests
from move_controls import Controls
from general_controls import GeneralControls

m=Controls()
sensorData=dict()
instructions=[]
currentHeading="N"
url="https://ai-4x4-api.herokuapp.com/plsSendNext"
lastMoveID=0
moveCommand = { "OrderNr" : 0 , "Direction" : "", "Afstand" : 0 }
JsonFileName="data.txt"
WheelCirc=0.27*math.pi
leftFrontEncoderStart = 0
leftBackEncoderStart =0
RightFrontEncoderStart =0
RightBackEncoderStart =0


# //van 1 - x voor volgorde -> orderNr

def calculateDistance(target,LeftFrontencoderAbs,leftBackEncoderAbs,RightFrontencoderAbs,RightBackEncoderAbs):
    # self.sensorValues["EncoderPositionCountLeft"+p]=values[0]
    # self.sensorValues["EncoderPositionCountRight"+p]=values[1]
 
    leftDifferenceFront=float(LeftFrontencoderAbs)-float(leftFrontEncoderStart)
    leftDifferenceBack=float(leftBackEncoderAbs)-float(leftBackEncoderStart)
    

    RightDifferenceFront=float(RightFrontencoderAbs)-float(RightFrontEncoderStart)
    RightDifferenceBack=float(RightBackEncoderAbs)-float(RightBackEncoderStart)

    
    leftDistanceTravelledFront=leftDifferenceFront  * WheelCirc /380
    leftDistanceTravelledBack=leftDifferenceBack  * WheelCirc /380
    RightDistanceTravelledFront =RightDifferenceFront  * WheelCirc /380
    RightDistanceTraveledBack=RightDifferenceBack  * WheelCirc /380



    if (leftDistanceTravelledBack >= 1):
        # m.stop()
        print("LEFT" + str(leftDistanceTravelledFront) + " BACK, " +str(leftDistanceTravelledBack))
        print("RIGHT" + str(RightDistanceTravelledFront) +" BACK, " + str(RightDistanceTraveledBack))
        return False
    else:
        return True


def writeToJsonFile(data):
    with open(JsonFileName, 'w') as json_file:
        json.dump(data, json_file)

def ReadFromJsonFile():
    with open(JsonFileName) as json_file:
        data = json.load(json_file)
    print (data)
    return data



def exitHandler():
    print("emergency stop")
    m.emergency_stop()
    m.close_connection()
    print("closing program")
    
            
def pingThread():
    t=threading.Timer(0.5, pingThread)
    t.start()
    m.generalControls.ping()

def turnRobot (target):
    m.generalControls.send_cmd("SYS CAL")
    sensorData = m.readSensors.readAll()
    start = sensorData["YAW"]
    yaw = start
    m.turn_left(200,0)
    target -= 0.1

    while yawdiff(start, yaw) < target:
        try:     
            sensorData = m.readSensors.readAll()
            yaw = sensorData["YAW"]
            print ("YAW: " + str(yaw))
        except(KeyError):
            print("keyerror")

    print("STOPPING")
    m.stop()

def yawdiff(start, yaw):
    if(start > 0 and yaw < 0):
        return (yaw + 2* 3.14) - start
    else:
        return yaw-start

def getNextMove():
    url="https://ai-4x4-api.herokuapp.com/plsSendNext"
    x=requests.get(url)
    data=x.json()
    print(data)
    writeToJsonFile(data)
    if "End" in data.keys() :
        print("END")
        return False
    else:
        print(data)
        return data


def drive(distance):
    if distance ==1:
        distance += 0.50
    print("distance " + str(distance))
    sensorData=dict()

    
    for x in range(1000):
        sensorData=m.readSensors.readAll()
        try:
            global leftFrontEncoderStart 
            leftFrontEncoderStart = float(sensorData["EncoderPositionCountLeftFront"])
            global leftBackEncoderStart
            # print(leftBackEncoderStart)
            leftBackEncoderStart=float(sensorData["EncoderPositionCountLeftRear"])
            global RightFrontEncoderStart
            RightFrontEncoderStart=float(sensorData["EncoderPositionCountRightFront"])
            global RightBackEncoderStart
            RightBackEncoderStart=float(sensorData["EncoderPositionCountRightRear"])
        except(KeyError):
            print("KEYERROR BIJ INIT")
    m.go_forward(100,10)
    while True:
        sensorData=m.readSensors.readAll()
        try:
            check = calculateDistance(1,sensorData["EncoderPositionCountLeftFront"],sensorData["EncoderPositionCountLeftRear"],sensorData["EncoderPositionCountRightFront"],sensorData["EncoderPositionCountRightRear"])
            if check == False:
                print("STOP")
                exit()
        except(KeyError):
            print("keyerror in main")
            pass


def tryStuff():
    try:
        atexit.register(exitHandler)
        pingThread()
        m.emergency_stop_release()
        drive(1)      
        # turnRobot(3.14)
        # nextmove= getNextMove()   
    finally:
        
        exitHandler()


if __name__ == "__main__":
    print("STARTING PROGRAM")
    # queue1In = Queue() # put the json data you get from the API in this queue
    # queue2Out = Queue() # output queue of the read thread,read thread will signal here when it is done with the drive command

    # readDataThread = Thread(target=readData, args=(queue1In, queue2Out))
    # readDataThread.start() 

    # t2 = Thread(target=modify_variable, args=(queue2, queue1))
    
    
    tryStuff()



   

    # nextmove=getNextMove()

    
    
    
        

    
