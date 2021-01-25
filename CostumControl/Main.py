import logging
from threading import Thread
from queue import Queue 
from time import time, sleep
import time
import atexit
import threading
import math
from move_controls import Controls
from general_controls import GeneralControls

m=Controls()
sensorData=dict()
instructions=[]
currentHeading="N"



def getInstructions():
    # get all the instructions from the api
    pass

def exitHandler():
    print("emergency stop")
    m.emergency_stop()
    m.close_connection()
    print("closing program")
    
            
def pingThread():
    threading.Timer(0.5, pingThread).start()
    m.generalControls.ping()

def turnRobot (orientation):
    target = 0
    index =0
    # if orientation == "N":
    #     target =1
    #     m.turn_right(200,10)
    # elif orientation =="E":
    #     target = 3.14/2
    #     m.turn_right(200,10)
    # elif orientation =="S":
    #     target = -1
    #     m.turn_right(200,10)

    # elif orientation =="W":
    #     target = -3.14/2
    #     m.turn_left(200,10)
    # pingThread()

    while True:
        try:
            
            sensorData = m.readSensors.readAll()
            yaw = sensorData["YAW"]
            # if (index == 0):
            #     target = yaw
            #     print ("target" + str(yaw))
            # index = index +1
            print ("YAW: " + str(yaw))
            # if yaw <= target:
            #     currentHeading=target
            #     print("REACHED")
            #     exit()
            #     break
        except(KeyError):
            print("keyerror")







def drive(distance):
    check=0
    distance= distance
    print("distance " + str(distance))

    sensorData = dict()
    
    for x in range(1000):
         m.readSensors.readAll()

    m.go_forward(100,10)
    
    while True:
        try:
            sensorData=m.readSensors.readAll()
            # print("LEFT DIS")
            # print(sensorData["leftDis"])
            check=sensorData["leftDis"]
            # print("CHECK" + str(check))


            if(distance <= check):
                print("STOP")
                exit()
        except(KeyError):
            print("error?")
        

if __name__ == "__main__":

    # get all instruction
    # read all instructions
    # for instruction in instructions:
    #     then read instruction per instrction
    #     check direction first
    #      put it int he right direction
    #      drive
    #      stop and go to the next instruction



    try:
        print("STARTING PROGRAM")
        pingThread()
        atexit.register(exitHandler)
        m.emergency_stop_release()
        # drive(2)
        turnRobot("N")   
        

    finally:
        exitHandler()
    
    
    
        

    
