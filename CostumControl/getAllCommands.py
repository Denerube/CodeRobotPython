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


JsonFileName="jsonData.json"
lastPositionFile="LastPos.txt"

commandArray=[]

def WritePositionToTextfile(lastPos):
    with open(lastPositionFile,'w') as text_file:
        text_file.write(str(lastPositionFile))


def readLastCommandIdFromFile():
    with open(lastPositionFile) as text_file:
        dataLastCmdId= text_file.read()
    return lastPositionFile



def getNextMove():
    url="https://ai-4x4-api.herokuapp.com/plsSendNext"
    x=requests.get(url)
    data=x.json()
    print(data)
    # writeToJsonFile(data)
    return data


def writeToJsonFile(data):
    with open(JsonFileName, 'w') as json_file:
        json.dump(data, json_file)

def ReadFromJsonFile():
    with open(JsonFileName) as json_file:
        data = json.load(json_file)
    # print (data)
    return data

def getAllMoves():
    data=getNextMove()

    # data = getNextMove()
    # commandArray.append(data)
    # while 1:
    #     data = getNextMove()
    #     commandArray.append(data)
    #     if "End" in data.keys():
    #         break
    writeToJsonFile(data)

if __name__ == "__main__":
    getAllMoves()
    ReadFromJsonFile()
    print("DONE")
    

