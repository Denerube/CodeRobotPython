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
from datetime import datetime

m=Controls()
sensorData=dict()
instructions=[]
currentHeading="N"
url="https://ai-4x4-api.herokuapp.com/plsSendNext"
lastMoveID=0
moveCommand = { "OrderNr" : 0 , "Direction" : "", "Afstand" : 0 }
JsonFileName="jsonData.json"
WheelCirc=0.27*math.pi
commandArray=[]
lastCommandId= 0
lastCommandIdfile="txtLastCmd.txt"
# leftFrontEncoderStart = 0
# leftBackEncoderStart =0
# RightFrontEncoderStart =0
# RightBackEncoderStart =0


# //van 1 - x voor volgorde -> orderNr


def WriteLastCommandIdToFile(cmdId):
    with open(lastCommandIdfile,'w') as text_file:
        text_file.write(str(cmdId))

def readLastCommandIdFromFile():
    dataLastCmdId=-1
    with open(lastCommandIdfile) as text_file:
        dataLastCmdId= text_file.read()
    return int(dataLastCmdId)



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
   
def turnRobot (target,pingThread:Thread,runPintThread:threading.Event,queueCommands:Queue,CommandoSend:threading.Event):
    turnLeftOrRight =0 # left = 1,right=2
    command= {
        "motorValue":200,
        "command": "null"
    }
    if (target > 0):
        target -=0.1
        turnLeftOrRight =2
    elif (target < 0):
        target +=0.1
        turnLeftOrRight =1
    
    
    print("turning to target {0}".format(target))
    m.generalControls.send_cmd("SYS CAL")
    sensorData = m.readSensors.readAll()    
    for i in range(1000):
        sensorData = m.readSensors.readAll()
    
    start = sensorData["YAW"]
    print("startpos {0}".format(start))
    yaw = start
    m.emergency_stop_release()
    lastYaw = ""
    

    # target -= 0.1


    if turnLeftOrRight ==1:
        runPintThread.set()
        # m.turn_left(200,0)
        command["motorValue"]=200
        command["command"]=m.turn_left
        queueCommands.put(command)
        CommandoSend.set()
        # print("WACHT")
        # print("WACHT")  
        # pingThread.start()
        sleep(1)
        while yawdiff(start, yaw) > target:
            try:
                sensorData = m.readSensors.readAll()
                yaw = sensorData["YAW"]
                if (start == yaw):
                    print("HIJ HEEFT NIET BEWOGEN")
                    command["motorValue"]=200
                    command["command"]=m.turn_left
                    queueCommands.put(command)
                    CommandoSend.set()
                    sleep(1)
            except(KeyError):
                print("keyerror during turning")
                
    elif turnLeftOrRight ==2:
        runPintThread.set()
        # m.turn_right(200,0)
        command["motorValue"]=200
        command["command"]=m.turn_right
        queueCommands.put(command)
        CommandoSend.set()
        # print("WACHT")
        # print("WACHT")
        # pingThread.start()      
        sleep(1)
        while yawdiff(start, yaw) < target:
            try:     
                sensorData = m.readSensors.readAll()
                yaw = sensorData["YAW"]
                if (start == yaw):
                    print("hij heeft niet bewogen")
                    command["motorValue"]=200
                    command["command"]=m.turn_right
                    queueCommands.put(command)
                    CommandoSend.set()
                    sleep(1)
               
                
                
            except(KeyError):
                print("keyerror during turning")
                

            

    print("STOPPING")
    CommandoSend.clear()
    m.emergency_stop()
    # runPintThread.clear()
    # pingThread.join()

def yawdiff(start, yaw):
    if(start > 0 and yaw < 0):
        # print("return 1: {0}".format(yaw + 2* 3.14))
        return (yaw + 2* 3.14) - start
    else:
        # print("return 2: {0}".format(yaw-start))
        return yaw-start

def getNextMove():
    url="https://ai-4x4-api.herokuapp.com/plsSendNext"
    x=requests.get(url)
    data=x.json()
    print(data)
    # writeToJsonFile(data)
    return data

