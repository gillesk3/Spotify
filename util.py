import os,sys
import shutil
import configparser
from math import radians, cos, sin, asin, sqrt


Config = configparser.ConfigParser()
Config.read("./resources/Settings.ini")


#Checks if folder exists and creates one if not found
def checkFolder(folder, Input = False, Output=False, path=None ):
    try:
        folder = str(folder)
        rootDir = configSectionMap("Paths")['root']
        if os.path.exists(folder):
            print('Directory already exists')
            return
        #If not directory was given, use root
        if Input:
            folderPath=os.path.join(rootDir,'Inputs')
            folderPath= os.path.join(folderPath,folder)
        elif Output:
            folderPath= os.path.join(rootDir,'Outputs')
            folderPath= os.path.join(folderPath,folder)
        elif path:
            folderPath = os.path.join(path, folder)

        else:
            folderPath = os.path.join(rootDir, folder)

        if not (os.path.exists(folderPath)):
            print('Folder Not Found, Creating Directory: %s' % folder)
            os.makedirs(folderPath)

        return folderPath
    except:
        raise



#Yiels all files in a directory
def files(path):
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            yield file



#Moves files and delets original
def moveFile(path, dst):

    shutil.copy(path, dst )
    os.remove(path)



#Used to get a value from settings file
def configSectionMap(section):
    tmp = {}
    options = Config.options(section)
    for option in options:
        try:
            tmp[option] = Config.get(section, option)
            if tmp[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            tmp[option] = None
    return tmp
