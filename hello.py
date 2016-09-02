#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
write by: jackywei 2016.08.30 
email:    biao.wei@tcl.com
'''
import errno, optparse, os, select, subprocess, sys, time, zlib
import platform
import commands
import os
import shutil
import re
import time
import zipfile
import tarfile
import string
import traceback
import codecs
import sys
import socket,select
import time
import threading
reload(sys)
#sys.setdefaultencoding("utf-8")

from xml.etree import ElementTree



##################### global var ########################
MACRO = {'FileError':4}


conn = None
gConfig = None

class JKOsHelper(object):
    if(platform.system() == "Windows"):
        linksym = "\\"
    else:
        linksym = "/"
    if(platform.system() == "Windows"):
        newlinesym = "\r\n"
    else:
        newlinesym = "\n"
    
    gLogTempDir = None
    gLogStoreDir = None
    gLogsDir = None
    gLogFileFD = None
    gPluginsDir = None
    
    @classmethod
    def GetLogTempDir(cls):
        if(cls.gLogTempDir == None):
            cls.gLogTempDir = os.getcwd() + cls.linksym + "logtempdir"
        return cls.gLogTempDir
    
    @classmethod
    def GetLinkSym(cls):
        return cls.linksym
    
    @classmethod
    def GetNewLineSym(cls):
        return cls.newlinesym
    
    @classmethod
    def GetLogStoreDir(cls):
        if(cls.gLogStoreDir == None):
            if(platform.system() == "Windows"):
                cls.gLogStoreDir = gConfig['logdir'] + cls.linksym
            else:
                cls.gLogStoreDir = os.getcwd() + cls.linksym
        return cls.gLogStoreDir
    
    @classmethod
    def GetPluginsDir(cls):
        if(cls.gPluginsDir == None):
            if(platform.system() == "Windows"):
                cls.gPluginsDir = "plugins\\"
            elif(platform.system() == "Linux"):
                cls.gPluginsDir = "plugins/"
            else:
                raise LogFormatErr("We dont support the system %s" % platform.system())
        return cls.gPluginsDir
        
    @classmethod
    def GetLogsDir(cls):
        if(cls.gLogsDir == None):
            raise LogFormatErr("We dont support the system %s" % platform.system())
        else:
            return cls.gLogsDir

    @classmethod
    def GetLogFD(cls):
        if(cls.gLogFileFD == None):
            if(os.path.exists("logs") == False):
                os.mkdir("logs")
            cls.gLogFileFD = codecs.open('logs.txt', 'a', "utf-8")
            #cls.gLogFileFD = open('logs.txt', 'a+')
            return cls.gLogFileFD
        else:
            return cls.gLogFileFD

class JKLog(object):
    @staticmethod
    def e(msg):
        print msg
        JKOsHelper.GetLogFD().write("[" + time.strftime('%Y-%m-%d,%H:%M:%S') + "]: " + msg+"\n")
        JKOsHelper.GetLogFD().flush();
    @staticmethod
    def d(msg):
        print msg
        JKOsHelper.GetLogFD().write("[" + time.strftime('%Y-%m-%d,%H:%M:%S') + "]: " + msg+"\n")
        JKOsHelper.GetLogFD().flush();
    @staticmethod
    def w(msg):
        print msg
        JKOsHelper.GetLogFD().write("[" + time.strftime('%Y-%m-%d,%H:%M:%S') + "]: " + msg+"\n")
        JKOsHelper.GetLogFD().flush();

class LogFormatErr(Exception):
    '''
    LogFormatErr
    '''
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return self.value

#############################################################
global unrarinfo

global DEBUG
DEBUG = False

global isLogined
isLogined = False


global SETP
SETP = 0


global gExceptionTimes
gExceptionTimes = 0

def mainLogic():
    global unrarinfo
    global isLogined
    global gExceptionTimes
    com = "telnet 192.168.10.1"
    #com = "telnet 127.0.0.1"
    unrarinfo = subprocess.Popen(com.split(' '), stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    result = None;
    end = "";
    while True:
        if isLogined:
            if gMythread.isAlive():
                if DEBUG:
                    JKLog.d("gMythread.isAlive()")
            else:
                JKLog.d("Command executor is over,exit process!")
                unrarinfo.terminate()
                return
        out = "";
        #print "true,true,true"
        ready = select.select([unrarinfo.stdout, unrarinfo.stderr], [unrarinfo.stdin], [unrarinfo.stdout, unrarinfo.stderr])
        if unrarinfo.stderr in ready[0]:
            err = os.read(unrarinfo.stderr.fileno(), 4096)
            print "-------------------- err: "+err
            sys.stderr.write(err)
            sys.stderr.flush()

        if unrarinfo.stderr in ready[2]:
            err = os.read(unrarinfo.stderr.fileno(), 4096)
            print "+++++++++++++++++++++ err: "+err
            sys.stderr.write(err)
            sys.stderr.flush()
        
        if unrarinfo.stdout in ready[0]:
            out = os.read(unrarinfo.stdout.fileno(), 4096)
            if len(out) > 0 :
                if DEBUG:
                    JKLog.d("len = "+str(len(out)))
            else :
                if DEBUG:
                    JKLog.d("next!!!")
                continue
        elif len(end) > 0 :
            if DEBUG:
                print "deal last info: ",end
            JKLog.d(end)
            if not isLogined:
                Logincheck(end)
            end = ""
            continue
        else :
            if DEBUG:
                print "main next!!!"
            time.sleep(2)
            continue
#         if unrarinfo.stdin in ready[1]:
#             print "stdin can write!"
        

        lastindex = out.rfind('\n')
        record = end + out[:lastindex]
        end = out[lastindex + 1:]
        #print record
        for string in record.splitlines():
            string = string.strip('\n')
            JKLog.d(string)
            if not isLogined:
                Logincheck(string)
            else :
                '''
                    检查是否是在执行命令的状态,如果是的话,检查当前获取的字符串是否是命令结束的标志
                '''
                print "IsCmdException: %d,%s,%s" %(GetStatus(),GetCurCmd()[1],string)
                if GetStatus() == 1 and GetCurCmd()[1]:
                    #如果当前命令结束,开始下一条命令
                    if (len(GetCurCmd()[2]) > 0) and IsCmdFinishFlag(string):
                        SetStatus(0)
                        SetNextCmd()
                    #判断是否是异常结束
                    elif (len(GetCurCmd()[3]) > 0) and IsCmdException(string):
                        print "IsCmdException"
                        gExceptionTimes = gExceptionTimes+1
                        if gExceptionTimes > GetCurCmd()[4]:
                            print "CmdException is more than %d" % GetCurCmd()[4]
                            SetStatus(0)
                            SetNextCmd()
                            gExceptionTimes = 0
                        else :
                            SetStatus(0)
        result = unrarinfo.poll()
    raise LogFormatErr('never get here!!!')


def jkWrite(strings):
    global unrarinfo
    os.write(unrarinfo.stdin.fileno(),strings+"\n")

'''
数据说明:
["ls",False,"","Permission denied",3]