def getAllMoves():
    data = getNextMove()
    commandArray.append(data)
    while 1:
        data = getNextMove()
        commandArray.append(data)
        if "End" in data.keys():
            break
    writeToJsonFile(commandArray)

    

    

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

def drive(queueIn:Queue,QueueOther:Queue,QueueCommands:Queue,pingThread,runPingThread,runDriveInStraightLine:threading.Event,runThreads:threading.Event,CommandoSend:threading.Event):
    print("start drive")
    index=0
    sensorData=dict()
    begindata=dict()
    
    # example of the command you get back
    command= {
        "motorValue":200,
        "command": "null"
    }
    
    

    while runThreads.is_set():
        sensorData=queueIn.get()

        if  runDriveInStraightLine.is_set():
            if (index ==0):
                print("driving straight")
                startData=queueOtherData.get()    
                beginData=startData["encoderStartValues"]
                TargetDistance=startData["TargetDistance"]-0.05
                index +=1
                command["motorValue"]=100
                command["command"]=m.go_forward
                m.emergency_stop_release()
                queueCommands.put(command)
                CommandoSend.set()

                # pingThread.start()
            try:
                if TargetDistance <= calculateDistance(TargetDistance,beginData,sensorData["EncoderPositionCountLeftFront"],sensorData["EncoderPositionCountLeftRear"],sensorData["EncoderPositionCountRightFront"],sensorData["EncoderPositionCountRightRear"]):
                    m.stop()
                    print("STOP")
                    index=0
                    sleep(2)
                    # runPingThread.clear()
                    # pingThread.join()
                    runDriveInStraightLine.clear()
    
            except():
                print("error in drive function")
        else:
            pass #print("no data?")

            
            


def pingThread(queueOtherData:Queue,runThreads:threading.Event,runPingthread:threading.Event):
    while runThreads.is_set() and runPingthread.is_set():
        m.generalControls.ping()
        sleep(0.3)

def CommandThreadFunction(commandQueue:Queue,runThreads:threading.Event,CommandoSend:threading.Event):

    # example of the command you get back
    # command= {
    #     "motorValue":200,
    #     "command": m.turn_left
    # }

    tping=round(time.time()*10,2)
    while runThreads.is_set():
        try:
            t=round(time.time()*10,2)
            if CommandoSend.is_set():
                command = commandQueue.get()
                # print("executing command: {0}".format(command))
                tping=round(time.time()*10,2)
                commandparam=command["motorValue"]
                commandFunction=command["command"]
                # m.emergency_stop_release()
                commandFunction(commandparam,0)
                CommandoSend.clear()
                sleep(0.3)
            elif (round(t-tping,2) >= 0.45):
                # print(t-tping)
                m.generalControls.ping()
                tping=round(time.time()*10,2)
        except:
            print("PING ERROR?")

       




