#!/usr/bin/python
import os
import psutil
import time
import sys
import notify2
from PyQt5 import QtCore, QtGui, QtWidgets


DEBUG = False
LOG = False
TRAY_TOOLTIP = 'PulseSecure' 
TRAY_ICON_CONNECTED = '/home/fdlsifu/Documents/tools/pulseicon/Pulse-Secure.png' 
TRAY_ICON_NOTCONNECTED = '/home/fdlsifu/Documents/tools/pulseicon/Pulse-Secure-not.png'

TUN_PATH = '/sys/class/net/tun0'

state = {'RUNNING':0,'NOTRUNNING':1}


def log(msg,type='info'):
    output = ''
    if type == 'info':
        output += '[INFO]'
    elif type == 'error':
        output += '[ERROR]'
    elif DEBUG and type == 'debug':
        output += '[DEBUG]'
    output +='PulseIcon: ' + msg
    
    if LOG == True:
        print(output)

def dlog(msg):
    log(msg,type='debug')


class Worker(QtCore.QRunnable):

    def run(self):
        dlog("main loop start")
        time.sleep(1)
        dlog("main loop end")

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QtWidgets.QMenu(parent)

        self.pulseUiAction = self.menu.addAction("Toggle PulseUi")
        self.pulseUiAction.triggered.connect(self.pulseui)

        self.exitAction = self.menu.addAction("Exit")
        self.exitAction.triggered.connect(self.exit)

        self.setContextMenu(self.menu)
        
        # Thread work 
        self.timer = QtCore.QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.work)
        self.timer.start()

        self.vpn_connected = SystemTrayIcon.check_vpn_connected()
        notify2.init("Pulse UI Icon")

    def changeIcon(self,icon):
        self.setIcon(QtGui.QIcon(TRAY_ICON_CONNECTED))

    def run(self):
        dlog("SystemTrayIcon started")
        return

    def exit(self):
        puipid = SystemTrayIcon.get_pulseui_state()[1]
        if not puipid == -1 :
            os.system("sudo -b kill -9 "+str(puipid))
        QtCore.QCoreApplication.exit()

    def pulseui(self):
        puistate,pid = SystemTrayIcon.get_pulseui_state()

        if puistate == state['RUNNING']:
            os.system("sudo -b kill -9 "+str(pid))
        else:
            os.system("sudo -b pulseUi")

    def work(self):
        # check vpn connection
        # change icon accordingly
        # popup on connection
        # popup on disconnect

        new_state = SystemTrayIcon.check_vpn_connected()
        
        if not self.vpn_connected and new_state:
            self.setIcon(QtGui.QIcon(TRAY_ICON_CONNECTED))
            self.vpn_connected = new_state
            n = notify2.Notification("Pulse Secure VPN Connected")
            # Set the urgency level
            n.set_urgency(notify2.URGENCY_NORMAL)
            # Set the timeout
            n.set_timeout(1000)
            n.show()

        elif self.vpn_connected and not new_state:
            self.setIcon(QtGui.QIcon(TRAY_ICON_NOTCONNECTED))
            self.vpn_connected = new_state
            n = notify2.Notification("Pulse Secure VPN disconnected")
            # Set the urgency level
            n.set_urgency(notify2.URGENCY_NORMAL)
            # Set the timeout
            n.set_timeout(1000)
            n.show()
        dlog("wake up to work")
        return
    
    @staticmethod
    def check_vpn_connected():
        if os.path.isdir(TUN_PATH):
            log('vpn connected')
            return True
        log('vpn not connected')
        return False


    @staticmethod
    def get_pulseui_state():
        for proc in psutil.process_iter():
            try:
                if 'pulseui' in proc.name().lower():
                    dlog('PulseUi is running')
                    return state['RUNNING'],proc.pid
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        dlog('PulseUi is not running')
        return state['NOTRUNNING'],-1

    @staticmethod
    def is_pulseui_running():
        timeout = time.time() + 60*0.1   # 1 minutes from now
        while True:
            if SystemTrayIcon.get_pulseui_state()[0] == state['RUNNING']:
                return True
            elif time.time() > timeout:
                return False
            time.sleep(3)

def parseargs():
    global LOG
    if len(sys.argv) == 1:
        return
    if sys.argv[1] == "-v":
        LOG = True
        log("log activated")

def launch_app():
    app = QtWidgets.QApplication(sys.argv)

    w = QtWidgets.QWidget()
    if SystemTrayIcon.check_vpn_connected():
        trayIcon = SystemTrayIcon(QtGui.QIcon(TRAY_ICON_CONNECTED), w)
    else:
        trayIcon = SystemTrayIcon(QtGui.QIcon(TRAY_ICON_NOTCONNECTED), w)

    trayIcon.show()
    trayIcon.run()
    sys.exit(app.exec_())


def main():
    parseargs()
    cmd = 'sudo -b pulseUi'
    log('Asking for permissions')
    os.system(cmd)
    
    time.sleep(1)
    if not SystemTrayIcon.is_pulseui_running():
        log("PulseUi failed to execute",type='error')
        exit()

    launch_app()

if __name__ == '__main__':
    main()