"ls":需要执行的命令行
False:是否需要返回结果,True表示需要,False表示不需要
"": 当上面为False时，此值可以为空,当为True时，需要根据实际命令的输出结果确定成功的关键字
"Permission denied": 异常关键字
3: 表示等待3次异常,如果3次全部异常就pass

'''
mycommands = [
       ["ls",False,"","Permission denied",3],
       [None,None,None]
]

global gCurStatus
'''
gCurStatus 0:表示idle状态
          1:表示正在执行命令,等待返回结果
'''
gCurStatus = 0

def GetStatus():
    global gCurStatus
    return gCurStatus

def SetStatus(status):
    global gCurStatus
    gCurStatus = status

global gCurCmd
gCurCmd = 0

global gWaitingCmd
gWaitingCmd = 0

global gTimeout
gTimeout = 0

def SetCurCmd(cmdindex):
    global gCurCmd
    gCurCmd = cmdindex

def SetNextCmd():
    global gCurCmd
    gCurCmd = gCurCmd+1

def GetCurCmd():
    global gCurCmd
    return mycommands[gCurCmd]

def GetCurCmdIndex():
    global gCurCmd
    return gCurCmd

def IsCmdFinishFlag(strings):
    ma = re.search(GetCurCmd()[2],strings)
    if(ma != None):
        return True
    else:
        return False

def IsCmdException(strings):
    ma = re.search(GetCurCmd()[3],strings)
    if(ma != None):
        return True
    else:
        return False

class ExecuteThreader (threading.Thread):
    def __init__(self,name):
        threading.Thread.__init__(self)
        self.name = name
    def run(self):
        global isLogined
        global gExceptionTimes
        global gWaitingCmd
        global gTimeout
        JKLog.d("Starting " + self.name)
        while True:
            if isLogined:
                if GetStatus() == 0:
                    #命令结束
                    if GetCurCmd()[0] == None:
                        break
                    SetStatus(1)
                    jkWrite(GetCurCmd()[0])
                    time.sleep(2)
                    if not GetCurCmd()[1]:
                        SetStatus(0)
                        SetNextCmd()
                    else:
                        gWaitingCmd = GetCurCmdIndex()
                        gTimeout = 0
                elif GetStatus() == 1:
                    JKLog.d("waiting for result by cmd: %s" % GetCurCmd()[0])
                    time.sleep(2)
                    if gWaitingCmd == GetCurCmdIndex():
                        gTimeout = gTimeout+1
                        if gTimeout > 5:
                            JKLog.d("Timeout is comming for cmd: %s" % GetCurCmd()[0])
                            SetStatus(0)
                            SetNextCmd()
                            gTimeout = 0
            time.sleep(1)
        JKLog.d("Exiting " + self.name)
        sys.exit(0)


def Logincheck(strings):
    global isLogined
    #print "strings: ",strings 
    '''
        这里可以判断是否登入成功,关键字: Last login:
    '''
    ma = re.search('Last login:',strings)
    if(ma != None):
        JKLog.d("login success!!!")
        isLogined = True
        return
    '''
        这里可以判断是否登入成功,关键字: BARRIER BREAKER
    '''
    ma = re.search('BARRIER BREAKER',strings)
    if(ma != None):
        JKLog.d("login success!!!")
        isLogined = True
        return
    '''
        这里判断是否有登入提示信息,关键字: login:
    '''
    ma = re.search('login:',strings)
    if(ma != None):
        if DEBUG:
            JKLog.d("login user!!!")
        jkWrite("jackywei")
        return
    '''
        这里判断是否需要输入密码,关键字: Password:
    '''
    ma = re.search('Password:',strings)
    if(ma != None):
        if DEBUG:
            print "login password!!!"
        JKLog.d("login password!!!")
        jkWrite("mobile#3")
        return

global gMythread

if __name__ == "__main__":
    JKLog.d("**********************************************")
    JKLog.d("* hello start at: %s" % time.strftime('%Y-%m-%d,%H:%M:%S'))
    JKLog.d("**********************************************")
    global gMythread
    gMythread = ExecuteThreader("Command executor")
    gMythread.start()
    mainLogic()
    gMythread.join()
    JKLog.d("process is over!")
    JKLog.d("**********************************************")
    JKLog.d("* hello end at: %s" % time.strftime('%Y-%m-%d,%H:%M:%S'))
    JKLog.d("**********************************************")
