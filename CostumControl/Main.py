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



    if (leftDistanceTravelledBack >= 1.75):
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
    threading.Timer(0.5, pingThread).start()
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
    check=0
    if distance ==1:
        distance += 0.50
    print("distance " + str(distance))

    sensorData = dict()
    
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
    m.readSensors.readAll()
   
    while True:
        try:
            sensorData=m.readSensors.readAll()
            check = calculateDistance(1,sensorData["EncoderPositionCountLeftFront"],sensorData["EncoderPositionCountLeftRear"],sensorData["EncoderPositionCountRightFront"],sensorData["EncoderPositionCountRightRear"])
            # check=sensorData["EncoderPositionCountLeft"]
            # print("CHECK" + str(check))

            if check == False:
                exit()


            # if(distance <= check):
            #     print("STOP")
            #     exit()
        except(KeyError):
            print("error?")
        


def tryStuff():
    try: 
        pingThread()
        atexit.register(exitHandler)
        m.emergency_stop_release()
        drive(1)      
        # turnRobot(3.14)
        # nextmove= getNextMove()   
    finally:
        exitHandler()


if __name__ == "__main__":
    print("STARTING PROGRAM")
    
    
    tryStuff()



   

    # nextmove=getNextMove()

    # index =0
    # while (nextmove != False):
    #     lastMoveID=nextmove["OrderNr"]
    #     if (sys.argv[1] == "N" and index ==0):
            
    #         # ignore the direction , this means robot has been manually reset
    #         #  does not need to be checked if application doesn't run for the first time

    #         pass
    #     elif(sys.argv[1] =="Y" or index >=1):
    #         # do as normal
    #         try:
    #             if (nextmove["Direction"] =="N"):
    #                 # just drive ,no direction changes

                
    #                 pingThread()
    #                 atexit.register(exitHandler)
    #                 m.emergency_stop_release()
    #                 # drive(2)
    #             else:
    #                 # change direction,then drive
    #                 turnRobot(3.14)
    #                 drive(2)
                  
    #         finally:
    #             exitHandler()
    #     index +1
    #     nextmove= getNextMove() 
    
    
    
        

    
