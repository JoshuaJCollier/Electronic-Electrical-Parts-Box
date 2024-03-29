import socket
import select
import sys
import time
import re
import numpy as np

import RPi.GPIO as GPIO
from multiprocessing import Process

# Initialising Pins
# 0 is serial, 1 is clock, 2 is latch

GPIO.setmode(GPIO.BCM)
RED_PIN_DATA  = 2
RED_PIN_LATCH = 4
RED_PIN_CLOCK = 3
GPIO.setup(RED_PIN_DATA,  GPIO.OUT)
GPIO.setup(RED_PIN_LATCH, GPIO.OUT)
GPIO.setup(RED_PIN_CLOCK, GPIO.OUT)

GREEN_PIN_DATA  = 17
GREEN_PIN_LATCH = 22
GREEN_PIN_CLOCK = 27
GPIO.setup(GREEN_PIN_DATA,  GPIO.OUT)
GPIO.setup(GREEN_PIN_LATCH, GPIO.OUT)
GPIO.setup(GREEN_PIN_CLOCK, GPIO.OUT)

BLUE_PIN_DATA  = 10
BLUE_PIN_LATCH = 11
BLUE_PIN_CLOCK = 9
GPIO.setup(BLUE_PIN_DATA,  GPIO.OUT)
GPIO.setup(BLUE_PIN_LATCH, GPIO.OUT)
GPIO.setup(BLUE_PIN_CLOCK, GPIO.OUT)

GROUND_PIN_DATA  = 5
GROUND_PIN_LATCH = 13
GROUND_PIN_CLOCK = 6
GPIO.setup(GROUND_PIN_DATA,  GPIO.OUT)
GPIO.setup(GROUND_PIN_LATCH, GPIO.OUT)
GPIO.setup(GROUND_PIN_CLOCK, GPIO.OUT)

secondsOn = 0.5
# Code executed to listen to port 4000 on the localhost (127.0.0.1)
# Listens to commands in format /?find=NAME, /?add=NAME:AMOUNT, /?take=NAME:AMOUNT
# There is a linked html file that sorts our interaction
# By Josh Collier, June 2020

# -------------------------------------------------- Initialising Variables ---------------------------------------------------
# Setting some global constants
fileName = "/home/pi/Desktop/electronicsBox/Electronic-Electrical-Parts-Box/parts.txt"
maxReadSize = 1024
tcpPort = 5000
tcpAddress = "0.0.0.0"

httpHeaders = "HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: Closed\n\n"

preBody = """  <head>
    <title>Electronic Electrical Parts Box</title>
    <style>
      table,
      th,
      td {
        padding: 10px;
        border: 1px solid black;
        border-collapse: collapse;
      }
    </style>
  </head>"""

htmlHeader = "<html>\n" + preBody + "\n<body>\n"
htmlTail = "\n</body>\n</html>\n"

# Initialise empty 8x8 array
parts = []
for i in range(8):
    parts.append([])
    for j in range(8):
        parts[i].append([])
        parts[i][j].append("N/A")
        parts[i][j].append(0)


# ---------------------------------------------------- Dealing with Funcs -----------------------------------------------------
def buildParts():
    # Build parts array
    partsFile = open(fileName, "r")
    partsFileLines = partsFile.readlines()
    for i in range(len(partsFileLines)):
        line = partsFileLines[i].strip()
        lineComponents = line.split(",")
        for j in range(len(lineComponents)):
            itemComponents = lineComponents[j].split(":")
            parts[i][j][0] = itemComponents[0]
            parts[i][j][1] = int(itemComponents[1])
    partsFile.close()

def uploadChanges():
    partsFile = open(fileName, "w")
    for i in range(len(parts)):
        partsLine = ""
        for j in range(len(parts[i])):
            partsLine += parts[i][j][0] + ":" + str(parts[i][j][1]) + ","
        partsLine = partsLine[0:-1]
        partsFile.write(partsLine+"\n")
    partsFile.close()

def sendAndClose(message, sock):
    sock.send((httpHeaders + htmlHeader + buildTable() + "<h1>" + message + "</h1>" + htmlTail).encode('utf-8'))
    sock.close()

