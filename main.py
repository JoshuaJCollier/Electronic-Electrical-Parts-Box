import socket
import select
import sys
import time
import re
from gpiozero import LED

# Initialising Pins
# 0 is serial, 1 is clock, 2 is latch
red = [LED(2), LED(3), LED(4)]
green = [LED(17), LED(27), LED(22)]
blue = [LED(10), LED(9), LED(11)]
ground = [LED(5), LED(6), LED(13)]

for i in range(3):
    red[i].off()
    green[i].off()
    blue[i].off()
    ground[i].off()


# Code executed to listen to port 4000 on the localhost (127.0.0.1)
# Listens to commands in format /?find=NAME, /?add=NAME:AMOUNT, /?take=NAME:AMOUNT
# There is a linked html file that sorts our interaction
# By Josh Collier, June 2020

# -------------------------------------------------- Initialising Variables ---------------------------------------------------
# Setting some global constants
fileName = "/home/pi/Desktop/ElectronicsBox/Electronic-Electrical-Parts-Box/parts.txt"
maxReadSize = 1024
tcpPort = 25000
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

htmlHeader = "<html>\n" + preBody + "\n<body>\n<h1>"
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
    sock.send((httpHeaders + htmlHeader + message + "</h1>" + buildTable() + htmlTail).encode('utf-8'))
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
    returnList = []
    for i in range(8):
        returnList.append([])
        for j in range(8):
            returnList[i].append(0)
    return returnList

# RGB values are 8x8 list of 0s and 1s
def updateShiftRegisters(r, g, b):
    allColours = [red, green, blue, ground]
    for i in range(4):
        allColours[i][2].off() # Turn all latch low
    
    for i in range(8):
        allColours[3][1].on() # Turn ground clock high
        allColours[3][0].on() # Turn ground serial high
            
        for j in range(8):
            
            for k in range(3): # Only for RGB
                allColours[k][1].on() # Turn colour clock high
                if (r[i][j] == 1):
                    allColours[k][0].on() # Turn colour serial high
                else if (r[i][j] == 0):
                    allColours[k][0].off() # Turn colour serial low

            time.sleep(0.1) # Bit of a rest
            for k in range(3):
                allColours[k][1].off() # Turn colour clock low

        allColours[3][1].off() # Turn ground clock low

    for i in range(4):
        allColours[i][2].on() # Turn all latch high

    
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
while(listening):
    clientSock, address = tcpSock.accept()
    
    data = clientSock.recv(maxReadSize)
    dataStr = data.decode('utf-8')
    
    if data:
        print("Client Accepted")
        print("We just recieved:", data)
        print("Current Parts:")
        print(parts)
        
        # --------------------------------------------- We are looking for a part ---------------------------------------------
        if ("GET /?find=" in dataStr):
            partLookingFor = re.search(r'(?<=\?find=)\w+', dataStr).group(0)
            print("Finding", partLookingFor)

            purpleLeds = eightsquare()
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

            updateShiftRegisters(purpleLeds, emptySquare, purpleLeds)
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
            greenLeds = eightsquare()


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
            updateShiftRegisters(emptySquare, greenLeds, emptySquare)
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
                            weveRemoved = True
                            break
                        elif (parts[i][j][1] < takeNo):
                            partsNow = parts[i][j][1]
                            weCantRemove = True
                            break
                if (weveRemoved or weCantRemove):
                    weDontHave = False
                    break

            uploadChanges()
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
                        else:
                            # We have found 1, now we have to find the other
                            foundOne = True
                            otherPart = [i,j]
                    elif (parts[i][j][0] == swap[1]):
                        if (foundOne):
                            otherParti = otherPart[0]
                            otherPartj = otherPart[1]
                            buf = parts[otherParti][otherPartj]
                            parts[otherParti][otherPartj] = parts[i][j]
                            parts[i][j] = buf
                            done = True
                        else:
                            # We have found 1, now we have to find the other
                            foundTwo = True
                            otherPart = [i,j]
                if (done):
                    break
            
            uploadChanges()
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
