# Electronic-Electrical-Parts-Box
IMPORTANT: curl ifconfig.me to find ip address
IMPORTANT: ssh pi@pislocalip to ssh in
Code to run for keeping track of and finding electronic parts in my parts box

Currently its job is to take an input in a webformat, from any ip port 25000, with requests of either find, add or take.

Find:
Provide the name of a part and it will return the position in the box of that particular part, and eventually it will light up that part of the box

Add:
Provide the name of a part and an amount, it will add that amount of that thing to the spreadsheet. If that part doesnt exist it will add it to the next avaliable slot, potentially we can make it so that it adds it to a new spot that you can specify. (Will also light up the slot in green for addition)

Take:
Provide the name of a part and an amount, it will take that amount of that thing from the spreadsheet. (Will light up that slot in a particular colour not sure yet, maybe red)

Swap:
Provide the name of two parts, and the position of them will swap in the spreadsheet. (Will light up the slots that have moved in blue)

Other things:
- It will keep track of how much of everything there is
- Passive light cycling when it is not in use
- Return errors in that occur to the html window
- Have related html code that allows for easy view of the spreadsheet and manipulation
- Can have a check of quantity, lights up with how much of everything there is
- Other....
