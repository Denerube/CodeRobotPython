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
# leftFrontEncoderStart = 0
# leftBackEncoderStart =0
# RightFrontEncoderStart =0
# RightBackEncoderStart =0


# //van 1 - x voor volgorde -> orderNr

def calculateDistance(target,beginData,LeftFrontencoderAbs,leftBackEncoderAbs,RightFrontencoderAbs,RightBackEncoderAbs):
    # self.sensorValues["EncoderPositionCountLeft"+p]=values[0]
    # self.sensorValues["EncoderPositionCountRight"+p]=values[1]
    # UNDER THIS is an example of the begindata you recieve
    #  StartValuesArray ={ "EncoderPositionCountLeftFront" : leftFrontEncoderStart,
    #                     "EncoderPositionCountLeftRear" : leftBackEncoderStart,
    #                     "EncoderPositionCountRightFront":RightFrontEncoderStart,
    #                     "EncoderPositionCountRightRear":RightBackEncoderStart
    #                     }
    leftFrontEncoderStart=beginData["EncoderPositionCountLeftFront"]
    leftBackEncoderStart=beginData["EncoderPositionCountLeftRear"]
    RightFrontEncoderStart=beginData["EncoderPositionCountRightFront"]
    RightBackEncoderStart=beginData["EncoderPositionCountRightRear"]
 
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

def getStartEncoderPositions():
    
    for x in range(1000):
        sensorData=m.readSensors.readAll()
        try:
            leftFrontEncoderStart = float(sensorData["EncoderPositionCountLeftFront"])
            leftBackEncoderStart=float(sensorData["EncoderPositionCountLeftRear"])
            RightFrontEncoderStart=float(sensorData["EncoderPositionCountRightFront"])
            RightBackEncoderStart=float(sensorData["EncoderPositionCountRightRear"])
            print("DONE?")
        except(KeyError):
            print("KEYERROR BIJ INIT")
    StartValuesArray ={ "EncoderPositionCountLeftFront" : leftFrontEncoderStart,
                        "EncoderPositionCountLeftRear" : leftBackEncoderStart,
                        "EncoderPositionCountRightFront":RightFrontEncoderStart,
                        "EncoderPositionCountRightRear":RightBackEncoderStart
                        }
    return StartValuesArray




def drive(queue1In:Queue,queue2Out:Queue):
    sensorData=dict()
    begindata=dict()
    doCalc= False
    TargetDistance=1

    while True:
        if not queue1In.empty:
            # get data and do calc
            var = queue1In.get()
            doCalc=True
            begindata=var["encoderStartValues"]
            TargetDistance=var["TargetDistance"]

        sensorData=m.readSensors.readAll()
        if doCalc:
            try:
                check = calculateDistance(TargetDistance,begindata,sensorData["EncoderPositionCountLeftFront"],sensorData["EncoderPositionCountLeftRear"],sensorData["EncoderPositionCountRightFront"],sensorData["EncoderPositionCountRightRear"])
                if check == False:
                    print("STOP")
                    doCalc=False
                    exit()
            except(KeyError):
                print("keyerror in main")
                pass





if __name__ == "__main__":
    print("STARTING PROGRAM")
    
    encoderStartValues=getStartEncoderPositions()
    queueIn = [Queue(), Queue(), Queue()]
    queueOut = Queue() # output queue of the read thread,read thread will signal here when it is done with the drive command

    #readDataThread1 = Thread(target=drive, args=(queueIn[0], queueOut))
    #readDataThread2 = Thread(target=drive, args=(queueIn[1], queueOut))
    #readDataThread3 = Thread(target=drive, args=(queueIn[2], queueOut))

    startObject= {
        "encoderStartValues":encoderStartValues,
        "TargetDistance":1
    }

    readDataThread = []

    for x in range(0, len(queueIn) - 1):
        readDataThread.append( Thread(target=drive, args=(queueIn[x], queueOut)))
        queueIn[x].put(startObject)
        readDataThread[x].start()

    try:
        atexit.register(exitHandler)
        pingThread()
        m.go_forward(100,10)
    finally:
        exitHandler()

        



   

    # nextmove=getNextMove()

    
    
    
        

    