if __name__ == "__main__":
    print("STARTING PROGRAM")
    atexit.register(exitHandler)
    
    # encoderStartValues=getStartEncoderPositions()
    queueOtherData =Queue()
    runThreads= threading.Event()
    runDriveInStraightLine=threading.Event()
    runThreads.set()
    runPingThread=threading.Event()
    CommandoSend=threading.Event()
    # runPingThread.set()
    # encoderStartValues=getStartEncoderPositions()
    startObject= {
                    "encoderStartValues":"",
                    "TargetDistance":1
                    
                            }

   
    queueSensorData = Queue() # output queue of the read thread
    queueCommands=Queue()
    pingThread=Thread(target=pingThread,args=(queueOtherData,runThreads,runPingThread))
    readDataThread = Thread(target=readDataPutInQue, args=(queueOtherData, queueSensorData,runThreads))
    CalculateDatathread = Thread(target=drive,args=(queueSensorData,queueOtherData,queueCommands,pingThread,runPingThread,runDriveInStraightLine,runThreads,CommandoSend))
    CommandThread=Thread(target=CommandThreadFunction,args=(queueCommands,runThreads,CommandoSend))
    readDataThread.start()
    sleep(5)
    CalculateDatathread.start()
    txtChoice=""
    CommandThread.start()
    commands=ReadFromJsonFile()
    
    while txtChoice !="Q":
        if lastCommandId == -1:
            print("stopping program")
            exit()
        lastCommandId=readLastCommandIdFromFile()
        commandToExecute=commands[lastCommandId-1]

        if lastCommandId !=1:
            print("last command executed: {0}".format(commands[lastCommandId-1]))
            txtrepeat=input("do you want to repeat this command?")
            if txtrepeat =="Y":
                commandToExecute=commandToExecute
            elif txtrepeat =="N":
                print("executing next command")
                lastCommandId +=1
                commandToExecute=commands[lastCommandId-1]


        print("executing: {0}".format(commandToExecute))

        if ("End" in commandToExecute.keys()):
            print("reached the end")
            lastCommandId =1
            WriteLastCommandIdToFile(lastCommandId)
            exit()

        txtChoice =input("Do you want to  execute the  command and start the program ? (Y/N),press Q to exit inmediatly")
        
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
            CalculateDatathread.join()
            # pingThread.join()
            exit()
        elif txtChoice =="Y":
            # check if turning or straight line
            WriteLastCommandIdToFile(lastCommandId)
           
            
            turnOrDriveStraigh:int #0= nothing, 1= drive straight,2=turn
            if commandToExecute["Direction"] != "North":
                turnOrDriveStraigh =2
            else:
                turnOrDriveStraigh =1
            
            # turnOrDriveStraigh=2
            # when turning
            if turnOrDriveStraigh == 2:
                turnDirection =""
                if commandToExecute["Direction"] =="East":
                    turnDirection=3.14/2
                elif commandToExecute["Direction"] =="West":
                    turnDirection= -3.14/2
                elif commandToExecute["Direction"] =="South":
                    turnDirection =3.14
                
                try:
                    turnRobot(turnDirection,pingThread,runPingThread,queueCommands,CommandoSend)
                    # pingThread.start()

                except (KeyboardInterrupt):
                    print("exitting via keyboard")
                    runThreads.clear()
                    readDataThread.join()
                    CalculateDatathread.join()
                    CommandThread.join()
                    # pingThread.join()
                    exit()
                finally:
                    print("DONE with turn command")
                    # runPingThread.clear()
                    # pingThread.join()
                    txtChoice =input("Do you want to go straight for {0}m or skip command,or redo command Y=yes, R=Redo,Q=Stop program, anything else= skip going straight".format(commandToExecute["Afstand"]))
                    txtChoice = txtChoice.upper()
                    if txtChoice =="R":
                        turnOrDriveStraigh =2
                    if txtChoice == "Y":
                        turnOrDriveStraigh =1
                        txtChoice=""
                    elif txtChoice =="Q":
                        txtChoice =="Q"
                    else:
                        turnOrDriveStraigh =0
                        txtChoice=""
            if turnOrDriveStraigh ==1:
            # when driving straigt
                try:
                    encoderStartValues=getStartEncoderPositions()
                    startObject["encoderStartValues"]=encoderStartValues
                    startObject["TargetDistance"]=commandToExecute["Afstand"]
                    queueOtherData.put(startObject)
                    runDriveInStraightLine.set()
                    while runDriveInStraightLine.is_set():
                        pass

                except (KeyboardInterrupt):
                    print("exitting via keyboard")
                    runThreads.clear()
                    readDataThread.join()
                    CalculateDatathread.join()
                    CommandThread.join()
                    exit()
                finally:
                    print("DONE with command")
                    runDriveInStraightLine.clear()
                    lastCommandId +=1
                    WriteLastCommandIdToFile(lastCommandId)
                    txtChoice =input("Do you want to get and execute the next command ? (Y/N)")   
                    txtChoice=txtChoice.upper()
                         
        else:
            txtChoice =input("invalid input")

    print("closing program")
    runThreads.clear()
    readDataThread.join()
    CalculateDatathread.join()
    CommandThread.join()
    # pingThread.join()
    exit()




    
    
    
        

    
