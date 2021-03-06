# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Updateui.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import hunterpyqrc_rc

from threading import Thread
import requests
import sys
import hashlib
import os
import subprocess
import time

class Update:
    Server = "https://bitbucket.org/Haato/hunterpy/raw/" # URL Base for the project
    def __init__(self, version, branch):
        self.LocalVersion = version # Version of HunterPy in the user computer, passed as an args
        self.LatestVersion = "unknown" # Online version of HunterPy, it's in the project url
        self.hasInternet = False
        self.UpdateQueue  = []
        self.Files = None
        self.LocalFiles = {}
        self.UpdateWindow = None
        self.Ui = None
        self.Progress = 0
        self.Branch = branch
        Update.Server = f"{Update.Server}{branch}/" # Update server url depending on branch

    def start(self):
        self.OpenUpdateWindow()
        
    def StartUpdateThread(self):
        t = Thread(target=self.StartUpdate)
        t.daemon = True
        t.start()

    def StartUpdate(self):
        self.CheckVersionOnline()
        self.CheckIfVersionIsDifferent()

    def OpenUpdateWindow(self):
        app = QtWidgets.QApplication(sys.argv)
        self.UpdateWindow = QtWidgets.QMainWindow()
        self.Ui = Ui_UpdateWindow()
        self.Ui.setupUi(self.UpdateWindow)
        QtCore.QTimer.singleShot(1000, self.StartUpdateThread)
        sys.exit(app.exec_())

    def CheckVersionOnline(self):
        try:
            self.Ui.updateText.setText(f"Checking branch: {self.Branch}...")
            onlineVersion = requests.request('get', Update.Server+"version.txt", timeout=3)
            self.hasInternet = True
            self.LatestVersion = onlineVersion.text
            time.sleep(1.5)
        except:
            self.Ui.updateText.setText("Failed to get latest version online...")
            self.hasInternet = False
            time.sleep(2)

    def CheckIfVersionIsDifferent(self):
        if self.hasInternet:
            if self.LatestVersion != self.LocalVersion:
                self.GetFiles()
                self.ListLocalFiles()
                self.GetFileQueue()
                self.UpdateHunterPy()
            else:
                self.Ui.updateText.setText("No new version found!")
                time.sleep(1)
                subprocess.Popen("HunterPy.exe notupdated", shell=True)
                self.UpdateWindow.close()
        else:
            subprocess.Popen("HunterPy.exe notupdated", shell=True)
            self.UpdateWindow.close()

    def ListLocalFiles(self):
        for file in os.listdir():
            if os.path.isdir(file) == False:
                f = open(file, "rb")
                fBytes = f.read()
                f.close()
                self.LocalFiles[file] = hashlib.sha256(fBytes).hexdigest()

    def GetFiles(self):
        files = requests.request('get', Update.Server+"files.json")
        self.Ui.updateText.setText("Checking for new files...")
        self.Files = files.json()

    def GetFileQueue(self):
        for file in self.Files:
            if file in self.LocalFiles:
                if self.LocalFiles[file] == self.Files[file]:
                    continue
                else:
                    if file == "update.exe":
                        continue
                    self.UpdateQueue.append(file)
            else:
                self.UpdateQueue.append(file)
        self.Ui.updateText.setText(f"Found {len(self.UpdateQueue)} new file(s)!")

    def ReplaceOldFile(self, fileName, fileBytes):
        nFile = open(fileName, "wb")
        nFile.write(fileBytes)
        nFile.close()

    def GetFileBytes(self, file):
        fBytes = requests.request('get', Update.Server+file).content
        return fBytes
    
    def UpdateHunterPy(self):
        if self.hasInternet:
            for file in self.UpdateQueue:
                self.Ui.updateText.setText(f"Updating \"{file}\"...")
                fBytes = self.GetFileBytes(file)
                self.ReplaceOldFile(file, fBytes)
        self.Ui.updateText.setText("Done!")
        subprocess.Popen("HunterPy.exe updated", shell=True)
        self.UpdateWindow.close()
        sys.exit()

class Ui_UpdateWindow(object):
    def setupUi(self, UpdateWindow):
        UpdateWindow.setObjectName("UpdateWindow")
        UpdateWindow.resize(380, 380)
        UpdateWindow.setMinimumSize(QtCore.QSize(380, 380))
        UpdateWindow.setMaximumSize(QtCore.QSize(380, 380))
        UpdateWindow.setStyleSheet("QMainWindow {\n"
                "    background-color: rgb(38, 38, 38);\n"
                "    border-radius: 3px;\n"
                "}\n"
                "\n"
                "QLabel {\n"
                "    color: white;\n"
                "}")
        UpdateWindow.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        #UpdateWindow.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        UpdateWindow.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.centralwidget = QtWidgets.QWidget(UpdateWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.updateProgress = QtWidgets.QProgressBar(self.centralwidget)
        self.updateProgress.setGeometry(QtCore.QRect(40, 230, 301, 7))
        self.updateProgress.setAutoFillBackground(False)
        self.updateProgress.setStyleSheet("QProgressBar {\n"
                "    background-color: rgb(79, 79, 79);\n"
                "    border-radius: 3px;\n"
                "}\n"
                "QProgressBar::chunk {\n"
                "    background-color: rgb(183, 3, 3);\n"
                "    border-radius: 3px;\n"
                "}")
        self.updateProgress.setProperty("value", 1)
        self.updateProgress.setMaximum(0)
        self.updateProgress.setTextVisible(False)
        self.updateProgress.setInvertedAppearance(False)
        self.updateProgress.setTextDirection(QtWidgets.QProgressBar.TopToBottom)
        self.updateProgress.setFormat("")
        self.updateProgress.setObjectName("updateProgress")
        self.updateText = QtWidgets.QLabel(self.centralwidget)
        self.updateText.setGeometry(QtCore.QRect(46, 240, 291, 41))
        font = QtGui.QFont()
        font.setFamily("MS Reference Sans Serif")
        font.setPointSize(10)
        self.updateText.setFont(font)
        self.updateText.setAlignment(QtCore.Qt.AlignCenter)
        self.updateText.setObjectName("updateText")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(50, 40, 301, 191))
        self.label.setTextFormat(QtCore.Qt.RichText)
        self.label.setObjectName("label")
        UpdateWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(UpdateWindow)
        QtCore.QMetaObject.connectSlotsByName(UpdateWindow)
        UpdateWindow.showNormal()

    def retranslateUi(self, UpdateWindow):
        _translate = QtCore.QCoreApplication.translate
        UpdateWindow.setWindowTitle(_translate("UpdateWindow", "HunterPy Update"))
        self.updateText.setText(_translate("UpdateWindow", "Checking for updates..."))
        self.label.setText(_translate("UpdateWindow", "<html><head/><body><p><img src=\":/Assets/hunterpylogo.png\"/></p></body></html>"))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.exit()
    else:
        update = Update(sys.argv[1], sys.argv[2])
        update.start()

