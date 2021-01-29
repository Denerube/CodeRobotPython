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
  
    leftFrontEncoderStart=beginData["EncoderPositionCountLeftFront"]
    leftBackEncoderStart=beginData["EncoderPositionCountLeftRear"]
    RightFrontEncoderStart=beginData["EncoderPositionCountRightFront"]
    RightBackEncoderStart=beginData["EncoderPositionCountRightRear"]
 
    leftDifferenceFront=float(LeftFrontencoderAbs)-float(leftFrontEncoderStart)
    leftDifferenceBack=float(leftBackEncoderAbs)-float(leftBackEncoderStart)
    

    RightDifferenceFront=float(RightFrontencoderAbs)-float(RightFrontEncoderStart)
    RightDifferenceBack=float(RightBackEncoderAbs)-float(RightBackEncoderStart)

    
    leftDistanceTravelledFront=leftDifferenceFront  * WheelCirc /310
    leftDistanceTravelledBack=leftDifferenceBack  * WheelCirc /310
    RightDistanceTravelledFront =RightDifferenceFront  * WheelCirc /310
    RightDistanceTraveledBack=RightDifferenceBack  * WheelCirc /310

    return leftDistanceTravelledBack



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
    print("closing program")
    m.emergency_stop()
    m.close_connection()
   
def turnRobot (target):
    m.generalControls.send_cmd("SYS CAL")
    sensorData = m.readSensors.readAll()
    start = sensorData["YAW"]
    yaw = start
    m.emergency_stop_release()
    m.turn_left(200,0)
    target -= 0.1

    while yawdiff(start, yaw) < target:
        try:     
            sensorData = m.readSensors.readAll()
            yaw = sensorData["YAW"]
            # print ("YAW: " + str(yaw))
        except(KeyError):
            pass #print("keyerror")

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
    print("getting start values")
    
    for x in range(1000):
        sensorData=m.readSensors.readAll()
        try:
            leftFrontEncoderStart = float(sensorData["EncoderPositionCountLeftFront"])
            leftBackEncoderStart=float(sensorData["EncoderPositionCountLeftRear"])
            RightFrontEncoderStart=float(sensorData["EncoderPositionCountRightFront"])
            RightBackEncoderStart=float(sensorData["EncoderPositionCountRightRear"])
            # print("DONE?")
        except(KeyError,ValueError):
            pass# print("KEYERROR BIJ INIT")
    StartValuesArray ={ "EncoderPositionCountLeftFront" : leftFrontEncoderStart,
                        "EncoderPositionCountLeftRear" : leftBackEncoderStart,
                        "EncoderPositionCountRightFront":RightFrontEncoderStart,
                        "EncoderPositionCountRightRear":RightBackEncoderStart
                        }
    print("start values done")
    return StartValuesArray

def readDataPutInQue(queueIn:Queue,queueOut:Queue,runThreads:threading.Event):
    while runThreads.is_set():
        # print("executed function")
        try:
            sensorData=m.readSensors.readAll()
            # print(sensorData["MotorDriverBoardPowerMainFront"])
            queueOut.put(sensorData)
        except(ValueError):
            pass

def drive(queueIn:Queue,QueueOther:Queue,pingThread,runPingThread,runDriveInStraightLine:threading.Event):
    print("start drive")
    index=0
    isFirst=True
    sensorData=dict()
    begindata=dict()
    

    while 1:
        

        sensorData=queueIn.get()
        if isFirst:
            print("BEGINSENSORLEFTFRONT {0}".format(sensorData["EncoderPositionCountLeftFront"]))
            isFirst=False

        if  runDriveInStraightLine.is_set():
            if (index ==0):
                print("should drive after this?")
                startData=queueOtherData.get()    
                beginData=startData["encoderStartValues"]
                TargetDistance=startData["TargetDistance"]-0.05
                index +=1
                print("TARGET {0}".format(TargetDistance))
                m.emergency_stop_release()
                m.go_forward(100,10)
                # sleep(0.4)
                pingThread.start()
            try:
                if TargetDistance <= calculateDistance(TargetDistance,beginData,sensorData["EncoderPositionCountLeftFront"],sensorData["EncoderPositionCountLeftRear"],sensorData["EncoderPositionCountRightFront"],sensorData["EncoderPositionCountRightRear"]):
                    m.stop()
                    print("STOP")
                    index=0
                    sleep(2)
                    sensorData=queueIn.get()
                    print("ENDSENSORLEFTFRONT {0}".format(sensorData["EncoderPositionCountLeftFront"]))
                    DistanceTravelled=calculateDistance(TargetDistance,beginData,sensorData["EncoderPositionCountLeftFront"],sensorData["EncoderPositionCountLeftRear"],sensorData["EncoderPositionCountRightFront"],sensorData["EncoderPositionCountRightRear"])
                    print(DistanceTravelled)
                    runPingThread.clear()
                    pingThread.join()
                    runDriveInStraightLine.clear()
                        
                        
                    
            except():
                print("error in drive function")
        else:
            pass #print("no data?")

            
            


def pingThread(queueOtherData:Queue,runThreads:threading.Event,runPingthread:threading.Event):
    while runThreads.is_set() and runPingthread.is_set():
        m.generalControls.ping()
        sleep(0.3)





if __name__ == "__main__":
    print("STARTING PROGRAM")
    atexit.register(exitHandler)
    
    # encoderStartValues=getStartEncoderPositions()
    queueOtherData =Queue()
    runThreads= threading.Event()
    runDriveInStraightLine=threading.Event()
    runTurnOnTheSpot=threading.Event()
    runThreads.set()
    runPingThread=threading.Event()
    runPingThread.set()
    encoderStartValues=getStartEncoderPositions()
    startObject= {
                    "encoderStartValues":encoderStartValues,
                    "TargetDistance":1
                            }

   
    queueSensorData = Queue() # output queue of the read thread,read thread will signal here when it is done with the drive command
    pingThread=Thread(target=pingThread,args=(queueOtherData,runThreads,runPingThread))
    readDataThread = Thread(target=readDataPutInQue, args=(queueOtherData, queueSensorData,runThreads))
    CalculateDatathread = Thread(target=drive,args=(queueSensorData,queueOtherData,pingThread,runPingThread,runDriveInStraightLine))
    # drive(queueSensorData,queueOtherData,startObject,pingThread,runPingThread)
    

    


   
    
    # queueIn1.put(startObject)
    readDataThread.start()
    sleep(5)
    CalculateDatathread.start()
    txtChoice =input("Do you want to get and execute the next command ? (Y/N),press Q to exit inmediatly")
    txtChoice=txtChoice.upper()

    while txtChoice !="Q": 
        txtChoice=txtChoice.upper()
        if txtChoice =="N":
            print("closing program")
            runThreads.clear()
            readDataThread.join()
            pingThread.join()
            exit()
        elif txtChoice =="Q":
            print("closing program")
            runThreads.clear()
            readDataThread.join()
            pingThread.join()
            exit()
        elif txtChoice =="Y":
            try:
                queueOtherData.put(startObject)
                runDriveInStraightLine.set()
                while runDriveInStraightLine.is_set():
                    pass

            except (KeyboardInterrupt):
                print("exitting via keyboard")
                runThreads.clear()
                runPingThread.clear()
                readDataThread.join()
                pingThread.join()
                exit()
            finally:
                print("DONE with command")
                exitHandler()
                txtChoice =input("Do you want to get and execute the next command ? (Y/N)")
               
        else:
            txtChoice =input("invalid input")




    
    
    
        

    
