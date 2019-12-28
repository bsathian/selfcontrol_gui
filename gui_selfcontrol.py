import os
import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout,QSlider,QLabel,QHBoxLayout,QScrollBar,QGridLayout
from PyQt5.QtCore import QDateTime, Qt, QTimer

class selfcontrolCORE:
    def __init__(self,blockedListFilePath = None, hostsFilePath = None):
        if blockedListFilePath:
            self.blockedListfilePath = blockedListFilePath
        else:
            self.blockedListFilePath = "blocked.txt"

        if hostsFilePath:
            self.hostsFilePath = hostsFilePath
        else:
            self.hostsFilePath = "/etc/hosts"

    def createBackupFiles(self):
        os.system("cp "+self.hostsFilePath+" hosts_backup")
        os.system("cp hosts_backup hosts_new")
        self.addLinesToFile("hosts_new")
        os.system("gksu cp hosts_new "+self.hostsFilePath)
        #os.system("rm hosts_new")

    def endSelfcontrol(self):
        os.system("gksu cp hosts_backup "+self.hostsFilePath)


    def addLinesToFile(self,duplicateHostsFilePath):
        '''Adds website lines from blocked.txt to /etc/hosts if not already present. For extra protection, use the argument duplicateHostsFilePath to write into a copy of /etc/hosts'''

        blockedListFile = open(self.blockedListFilePath,"r")

        if duplicateHostsFilePath:
            hostsFile = open(duplicateHostsFilePath,"a")
        else:
            hostsFile = open(self.hostsFilePath,"a")

        hostsFile.write("\n#SELFCONTROL BLOCK START\n")
        for site in blockedListFile:
            addString = site
            if site[0:4] != "www.":
                addString = "www."+addString
            hostsFile.write("0.0.0.0 " +addString)
            hostsFile.write("::0 "+addString)
        hostsFile.write("#SELFCONTROL BLOCK END\n\n")

    def linesAlreadyPresent(self):
        '''Checks if lines are already present in hosts file'''
        hostsFile = open(self.hostsFilePath,"r")

        startFlag = False
        endFlag = False
        for i in hostsFile:
            if i.rstrip("\n") == "#SELFCONTROL BLOCK START":
                startFlag = True
            elif i.rstrip("\n") == "#SELFCONTROL BLOCK END":
                endFlag = True

        return startFlag and endFlag


class selfcontrolGUI(selfcontrolCORE,QWidget):
    def __init__(self,blockedListFilePath = None,hostsFilePath = None):
        super().__init__(blockedListFilePath,hostsFilePath)
        super(QWidget,self).__init__()

        #Create the widgets in abstract space
        self.createSliderWidget()
        self.createButtonWidget()
        self.createCountdowntimerWidget()


        mainLayout = QGridLayout()
        mainLayout.addWidget(self.countdownTimer,0,0)
        mainLayout.addWidget(self.slider,1,0)
        mainLayout.addWidget(self.button,2,0)
        #mainLayout.setRowStretch(1, 1)
        #mainLayout.setRowStretch(2, 1)
        #mainLayout.setColumnStretch(0, 1)
        #mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)


        #Define actions, for button set the slider and the button widget visible to "False" after getting clicked
        self.slider.valueChanged.connect(self.setSelfcontrolDuration)
        self.button.clicked.connect(self.startSelfcontrol)

    def createCountdowntimerWidget(self):
        '''Define the attributes of the countdown timer'''
        self.countdownTimer = QLabel("00:00:00")
        #TODO:Fine tune this mofo
        self.countdownTimer.setStyleSheet("font: 48pt")

    def createSliderWidget(self):
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        #up to 10 hours in half hour windows - Multiply by 1800 to get seconds
        self.slider.setMaximum(10*2)


    def createButtonWidget(self):
        self.button = QPushButton("START")

    def hideSliderAndButton(self):
        self.slider.setVisible(False)
        self.button.setVisible(False)

    def startSelfcontrol(self):
        '''Add what happens if START button is clicked'''
        self.hideSliderAndButton()
        #copying files stuff comes here
        if not self.linesAlreadyPresent():
            #Create backup files, and do the copying shenanigans
            self.createBackupFiles()

        #Set the time for countdown - We don't really need this, but having this here
        #For extra protection :)
        self.hh = self.slider.value() // 2
        self.mm = (self.slider.value() % 2) * 30
        #do countdown
        self.waitForCompletion()

    def setSelfcontrolDuration(self):
        '''Translate slider sliding to text, and make updateCountdownTimer display it'''
        self.hh = self.slider.value() // 2
        self.mm = (self.slider.value() % 2) * 30
        reqTime = self.hh*3600 + self.mm*60
        self.timeString = time.strftime("%H:%M:%S",time.gmtime(reqTime))
        self.updateCountdownTimer()


    def updateCountdownTimer(self):
        '''Create a huge text of the countdown timer. Also specifies the original set time'''
        self.countdownTimer.setText(self.timeString)

    def periodicUpdateCountdownTimer(self):
        currTime = time.time()
        reqTime = self.hh*3600 + self.mm*60

        if currTime - self.startTime > reqTime:
            self.timer.stop()
            self.endSelfcontrol()
        else:
            countdownTime = reqTime - (currTime - self.startTime)
            self.timeString = time.strftime("%H:%M:%S",time.gmtime(countdownTime))
            self.updateCountdownTimer()



    def waitForCompletion(self):
        '''Runs a countdown timer'''
        self.startTime = time.time()
        self.timer = QTimer()
#        QTimer.singleShot(reqTime * 1000,self.timer,self.updateCountdownTimer)
        self.timer.timeout.connect(self.periodicUpdateCountdownTimer)
        self.timer.start(1000)



app = QApplication(["SelfControl"])
s = selfcontrolGUI()
s.show()
sys.exit(app.exec_())