def buildTable():
    returnTable = "\n\t<table>\n"
    
    for i in range(len(parts)):
        returnTable += "\t\t<tr>\n"
        for j in range(len(parts[i])):
            returnTable += "\t\t\t<th>" + '<a href="/?find=' + parts[i][j][0] + '">' + parts[i][j][0] + '</a>' + ": " + str(parts[i][j][1]) + "</th>\n"
        returnTable += "\t\t</tr>\n"
    returnTable += "\t</table>"

    return returnTable

def eightSquare():
    returnList = [[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]
    return returnList

# RGB values are 8x8 list of 0s and 1s
def updateShiftRegisters(r, g, b):
    r = np.array(r).T.tolist()
    g = np.array(g).T.tolist()
    b = np.array(b).T.tolist()

    startTime = time.time()
    
    z = 0
    while(time.time() - startTime < secondsOn):
        z += 1
        # Ground
        #GPIO.output(GROUND_PIN_LATCH, 0)

        for y in range(8):
            GPIO.output(GROUND_PIN_LATCH, 0)
            for x in range(8):
                if (x == (7-y)):
                    GPIO.output(GROUND_PIN_DATA, 0)
                else:
                    GPIO.output(GROUND_PIN_DATA, 1)
                GPIO.output(GROUND_PIN_CLOCK, 1)
                GPIO.output(GROUND_PIN_CLOCK, 0)
                if (z == 1 and x == (8-y)):
                    print("Ground: 0")
                elif (z == 1):
                    print("Ground: 1")
            GPIO.output(GROUND_PIN_LATCH, 1)

            # Red
            red = sum(d * 2**i for i, d in enumerate(r[7-y][::-1])) 
            GPIO.output(RED_PIN_LATCH, 0)
            for x in range(8):
                GPIO.output(RED_PIN_DATA, (red >> x) & 1)
                GPIO.output(RED_PIN_CLOCK, 1)
                GPIO.output(RED_PIN_CLOCK, 0)
                if (z == 1):
                    print("Red: " + str((red >> x) & 1))
            GPIO.output(RED_PIN_LATCH, 1)
            
            # Red Reset
            GPIO.output(RED_PIN_LATCH, 0)
            for x in range(8):
                GPIO.output(RED_PIN_DATA, 0)
                GPIO.output(RED_PIN_CLOCK, 1)
                GPIO.output(RED_PIN_CLOCK, 0)
            GPIO.output(RED_PIN_LATCH, 1)

            # Green
            green = sum(d * 2**i for i, d in enumerate(g[7-y][::-1])) 
            GPIO.output(GREEN_PIN_LATCH, 0)
            for x in range(8):
                GPIO.output(GREEN_PIN_DATA, (green >> x) & 1)
                GPIO.output(GREEN_PIN_CLOCK, 1)
                GPIO.output(GREEN_PIN_CLOCK, 0)
                if (z == 1):
                    print("Green: " + str((green >> x) & 1))
            GPIO.output(GREEN_PIN_LATCH, 1)
            
            # Green Reset
            GPIO.output(GREEN_PIN_LATCH, 0)
            for x in range(8):
                GPIO.output(GREEN_PIN_DATA, 0)
                GPIO.output(GREEN_PIN_CLOCK, 1)
                GPIO.output(GREEN_PIN_CLOCK, 0)
            GPIO.output(GREEN_PIN_LATCH, 1)

            # Blue
            blue = sum(d * 2**i for i, d in enumerate(b[7-y][::-1])) 
            GPIO.output(BLUE_PIN_LATCH, 0)
            for x in range(8):
                GPIO.output(BLUE_PIN_DATA, (blue >> x) & 1)
                GPIO.output(BLUE_PIN_CLOCK, 1)
                GPIO.output(BLUE_PIN_CLOCK, 0)
                if (z == 1):
                    print("Blue: " + str((blue >> x) & 1))
            GPIO.output(BLUE_PIN_LATCH, 1)
            
            # Blue Reset
            GPIO.output(BLUE_PIN_LATCH, 0)
            for x in range(8):
                GPIO.output(BLUE_PIN_DATA, 0)
                GPIO.output(BLUE_PIN_CLOCK, 1)
                GPIO.output(BLUE_PIN_CLOCK, 0)
            GPIO.output(BLUE_PIN_LATCH, 1)
            
            # Ground Reset
            GPIO.output(GROUND_PIN_LATCH, 0)
            for x in range(8):
                GPIO.output(GROUND_PIN_DATA, 0)
                GPIO.output(GROUND_PIN_CLOCK, 1)
                GPIO.output(GROUND_PIN_CLOCK, 0)
            GPIO.output(GROUND_PIN_LATCH, 1)
    
    
    
# ------------------------------------------------------- TCP Listening -------------------------------------------------------
# Create TCP socket
tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpSock.bind((tcpAddress, tcpPort))
tcpSock.listen(1)
listening = True
emptyLeds = eightSquare()

buildParts()

# On the webpage we will generate it from the partsFile, which will allow you to take,
# add or find parts with simple buttons in a html page 
print("Server online. Awaiting requests...")
while(listening):
    clientSock, address = tcpSock.accept()
    
    data = clientSock.recv(maxReadSize)
    dataStr = data.decode('utf-8')
    
    if data:
        print("Client Accepted")
        print("We just recieved:", data[0:16])
        #print("Current Parts:")
        #print(parts)
        
        # ------------------------------------------------- When you are bored ------------------------------------------------
        if ("GET /?lightUp" in dataStr):
            #partLookingFor = re.search(r'(?<=\?find=)\w+', dataStr).group(0)
            print("Lighting Up")

            while(True):
                redOne = eightSquare()
                redOne[0] = [1, 1, 1, 1, 1, 1, 1, 1]
                greenOne = eightSquare()
                greenOne[1] = [1, 1, 1, 1, 1, 1, 1, 1]
                blueOne = eightSquare()
                blueOne[2] = [1, 1, 1, 1, 1, 1, 1, 1]
                for i in range(8):
                    redOne[i % 8] = [1, 1, 1, 1, 1, 1, 1, 1]
                    greenOne[(i+1) % 8] = [1, 1, 1, 1, 1, 1, 1, 1]
                    blueOne[(i+2) % 8] = [1, 1, 1, 1, 1, 1, 1, 1]
                    updateShiftRegisters(redOne, greenOne, blueOne)
                    redOne[(i-1) % 8] = [0, 0, 0, 0, 0, 0, 0, 0]
                    greenOne[i % 8] = [0, 0, 0, 0, 0, 0, 0, 0]
                    blueOne[(i+1) % 8] = [0, 0, 0, 0, 0, 0, 0, 0]
                    updateShiftRegisters(redOne, greenOne, blueOne)


            replyMessage = "Lets go"
            sendAndClose(replyMessage, clientSock)
        
        # --------------------------------------------- We are looking for a part ---------------------------------------------
        if ("GET /?find=" in dataStr):
            partLookingFor = re.search(r'(?<=\?find=)\w+', dataStr).group(0)
            print("Finding", partLookingFor)

            purpleLeds = eightSquare()
            replyX, replyY = "", ""
            found = False
            foundList = []
            for i in range(8):
                for j in range(8):
                    if (partLookingFor in parts[i][j][0]):
                        purpleLeds[i][j] = 1
                        replyX, replyY = str(j+1), str(i+1)
                        foundList.append([parts[i][j][0], replyX, replyY])
                        print("Found in row: " + replyX + ", column: " + replyY)
                        found = True

            Process(target=updateShiftRegisters, args=(purpleLeds, emptyLeds, purpleLeds)).start()
            print(purpleLeds)
            # Reply and close socket
            replyMessage = ""
            if (found):
                for i in range(len(foundList)):
                    replyMessage += foundList[i][0] + " is in row: " + foundList[i][1] + ", column: " + foundList[i][2] + "<br>"
            else:
                replyMessage = "Find failed."
            sendAndClose(replyMessage, clientSock)

        # ----------------------------------------------- We are adding a part/s ----------------------------------------------
        if ("GET /?add=" in dataStr):
            add = re.search(r'(?<=\?add=)\w+:\w+', dataStr).group(0)
            add = add.split(":")
            addPart = add[0]
            addNo = int(add[1])
            print("Adding", str(addNo), addPart)

            partsNow = 0
            greenLeds = eightSquare()


            # We will check if the part is in the list, if so we will add to its total, if
            # not we will add it to the next available slot and give it the amount provided
            weveAdded = False
            for i in range(8):
                for j in range(8):
                    if (parts[i][j][0] == addPart):
                        parts[i][j][1] += addNo
                        partsNow = parts[i][j][1]
                        greenLeds[i][j] = 1
                        weveAdded=True
                        break
                    elif (parts[i][j][0] == "N/A"):
                        parts[i][j][0] = addPart
                        parts[i][j][1] += addNo
                        partsNow = parts[i][j][1]
                        greenLeds[i][j] = 1
                        weveAdded=True
                        break
                if (weveAdded):
                    break
                
            uploadChanges()
            Process(target=updateShiftRegisters, args=(emptyLeds, greenLeds, emptyLeds)).start()
            # Reply and close socket (and text pedantics)
            addS = ""
            if (partsNow != 1):
                addS = "s"
            replyMessage = ""
            if (weveAdded):
                replyMessage = "You now have " + str(partsNow) + " " + addPart + addS + "."
            else:
                replyMessage = "Addition failed."
            sendAndClose(replyMessage, clientSock)
            
        # ---------------------------------------------- We are removing a part/s ---------------------------------------------
        if ("GET /?take=" in dataStr):
            take = re.search(r'(?<=\?take=)\w+:\w+', dataStr).group(0)
            take = take.split(":")
            takePart = take[0]
            takeNo = int(take[1])
            print("Removing", str(takeNo), takePart)

            partsNow = 0
            redLeds = eightSquare()
            
            # We will check if we have any of this part, and we will remove this amout
            # if we have that many
            weveRemoved = False
            weCantRemove = False
            weDontHave = True
            for i in range(8):
                for j in range(8):
                    if (parts[i][j][0] == takePart):
                        if (parts[i][j][1] >= takeNo):
                            parts[i][j][1] -= takeNo
                            partsNow = parts[i][j][1]
                            redLeds[i][j] = 1
                            weveRemoved = True
                            break
                        elif (parts[i][j][1] < takeNo):
                            partsNow = parts[i][j][1]
                            redLeds[i][j] = 1
                            weCantRemove = True
                            break
                if (weveRemoved or weCantRemove):
                    weDontHave = False
                    break

            uploadChanges()
            updateShiftRegisters(redLeds, emptyLeds, emptyLeds)
            # Reply and close socket (and text pedantics)
            replyMessage = ""
            addS = ""
            if (partsNow != 1):
                addS = "s"
            if (weveRemoved):
                replyMessage = "You now have " + str(partsNow) + " " + takePart + addS + "."
            elif (weDontHave):
                anyS = ["a", ""]
                if (takeNo != 1):
                    anyS = ["any", "s"]
                replyMessage + "You dont have " + anyS[0] + " " + takePart + anyS[1]
            elif (weCantRemove):
                replyMessage = "You dont have enough, you only have " + str(partsNow) + " " + takePart + addS + "."
            sendAndClose(replyMessage, clientSock)

        # ---------------------------------------------- We are swapping a part/s ---------------------------------------------
        if ("GET /?swap=" in dataStr):
            swap = re.search(r'(?<=\?swap=)\w+,\w+', dataStr).group(0)
            swap = swap.split(",")

            foundOne = False
            foundTwo = False
            done = False
            otherPart = []
            blueLeds = eightSquare()
            for i in range(8):
                for j in range(8):
                    if (parts[i][j][0] == swap[0]):
                        if (foundTwo):
                            otherParti = otherPart[0]
                            otherPartj = otherPart[1]
                            buf = parts[otherParti][otherPartj]
                            parts[otherParti][otherPartj] = parts[i][j]
                            parts[i][j] = buf
                            done = True
                            blueLeds[i][j] = 1
                        else:
                            # We have found 1, now we have to find the other
                            foundOne = True
                            otherPart = [i,j]
                            blueLeds[i][j] = 1
                    elif (parts[i][j][0] == swap[1]):
                        if (foundOne):
                            otherParti = otherPart[0]
                            otherPartj = otherPart[1]
                            buf = parts[otherParti][otherPartj]
                            parts[otherParti][otherPartj] = parts[i][j]
                            parts[i][j] = buf
                            done = True
                            blueLeds[i][j] = 1
                        else:
                            # We have found 1, now we have to find the other
                            foundTwo = True
                            otherPart = [i,j]
                            blueLeds[i][j] = 1
                if (done):
                    break
            
            uploadChanges()
            updateShiftRegisters(emptyLeds, emptyLeds, blueLeds)
            # Reply and close socket (and text pedantics)
            replyMessage = ""
            if (done):
                replyMessage = "You have swapped " + swap[0] + " with " + swap[1] + "."
            else:
                replyMessage = "Swap failed."
            sendAndClose(replyMessage, clientSock) 
            
            

    else:
        print("Closing client socket")
        clientSock.close()
