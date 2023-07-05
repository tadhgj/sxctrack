import logging
import io
import ftfy
import copy
from collections import Counter
from math import floor
from decimal import *
import urllib.request as urllib
from urllib.request import urlopen
import socket
import statistics
import functools
import math
import string
from functools import cmp_to_key
from bs4 import BeautifulSoup
import json
import time
import argparse
from ftplib import FTP
import datetime
#for timezone
import pytz
import sys

#wrap entire script in try/except to catch any errors

try:
    #READ COMMAND LING ARGS
    parser = argparse.ArgumentParser(description='silent checking script')
    parser.add_argument('link', action='store', type=str, help='FTP Link')
    parser.add_argument('user', action='store', type=str, help='FTP Username')
    parser.add_argument('passo', action='store', type=str, help='FTP Password')
    parser.add_argument('-textarg', action='store', type=str, help='Input time string if not using default.')
    # you would call -textarg with a string like "1671490801" like so:
    # python3 oneStep.py link user pass -textarg "1671490801"

    # add optional argument called -nuclear with default value False
    parser.add_argument('-nuclear', action='store_true', default=False, help='Re-fetch ALL files from fillmore.homelinux. Will take a long time.')
    # add optional argument called -neuter with default value False
    parser.add_argument('-neuter', action='store_true', default=False, help='Dump in temp but not to curr. Useful for testing.')
    parse_results = parser.parse_args()

    #create var neuter
    textarg = parse_results.textarg
    nuclear = parse_results.nuclear
    neuter = parse_results.neuter


    start_time = int(time.time())
    GMTTime = datetime.datetime.now()
    eastern = pytz.timezone('US/Eastern')
    ESTTime = GMTTime.astimezone(eastern)

    #logging.basicConfig(encoding='utf-8', format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
    #logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

    # COMMON BETWEEN BOTH
    root_logger= logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # or whatever


    #FOR RUNNING ON LOCAL MAC
    handler = logging.FileHandler(filename=str(start_time)+'.log', mode='w', encoding='utf-8')
    handler2 = handler
    handler.setFormatter(logging.Formatter('%(name)s %(message)s')) # or whatever
    root_logger.addHandler(logging.StreamHandler(sys.stdout))

    #FOR RUNNING ON VPS
    # handler = logging.FileHandler('/root/sxctrack/test.log', 'w', 'utf-8') # or whatever 
    # handler2 = logging.FileHandler('/root/sxctrack/logs/'+GMTTime.strftime("GMT_%Y-%m-%d_%H:%M:%S_oneStep.log"), "w", "utf-8") 
    # handler.setFormatter(logging.Formatter('%(name)s %(message)s')) # or whatever 

    # ???
    #to run on macbook...
    #filename=str(start_time)+'.log',
    # ???

    # COMMON BETWEEN BOTH
    root_logger.addHandler(handler) 
    root_logger.addHandler(handler2)
    log_stream = io.StringIO()
    log_handler = logging.StreamHandler(log_stream)
    root_logger.addHandler(log_handler)

    #BEGIN
    logging.info("starting time: " + str(start_time))
    logging.info("GMT Time: " + GMTTime.strftime("%Y-%m-%d, %H:%M:%S"))
    logging.info("EST Time: " + ESTTime.strftime("%Y-%m-%d, %H:%M:%S"))
    logging.info("Starting update check...")

    #LOG INTO FTP
    ftpHost = parse_results.link
    ftpUser = parse_results.user
    ftpPassword = parse_results.passo


    logging.info("logging into FTP...")
    # logging.info("host: "+str(ftpHost)+", user: "+str(ftpUser)+", pass: "+str(ftpPassword)+".")
    # SHOULD NOT LOG LOGIN INFO!
    ftpObject = FTP(ftpHost)

    #attempt ftp login a maximum of 3 times if it fails
    for i in range(3):
        try:
            ftpObject.login(user=ftpUser, passwd=ftpPassword)
            break
        except:
            logging.info("failed to login, trying again...")
            time.sleep(1)
            if i == 2:
                logging.info("failed to login, exiting...")
                exit()
            continue
    logging.info("successful")

    #FTP FUNCTIONS
    #navigate to directory ALWAYS FROM ROOT and create it if it does not exist
    def chdir(dir):
        #navigate to root

        #attempt to navigate to root a maximum of 3 times if it fails
        for i in range(3):
            try:
                ftpObject.cwd("/")
                break
            except:
                logging.info("failed to navigate to root, trying again... (attempt "+str(i)+" of 3)")
                time.sleep(1)
                if i == 2:
                    logging.info("failed to navigate to root, exiting...")
                    exit()
                continue

        #split by /
        dirSplit = dir.split("/")
        #remove empty
        dirSplit = [x for x in dirSplit if x]
        logging.info("chdir: "+str(dirSplit))
        for dirStr in dirSplit:
            if directory_exists(dirStr):
                #attempt to navigate to directory a maximum of 3 times if it fails
                for i in range(3):
                    try:
                        ftpObject.cwd(dirStr)
                        break
                    except:
                        logging.info("failed to navigate to directory "+str(dirStr)+", trying again... (attempt "+str(i)+" of 3)")
                        time.sleep(1)
                        if i == 2:
                            logging.info("failed to navigate to directory, exiting...")
                            exit()
                        continue

            else:
                logging.info("creating new dir '"+dirStr+"' at "+str(ftpObject.pwd()))
                #attempt to make directory a maximum of 3 times if it fails
                for i in range(3):
                    try:
                        ftpObject.mkd(dirStr)
                        break
                    except:
                        logging.info("failed to make directory "+str(dirStr)+", trying again... (attempt "+str(i)+" of 3)")
                        time.sleep(1)
                        if i == 2:
                            logging.info("failed to make directory, exiting...")
                            exit()
                        continue
                
                #attempt to navigate to directory a maximum of 3 times if it fails
                for i in range(3):
                    try:
                        ftpObject.cwd(dirStr)
                        break
                    except:
                        logging.info("failed to navigate to directory "+str(dirStr)+", trying again... (attempt "+str(i)+" of 3)")
                        time.sleep(1)
                        if i == 2:
                            logging.info("failed to navigate to directory, exiting...")
                            exit()
                        continue




    #helper function
    def directory_exists(dir):
        filelist = []
        #attempt to get file list a maximum of 3 times if it fails
        for i in range(3):
            try:
                ftpObject.retrlines('LIST', filelist.append)
                break
            except:
                logging.info("failed to get file list, trying again... (attempt "+str(i)+" of 3)")
                time.sleep(1)
                if i == 2:
                    logging.info("failed to get file list, exiting...")
                    exit()
                continue

        for f in filelist:
            if f.split()[-1] == dir and f.upper().startswith('D'):
                return True
        return False


    #store ftp file to variable
    def getFileFTP(fileNameStr):
        pythonData = io.BytesIO()
        #attempt to get file a maximum of 3 times if it fails
        for i in range(3):
            try:
                ftpObject.retrbinary('RETR ' + fileNameStr, pythonData.write)
                break
            except:
                logging.info("failed to get file, trying again... (attempt "+str(i)+" of 3)")
                time.sleep(1)
                if i == 2:
                    logging.info("failed to get file, exiting...")
                    exit()
                continue
        return pythonData.getvalue()


    #delete all files within a folder
    def deleteFilesInDir(dir):
        logging.info("deleting all files in '"+str(dir)+"'")

        # navigate to root
        #attempt to navigate to root a maximum of 3 times if it fails
        for i in range(3):
            try:
                ftpObject.cwd("/")
                break
            except:
                logging.info("failed to navigate to root, trying again... (attempt "+str(i)+" of 3)")
                time.sleep(1)
                if i == 2:
                    logging.info("failed to navigate to root, exiting...")
                    exit()
                continue

        # split by /
        dirSplit = dir.split("/")
        # remove empty
        dirSplit = [x for x in dirSplit if x]
        #print(dirSplit)
        for dirStr in dirSplit:
            if directory_exists(dirStr):
                # attempt to navigate to directory a maximum of 3 times if it fails
                for i in range(3):
                    try:
                        ftpObject.cwd(dirStr)
                        break
                    except:
                        logging.info("failed to navigate to directory " + str(dirStr) + ", trying again... (attempt " + str(i) + " of 3)")
                        time.sleep(1)
                        if i == 2:
                            logging.info("failed to navigate to directory, exiting...")
                            exit()
                        continue
            else:
                logging.info("Did not delete items in " + dirStr + ", directory does not exist")
                return

        #find all items in directory...
        itemList = ftpObject.nlst()
        logging.info("files: "+str(itemList))
        for i in enumerate(itemList):
            logging.info("testing item '"+str(i[1])+"'")
            if directory_exists(i[1]):
                logging.info("this is a directory...")
                deleteFilesInDir(dir + i[1] + "/")
                chdir(dir)
                #attempt to remove directory a maximum of 3 times if it fails
                for j in range(3):
                    try:
                        ftpObject.rmd(dir + i[1])
                        break
                    except:
                        logging.info("failed to remove directory, trying again... (attempt "+str(j)+" of 3)")
                        time.sleep(1)
                        if j == 2:
                            logging.info("failed to remove directory, exiting...")
                            exit()
                        continue

            else:
                logging.info("deleting '" + dir + str(i[1]) + "'")
                #attempt to delete file a maximum of 3 times if it fails
                for j in range(3):
                    try:
                        ftpObject.delete(dir + i[1])
                        break
                    except:
                        logging.info("failed to delete file, trying again... (attempt "+str(j)+" of 3)")
                        time.sleep(1)
                        if j == 2:
                            logging.info("failed to delete file, exiting...")
                            exit()
                        continue


    #move one folder's contents to another folder
    def moveContents(dir, newDir):
        logging.info("moving files from '"+dir+"' to '"+newDir+"'")
        # navigate to root
        #attempt to navigate to root a maximum of 3 times if it fails
        for i in range(3):
            try:
                ftpObject.cwd("/")
                break
            except:
                logging.info("failed to navigate to root, trying again... (attempt "+str(i)+" of 3)")
                time.sleep(1)
                if i == 2:
                    logging.info("failed to navigate to root, exiting...")
                    exit()
                continue

        # split by /
        dirSplit = dir.split("/")
        # remove empty
        dirSplit = [x for x in dirSplit if x]
        #print(dirSplit)
        for dirStr in dirSplit:
            if directory_exists(dirStr):
                # attempt to navigate to directory a maximum of 3 times if it fails
                for i in range(3):
                    try:
                        ftpObject.cwd(dirStr)
                        break
                    except:
                        logging.info("failed to navigate to directory " + str(dirStr) + ", trying again... (attempt " + str(i) + " of 3)")
                        time.sleep(1)
                        if i == 2:
                            logging.info("failed to navigate to directory, exiting...")
                            exit()
                        continue

            else:
                logging.info("Did not move contents " + dirStr + ", directory does not exist")
                return

        #find all items in directory...
        itemList = ftpObject.nlst()
        for i in enumerate(itemList):
            #print(i)
            #rename file
            currDir = dir
            fileName = i[1]
            print("moving '"+currDir+""+str(fileName)+"' to "+str(newDir)+fileName)
            #attempt to rename file a maximum of 3 times if it fails
            for i in range(3):
                try:
                    ftpObject.rename(currDir+""+fileName, newDir+""+fileName)
                    break
                except:
                    logging.info("failed to rename file, trying again... (attempt "+str(i)+" of 3)")
                    time.sleep(1)
                    if i == 2:
                        logging.info("failed to rename file, exiting...")
                        exit()
                    continue
        #print(str(itemList))


    def copyFile(fullFileName, targetDir):
        # navigate to root
        #attempt to navigate to root a maximum of 3 times if it fails
        for i in range(3):
            try:
                ftpObject.cwd("/")
                break
            except:
                logging.info("failed to navigate to root, trying again... (attempt "+str(i)+" of 3)")
                time.sleep(1)
                if i == 2:
                    logging.info("failed to navigate to root, exiting...")
                    exit()
                continue

        # split by /
        dirSplit = fullFileName.split("/")
        fileName = dirSplit[-1]
        dirSplit = dirSplit[:-1]
        dirSplit = dirSplit[1:]
        #logging.info("dirSplit: "+str(dirSplit))
        # remove empty
        dirSplit = [x for x in dirSplit if x]
        # print(dirSplit)
        for dirStr in dirSplit:
            if directory_exists(dirStr):
                # attempt to navigate to directory a maximum of 3 times if it fails
                for i in range(3):
                    try:
                        ftpObject.cwd(dirStr)
                        break
                    except:
                        logging.info("failed to navigate to directory " + str(dirStr) + ", trying again... (attempt " + str(i) + " of 3)")
                        time.sleep(1)
                        if i == 2:
                            logging.info("failed to navigate to directory, exiting...")
                            exit()
                        continue
            else:
                logging.info("Did not move file " + str(fullFileName) + ", directory does not exist")
                return

        #logging.info("fileName: "+str(fileName))

        logging.info("FILE: copying file '"+fullFileName+"' ("+fileName+") to '" + targetDir + "'")
        fileTempBytes = io.BytesIO(getFileFTP(fileName))

        chdir(targetDir)

        #attempt to store file a maximum of 3 times if it fails
        for i in range(3):
            try:
                ftpObject.storbinary('STOR '+fileName, fileTempBytes)
                break
            except:
                logging.info("failed to store file, trying again... (attempt "+str(i)+" of 3)")
                time.sleep(1)
                if i == 2:
                    logging.info("failed to store file, exiting...")
                    exit()
                continue

        #go back to prev. directory
        chdir("/"+joinArr(dirSplit, "/")+"/")

        logging.info("FILE: success")


    def copyContents(dir, newDir):
        # navigate to root
        # attempt to navigate to root a maximum of 3 times if it fails
        for i in range(3):
            try:
                ftpObject.cwd("/")
                break
            except:
                logging.info("failed to navigate to root, trying again... (attempt " + str(i) + " of 3)")
                time.sleep(1)
                if i == 2:
                    logging.info("failed to navigate to root, exiting...")
                    exit()
                continue
        # split by /
        dirSplit = dir.split("/")
        # remove empty
        dirSplit = [x for x in dirSplit if x]
        # print(dirSplit)
        for dirStr in dirSplit:
            if directory_exists(dirStr):
                # attempt to navigate to directory a maximum of 3 times if it fails
                for i in range(3):
                    try:
                        ftpObject.cwd(dirStr)
                        break
                    except:
                        logging.info("failed to navigate to directory " + str(dirStr) + ", trying again... (attempt " + str(i) + " of 3)")
                        time.sleep(1)
                        if i == 2:
                            logging.info("failed to navigate to directory, exiting...")
                            exit()
                        continue

            else:
                logging.info("Did not move contents of " + str(dir) + ", directory does not exist")
                return

        # find all items in directory...
        # attempt to get list of files a maximum of 3 times if it fails
        for i in range(3):
            try:
                itemList = ftpObject.nlst()
                break
            except:
                logging.info("failed to get list of files, trying again... (attempt " + str(i) + " of 3)")
                time.sleep(1)
                if i == 2:
                    logging.info("failed to get list of files, exiting...")
                    exit()
                continue

        logging.info("DIR: copying files from '"+dir+"' to '" + newDir + "' - "+str(itemList))
        #logging.info("thing list: "+str(itemList))
        for i in enumerate(itemList):
            chdir(dir)
            logging.info("testing item '" + str(i[1]) + "'")
            #check if this is yet another directory...
            if directory_exists(i[1]):
                #logging.info("item '"+i[1]+"' is a dir...")
                chdir(newDir+i[1]+"/")
                copyContents(dir+i[1]+"/", newDir+i[1]+"/")
            else:
                # print(i)
                #logging.info("copying " + str(i[1]) + " to " + str(newDir))
                # rename file
                currDir = dir
                fileName = i[1]
                copyFile(currDir+fileName, newDir)
        logging.info("DIR: success ("+dir+" -> "+newDir+")")


    def joinArr(list, separator=", "):
        return separator.join(list)


    #REMOTE PAGE FUNCTIONS

    def fetch_remote_page(url):
        page = "err"
        # attempt to open page a maximum of 3 times if it fails
        for i in range(3):
            try:
                page = urlopen(url, timeout=30)
                if i > 0:
                    logging.info("success on attempt " + str(i+1))
                break
            except socket.timeout as n:
                logging.error("Socket error on attempt " + str(i+1) + " of 3")
                logging.error(n)
                time.sleep(1)
                page = "err"
                continue
            except urllib.URLError as n:
                logging.error("Could not open page. Attempt " + str(i+1) + " of 3")
                logging.error(n)
                time.sleep(1)
                page = "err"
                continue
        return page


    #specifically for http://fillmore.homelinux.net/cgi-bin/Meets?year=*
    def parse_remote_meet_page(page_data):
        # read page_data
        read_data = page_data.read()

        # decode by utf-8
        html = read_data.decode("utf-8")

        # use beautifulsoup
        soup = BeautifulSoup(html, "html.parser")

        # THIS IS SPECIFIC TO THIS SPECIFIC FILLMORE.HOMELINUX.NET PAGE
        # main table
        meet_table = soup.find("form").table

        # row array (recursive=False, just in case)
        row_list = meet_table.find_all("tr", recursive=False)

        # remove the title row (contains search bars and other stuff not useful)
        row_list.pop(0)

        # now, the fun part
        remote_meets_array = []

        for temp_meet in row_list:
            meet_object = {
                "date": temp_meet.find_all("td")[0].getText(),
                "gender": temp_meet.find_all("td")[1].getText(),
                "name": temp_meet.find_all("td")[2].getText(),
                "season": temp_meet.find_all("td")[3].getText(),
                "location": temp_meet.find_all("td")[4].getText(),
                "id": temp_meet.a.get('href').split("=")[1]
            }
            remote_meets_array.append(meet_object)

        # return array
        return remote_meets_array


    def get_ids(objList):
        outputArr = []
        for objTemp in objList:
            outputArr.append(int(objTemp['id']))

        return outputArr

    def findFreshIDs(objList):
        # for every item in objList:
        #   if date is within 2 weeks of today:
        #   if date is now or the future:
        #       add id to outputArr
        # well, you see, anything past two weeks ago would also
        # include meets that are in the future, so we don't need
        # to check for that specifically

        #define today
        today = datetime.date.today()

        #define two weeks ago
        twoWeeksAgo = today - datetime.timedelta(days=14)

        #define output array
        outputArr = []

        #loop through objList
        for objTemp in objList:
            #log date
            # logging.info("date: "+objTemp['date'])

            #get date
            dateTemp = datetime.datetime.strptime(objTemp['date'], "%Y-%m-%d").date()

            #compare date
            if dateTemp > twoWeeksAgo:
                #add id to outputArr
                outputArr.append(int(objTemp['id']))

        return outputArr

    def find_new_ids(local_list, remote_list):
        #logging.info("local list:"+str(local_list))
        #logging.info("local list:"+str(len(local_list)))
        #logging.info("first item test:"+str(local_list[0]))
        # get array of IDs from local_list
        #just_ids_local = [d['id'] for d in local_list]
        just_ids_local = local_list

        # get array of IDs from remote_list
        #just_ids_remote = [d['id'] for d in remote_list]
        just_ids_remote = remote_list

        # find differences
        # remote - local, assuming that there will be more meets from remote than local
        s = set(just_ids_local)
        diff_array = [x for x in just_ids_remote if x not in s]
        # diff_array = list(set(just_ids_remote) - set(just_ids_local))

        # return array
        return diff_array


    def fetch_basic_remote_data(meet_id):
        #logging.info("all meet ids: "+str(all_meet_ids))
        for obj in remote_basic_data:
            if obj["id"] == str(meet_id):
                return obj

        print("no meet found")
        return "no meet"


    def read_meet_page(meet_id):
        #setup basic obj
        meet_object = fetch_basic_remote_data(meet_id)

        # set url
        meetBaseUrl = "http://fillmore.homelinux.net/cgi-bin/Meet?meet="
        tempUrl = meetBaseUrl + str(meet_id)
        tempPage = fetch_remote_page(tempUrl)

        if tempPage == None:
            logging.error("meet page failed to load")
            meet_object['categories'] = "URLError"
            return meet_object

        # READY BEAUTIFULSOUP
        # parse
        tempHtml_bytes = tempPage.read()
        # decode
        tempHtml = tempHtml_bytes.decode("utf-8")
        # soup
        tempSoup = BeautifulSoup(tempHtml, "html.parser")

        #ready local variables
        trList = []

        # h3 = meet annotation
        meet_object["annotation"] = tempSoup.h3.getText()

        # check if there's a footer
        if len(tempSoup.find_all("div", recursive=False)) > 1:
            #print("possible footer")
            temp_footer = str(tempSoup.find_all("div", class_="main")[0])
            temp_footer = temp_footer.split('<div class="main">')[1]
            temp_footer = temp_footer.split('</div>')[0]
            temp_footer = temp_footer.replace("\r", "")
            temp_footer = temp_footer.replace("<br/>", "\r")
            temp_footer = temp_footer.replace("\r \r", "\r\r")
            meet_object["footer"] = temp_footer
        else:
            #print("no footer")
            if 'footer' in meet_object:
                meet_object.pop("footer")

        # contains div
        # recursive=False means that it won't find nested tables. perfect.
        tableContainer = tempSoup.find_all("div")[1].find_all("table", recursive=False)

        # throw away empty table elements
        for y in range(len(tableContainer)):
            # start from back because otherwise things get funky
            zed = len(tableContainer) - 1 - y
            if len(tableContainer[zed].find_all("tr")) == 0:
                tableContainer.pop(zed)

        #for the top-level tables on the page
        for z in range(len(tableContainer)):
            #current table row:
            currentThing = tableContainer[z].find_all("tr", recursive=False)

            # for each table row in a top-level table
            for orange in range(len(currentThing)):
                #add to trList array
                trList.append(currentThing[orange])

        #now, go through each table row (these contain either category data or a category title)
        #set up variables
        trTrList = []
        tempTitle = None

        for count in range(len(trList)):
            #check if is title
            if len(trList[count].find_all("th")) == 1:
                # title
                tempTitle = trList[count].find_all("th")[0].getText()
            else:
                # not title. If tempTitle is not None, set this table's title.
                if tempTitle is not None:
                    #add category name to list along with table row data
                    trTrList.append({"name": tempTitle, "data": trList[count]})
                    #reset tempTitle
                    tempTitle = None
                else:
                    #add uncategorized category to list along with table row data
                    trTrList.append({"name": "uncategorized", "data": trList[count]})

        #now, go through each category and find specific event data
        #set up local variables
        tempEventListThing = []
        currentEventTitle = "empty"
        nextEventCount = 0
        relayCount = -1
        tempAthleteList = []
        splits = False
        splitLength = 0
        tempCaptionLength = 0
        currentCaptionList = []

        #for each category
        for secondCount in range(len(trTrList)):
            #find the column count in this category
            tableColumns = trTrList[secondCount]["data"].find_all("td", class_="top")

            #for each column in category
            for currentColumnCount in range(len(tableColumns)):
                #find the table directly within column
                currentColumn = tableColumns[currentColumnCount].find_all("table")[0]

                #for each table row in a column (technically inside the table within the column but whatever)
                for thirdCount in range(len(currentColumn.find_all("tr"))):
                    #either:
                    #title: regular, or with mulitple lines
                    #title with splits: funky
                    #caption row: includes splits if there
                    #data row: can contain relay objects

                    #getting current table row
                    currentRow = currentColumn.find_all("tr")[thirdCount]

                    #count of <th> elements
                    #a title has one
                    #a title with splits has two
                    #a caption row has more than two
                    #a data row has none
                    countToCheck = currentRow.find_all("th", recursive=False)

                    #the extra if condition is so that relay titles don't trigger this
                    if len(countToCheck) == 1 and len(currentRow.find_all("td")) < 1:
                        # title row

                        # if there's been a previous title, save the currently saved information in the tempAthleteList
                        if currentEventTitle != "empty":
                            temp_obj_append = {
                                "title": {
                                    "name": eventName,
                                },
                                "captions": currentCaptionList,

                                "data": tempAthleteList
                            }
                            if splits:
                                temp_obj_append['splits'] = {
                                    "length": splitLength
                                }
                            if courseID != "":
                                temp_obj_append['title']['courseID'] = courseID
                            if secondLine != "":
                                temp_obj_append['title']['addtl'] = secondLine
                            if division != "":
                                #print("adding division line 232 .. "+division)
                                temp_obj_append['title']['div'] = division
                            tempEventListThing.append(temp_obj_append)

                        #this title doesn't have splits
                        splits = False

                        #reset temp athletes (didn't do this before, disastrous)
                        tempAthleteList = []

                        # check for line breaks
                        secondLine = ""
                        if '<br/>' in str(countToCheck[0].decode_contents()):
                            firstLine = str(countToCheck[0].decode_contents()).split('<br/>')[0]
                            secondLine = str(countToCheck[0].decode_contents()).split('<br/>')[1]
                            currentEventTitle = str(countToCheck[0].decode_contents()).split('<br/>')
                        else:
                            firstLine = countToCheck[0].getText()
                            currentEventTitle = countToCheck[0].getText()

                        division = ""
                        courseID = ""
                        firstLineStr = firstLine
                        firstLine = BeautifulSoup(firstLine, "html.parser")
                        if firstLine.find_all("a"):
                            eventName = firstLine.a.getText()
                            division = firstLine.getText().split(" - ", 1)[0]
                            #print("has division line 325 - " + division)
                            href = firstLine.a.get("href")
                            if "course" in href:
                                courseID = href.split("course=", 1)[1].split(";", 1)[0]
                                #print(courseID)
                            #else:
                                #print("no course!")
                        else:
                            if " - " in firstLine:
                                eventName = firstLineStr.rsplit(" - ", 1)[1]
                                division = firstLineStr.rsplit(" - ", 1)[0]
                                #print("has division line 265 - "+division)
                            else:
                                eventName = firstLineStr

                        nextEventCount += 1


                    elif len(countToCheck) == 2:
                        # title row with splits

                        # if there's been a previous title, save the currently saved information in the tempAthleteList
                        if currentEventTitle != "empty":
                            temp_obj_append = {
                                "title": {
                                    "name": eventName,
                                },
                                "captions": currentCaptionList,

                                "data": tempAthleteList
                            }
                            if splits:
                                temp_obj_append['splits'] = {
                                    "length": splitLength
                                }
                            if courseID != "":
                                temp_obj_append['title']['courseID'] = courseID
                            if secondLine != "":
                                temp_obj_append['title']['addtl'] = secondLine
                            if division != "":
                                #print("adding division line 294 .. " + division)
                                temp_obj_append['title']['div'] = division
                            tempEventListThing.append(temp_obj_append)

                        #this row does have splits
                        splits = True

                        # reset temp athletes (didn't do this before, disastrous)
                        tempAthleteList = []

                        # get split length
                        tempCaptionLength = int(countToCheck[0]['colspan'])
                        # splitLength = int(countToCheck[1]['colspan'])

                        # check for line breaks
                        secondLine = ""
                        if '<br/>' in str(countToCheck[0].decode_contents()):
                            firstLine = str(countToCheck[0].decode_contents()).split('<br/>')[0]
                            secondLine = str(countToCheck[0].decode_contents()).split('<br/>')[1]
                            currentEventTitle = str(countToCheck[0].decode_contents()).split('<br/>')
                        else:
                            firstLine = countToCheck[0].getText()
                            currentEventTitle = countToCheck[0].getText()

                        division = ""
                        courseID = ""
                        firstLineStr = firstLine
                        firstLine = BeautifulSoup(firstLine, "html.parser")
                        if firstLine.find_all("a"):
                            eventName = firstLine.a.getText()
                            division = firstLine.getText().split(" - ", 1)[0]
                            #print("has division line 325 - " + division)
                            href = firstLine.a.get("href")
                            #hrefParse = urlparse(href)
                            #courseID = parse_qs(hrefParse.query)['course'][0]
                            if "course" in href:
                                courseID = href.split("course=", 1)[1].split(";", 1)[0]
                                #print(courseID)
                            #else:
                                #print("no course!")
                        else:
                            if " - " in firstLine:
                                eventName = firstLineStr.rsplit(" - ", 1)[1]
                                division = firstLineStr.rsplit(" - ", 1)[0]
                                #print("has division line 331 - " + division)
                            else:
                                eventName = firstLineStr

                        nextEventCount += 1


                    elif len(countToCheck) > 2:
                        # caption row

                        # reset previous captions
                        currentCaptionList = []

                        # print("caption row:")

                        # check if the current title has splits

                        #how many captions need to be saved
                        for banana in countToCheck:
                            currentCaptionList.append(banana.getText())

                        if splits:
                            # print("this caption has splits")
                            splitLength = len(currentCaptionList) - tempCaptionLength

                    else:
                        # data row

                        # check if current row is a relay title
                        if len(countToCheck) > 0:
                            # relay title

                            #find how many athletes in this relay object
                            #check if there are any rows at all, thanks to the one relay with nobody in it that
                            #caused one too many fatal errors

                            if currentRow.find_all("th", rowspan=True):

                                relayCount = (int(countToCheck[0]['rowspan']) - 1)
                                if relayCount == 0:
                                    # print("there's only one person in this relay. odd.")

                                    # pr check
                                    if len(currentRow.find_all("td")[2].find_all("a")) > 0:
                                        # there is a PR in this relay entry
                                        relayAthleteObj = {
                                            "name": currentRow.find_all("td")[1].getText(),
                                            "id": currentRow.find_all("td")[1].a.get('href').split("=")[1],
                                            "individual": currentRow.find_all("td")[2].b.getText().split("*")[0],
                                            "pr": currentRow.find_all("td")[2].a.getText(),
                                            "prID": currentRow.find_all("td")[2].a.get('href').split("=")[1]
                                        }
                                    elif len(currentRow.find_all("td")[2].find_all("b")) > 0 and "*" in \
                                            currentRow.find_all("td")[2].b.getText():
                                        relayAthleteObj = {
                                            "name": currentRow.find_all("td")[1].getText(),
                                            "id": currentRow.find_all("td")[1].a.get('href').split("=")[1],
                                            "individual": currentRow.find_all("td")[2].b.getText().split("*")[0],
                                            "pr": "PR",
                                        }
                                    else:
                                        #no PR
                                        relayAthleteObj = {
                                            "name": currentRow.find_all("td")[1].getText(),
                                            "id": currentRow.find_all("td")[1].a.get('href').split("=")[1],
                                            "individual": currentRow.find_all("td")[2].getText()
                                        }

                                    #set up relay object
                                    tempRelayObject = {
                                        currentCaptionList[0]: currentRow.find_all("td")[0].getText(),
                                        currentCaptionList[1]: countToCheck[0].getText(),
                                        "Athletes": [relayAthleteObj],
                                        currentCaptionList[3]: currentRow.find_all("td")[len(currentRow.find_all("td")) - 1].getText()
                                    }
                                    tempAthleteList.append(tempRelayObject)
                                    continue
                            else:
                                #nobody in this relay. stupid.

                                relayCount = -1

                                #set up temp relay object
                                tempRelayObject = {
                                    currentCaptionList[0]: currentRow.find_all("td")[0].getText(),
                                    currentCaptionList[1]: countToCheck[0].getText(),
                                    "Athletes": ["empty"],
                                    currentCaptionList[3]: currentRow.find_all("td")[len(currentRow.find_all("td")) - 1].getText()
                                }
                                tempAthleteList.append(tempRelayObject)
                                continue


                            #neither 1 nor zero people in the relay

                            # pr check

                            if len(currentRow.find_all("td")[2].find_all("a")) > 0:
                                # there is a PR in this relay entry
                                relayAthleteObj = {
                                    "name": currentRow.find_all("td")[1].getText(),
                                    "id": currentRow.find_all("td")[1].a.get('href').split("=")[1],
                                    "individual": currentRow.find_all("td")[2].b.getText().split("*")[0],
                                    "pr": currentRow.find_all("td")[2].a.getText(),
                                    "prID": currentRow.find_all("td")[2].a.get('href').split("=")[1]
                                }
                            elif len(currentRow.find_all("td")[2].find_all("b")) > 0 and "*" in currentRow.find_all("td")[
                                2].b.getText():
                                relayAthleteObj = {
                                    "name": currentRow.find_all("td")[1].getText(),
                                    "id": currentRow.find_all("td")[1].a.get('href').split("=")[1],
                                    "individual": currentRow.find_all("td")[2].b.getText().split("*")[0],
                                    "pr": "PR"
                                }
                            else:
                                relayAthleteObj = {
                                    "name": currentRow.find_all("td")[1].getText(),
                                    "id": currentRow.find_all("td")[1].a.get('href').split("=")[1],
                                    "individual": currentRow.find_all("td")[2].getText()
                                }

                            #set up relay object
                            tempRelayObject = {
                                currentCaptionList[0]: currentRow.find_all("td")[0].getText(),
                                currentCaptionList[1]: countToCheck[0].getText(),
                                "Athletes": [relayAthleteObj],
                                currentCaptionList[3]: currentRow.find_all("td")[len(currentRow.find_all("td")) - 1].getText()
                            }

                        #not a relay title
                        else:
                            #check if still in a relay object
                            if relayCount > 0:
                                #still in relay

                                #check if this relay entry is a PR
                                # pr check

                                if len(currentRow.find_all("td")[1].find_all("a")) > 0:
                                    # there is a PR in this relay entry
                                    relayAthleteObj = {
                                        "name": currentRow.find_all("td")[0].getText(),
                                        "id": currentRow.find_all("td")[0].a.get('href').split("=")[1],
                                        "individual": currentRow.find_all("td")[1].b.getText().split("*")[0],
                                        "pr": currentRow.find_all("td")[1].a.getText(),
                                        "prID": currentRow.find_all("td")[1].a.get('href').split("=")[1]
                                    }
                                elif len(currentRow.find_all("td")[1].find_all("b")) > 0 and "*" in currentRow.find_all("td")[1].b.getText():
                                    relayAthleteObj = {
                                        "name": currentRow.find_all("td")[0].getText(),
                                        "id": currentRow.find_all("td")[0].a.get('href').split("=")[1],
                                        "individual": currentRow.find_all("td")[1].b.getText().split("*")[0],
                                        "pr": "PR",
                                    }
                                else:
                                    relayAthleteObj = {
                                        "name": currentRow.find_all("td")[0].getText(),
                                        "id": currentRow.find_all("td")[0].a.get('href').split("=")[1],
                                        "individual": currentRow.find_all("td")[1].getText()
                                    }

                                #add athlete to relay object
                                tempRelayObject["Athletes"].append(relayAthleteObj)

                                #decrease current count of remaining relay athletes expected
                                relayCount = relayCount - 1

                                # check if this is the last athlete.
                                # if it is, append the relay table and clear it in preparation for the next line
                                if relayCount == 0:
                                    tempAthleteList.append(tempRelayObject)
                                    relayCount = -1
                                    #very important that temporary tables are cleared
                                    tempRelayObject = []

                            else:
                                #not in relay, regular old data row

                                #setup temp athlete obj
                                tempAthleteObj = {}

                                #for each caption
                                for tomato in range(len(currentRow.find_all("td"))):
                                    #athlete check (need to capture athlete ID here)
                                    if currentCaptionList[tomato] == "Athlete":
                                        tempAthleteObj["name"] = currentRow.find_all("td")[tomato].getText()
                                        tempAthleteObj["id"] = currentRow.find_all("td")[tomato].a.get('href').split("=")[1]

                                    #pr check
                                    elif len(currentRow.find_all("td")[tomato].find_all("a")) > 0:
                                        # print("personal record here")
                                        tempAthleteObj[currentCaptionList[tomato]] = \
                                        currentRow.find_all("td")[tomato].b.getText().split("*")[0]
                                        tempAthleteObj["pr"] = currentRow.find_all("td")[tomato].a.getText()
                                        tempAthleteObj["prID"] = currentRow.find_all("td")[tomato].a.get('href').split("=")[1]

                                        #also check for split even if it's a pr
                                        if currentRow.find_all("td")[tomato].has_attr('title'):
                                            #there is splits
                                            tempAthleteObj['splits'] = currentRow.find_all("td")[tomato].get('title')

                                    # other row (place, time, pace {which should be ignored})
                                    elif currentCaptionList[tomato] == "Time" or currentCaptionList[tomato] == "Mark":
                                        #check if it's a PR without link




                                        #check if there is title
                                        if currentRow.find_all("td")[tomato].has_attr('title'):
                                            #there is splits
                                            #print("splits")
                                            tempAthleteObj['splits'] = currentRow.find_all("td")[tomato].get('title')

                                        if len(currentRow.find_all("td")[tomato].find_all("b")) > 0:
                                            # something is bold, it would be a PR
                                            tempAthleteObj["pr"] = currentRow.find_all("td")[tomato].getText().split("* ")[1]
                                            # should it be blank or non-existent?
                                            tempAthleteObj["prID"] = ""
                                            tempAthleteObj[currentCaptionList[tomato]] = currentRow.find_all("td")[tomato].getText().split("*")[0]
                                        else:
                                            tempAthleteObj[currentCaptionList[tomato]] = currentRow.find_all("td")[tomato].getText()

                                    else:
                                        tempAthleteObj[currentCaptionList[tomato]] = currentRow.find_all("td")[tomato].getText()

                                #save to tempAthleteList
                                tempAthleteList.append(tempAthleteObj)
                    #end of table row
                #end of column
                #save event data

                #pop paces from captions
                #print(currentCaptionList)
                temp_length = len(currentCaptionList)
                for captionCount in range(temp_length):
                    backwards = temp_length-1-captionCount
                    if currentCaptionList[backwards] == "Pace/km" or currentCaptionList[backwards] == "Pace/mile":
                        currentCaptionList.remove(currentCaptionList[backwards])

                #pop paces from data
                for event in tempAthleteList:
                    if "Pace/km" in event:
                        event.pop("Pace/km")

                    if "Pace/mile" in event:
                        event.pop("Pace/mile")

                if currentEventTitle != "empty":
                    temp_obj_append = {
                        "title": {
                            "name": eventName,
                        },
                        "captions": currentCaptionList,

                        "data": tempAthleteList
                    }
                    if splits:
                        temp_obj_append['splits'] = {
                            "length": splitLength
                        }
                    if courseID != "":
                        temp_obj_append['title']['courseID'] = courseID
                    if secondLine != "":
                        temp_obj_append['title']['addtl'] = secondLine
                    if division != "":
                        #print("adding division line 580 .. " + division)
                        temp_obj_append['title']['div'] = division
                    tempEventListThing.append(temp_obj_append)

                #reset variables
                splits = False
                currentEventTitle = "empty"
                currentCaptionList = []
                relayCount = -1
                splitLength = 0
                tempCaptionLength = 0
                tempAthleteList = []

            #end of category
            trTrList[secondCount]["data2"] = tempEventListThing
            tempEventListThing = []
            nextEventCount = 0

        #end of page
        #format things nicely
        for fourthCount in range(len(trTrList)):
            trTrList[fourthCount]["events"] = trTrList[fourthCount]["data2"]
            trTrList[fourthCount].pop("data")
            trTrList[fourthCount].pop("data2")

        meet_object["events"] = {"categories": trTrList}

        #ADD TIMESTAMPS

        return meet_object


    def attempt_list_of_ids(id_list):
        # start failure list in case URL does not load
        failure_list = []

        # start result data list
        result_list = []

        # default cooldown of 3 seconds between
        for count in range(0, len(id_list)):
            # set up current id
            id = int(id_list[count])

            # fetch url data
            id_data = read_meet_page(id)

            # if failure, retry a maximum of 3 times
            if id_data == "URL failure":
                    # add to failure list
                    failure_list.append(id)
                    # add to result list
                    result_list.append(id_data) 
            else:
                # add to result list
                result_list.append(id_data)

            # print
            logging.info("Progress: " + str(count + 1) + "/" + str(len(id_list)) + ", " + str((round(((count + 1) / len(id_list)) * 10000)) / 100) + "%")

            # cooldown
            time.sleep(4)

        # completed list
        logging.info("Completed list. " + str(len(failure_list)) + " Failed, " + str(
            len(result_list) - len(failure_list)) + " Succeeded.")

        # save failed IDs to text file
        #
        #with open("failed_meet_ids.txt", "a") as outfile:
            #json.dump(failure_list, outfile)

        # return result list
        return result_list


    #depreciated! use merge_meet_data instead
    # (merge_meet_data doesn't create duplicate entries)
    def addToLocal(old_array, new_array):
        # add new array to beginning of old array
        return new_array + old_array

    def merge_meet_data(old_data, new_data):
        # print("merge meet data!")

        # merge new data into old data

        # get ids from both
        old_ids = get_ids(old_data)
        new_ids = get_ids(new_data)
        # print("old ids count:"+str(len(old_data)))


        # list of ids in new_ids that are not in old_ids
        new_ids_not_in_old_ids = []

        # list of meets to append!
        meets_to_append = []

        # iterate thru new_ids
        for id in new_ids:
            if not id in old_ids:
                new_ids_not_in_old_ids.append(id)

        overWriteCount = 0
        # iterate thru new_data
        for meet in new_data:
            # check if id is in new_ids_not_in_old_ids
            if str(meet['id']) in str(new_ids_not_in_old_ids):
                meets_to_append.append(meet)
            
            # if this meet is already in old_data, overwrite it
            else:
                #iterate using index
                for index in range(len(old_data)):
                    #check if id is the same
                    # print("old meet id:"+str(old_meet['id'])+" meet id:"+str(meet['id']))
                    if old_data[index]['id'] == meet['id']:
                        #overwrite
                        old_data[index] = meet
                        overWriteCount+=1
            

        # print("meets to append:"+str(len(meets_to_append)))

        # add meets to append to old_data
        output = meets_to_append + old_data

        #debug 
        # print("old ids now:"+str(len(output)))
        # print(str(len(new_ids)))
        # print("new ids not in old ids: " + str(new_ids_not_in_old_ids))


        return output


    def getAthleteIdsFromData(input_data):
        athlete_id_array = []
        # iterate thru categories
        for meet_obj in input_data:
            for category in meet_obj['events']['categories']:
                for current_event in category['events']:
                    for data_point in current_event['data']:
                        # debug
                        # print(data_point)
                        # check if relay or normal
                        if "Team" in data_point.keys():
                            # relay
                            if not data_point['Athletes'][0] == 'empty':
                                for relay_ath in data_point['Athletes']:
                                    # print(relay_ath['id'])
                                    if not relay_ath['id'] in athlete_id_array:
                                        athlete_id_array.append(relay_ath['id'])
                        else:
                            # print(data_point['id'])
                            if not data_point['id'] in athlete_id_array:
                                athlete_id_array.append(data_point['id'])

        return athlete_id_array


    def read_athlete_page(ath_id):
        athBaseUrl = "http://fillmore.homelinux.net/cgi-bin/Athlete?athlete="

        # set url
        tempUrl = athBaseUrl + str(ath_id)

        # attempt to load URL
        tempPage = fetch_remote_page(tempUrl)

        # url good

        # READY BEAUTIFULSOUP
        # parse
        tempHtml_bytes = tempPage.read()
        # decode
        tempHtml = tempHtml_bytes.decode("utf-8")
        # soup
        tempSoup = BeautifulSoup(tempHtml, "html.parser")

        # ready local variables
        # meet_object = fetch_basic_remote_data(meet_id)
        ath_object = previous_athlete_data(ath_id)
        tempRaceList = []

        # overwrite races object of athlete here...
        athleteRaceTable = tempSoup.find_all("table")[len(tempSoup.find_all("table")) - 1]
        # if athleteRaceTable
        # print(tempSoup.find_all("table")[len(tempSoup.find_all("table"))-1])
        # print("")
        # print("")
        # check if athlete has no races
        # athletes with no races will have a different table here, containing an <option> tag
        if athleteRaceTable.td is not None:
            # split by rows
            athleteRaceList = athleteRaceTable.find_all("tr")
            # remove first one, the title row
            athleteRaceList.pop(0)
            for y in athleteRaceList:
                tempDictionary = {
                    # determined from
                    "date": y.find_all("td")[0].getText(),

                    "meetID": y.a.get('href').split("=")[1],
                    "meetName": y.a.getText(),
                    "eventName": y.find_all("td")[2].getText(),

                    "place": y.find_all("td")[3].getText(),
                    "time": y.find_all("td")[4].getText(),
                    "points": y.find_all("td")[5].getText(),
                    "PacePerMile": y.find_all("td")[6].getText(),
                    "PacePerKilo": y.find_all("td")[7].getText(),
                    "splits": [],
                    # y.find_all("td")[8].getText()
                }
                for j in range(len(y.find_all("td")) - 8):
                    # if len(y.find_all("td"))-8 > 1:
                    #    if y.find_all("td")[j+8].getText() == "":
                    #        break
                    tempDictionary["splits"].append(y.find_all("td")[j + 8].getText())
                # print(tempDictionary)

                # pop empty things
                if tempDictionary["place"] == "":
                    tempDictionary.pop("place")
                if tempDictionary["points"] == "":
                    tempDictionary.pop("points")
                if tempDictionary["PacePerMile"] == "":
                    tempDictionary.pop("PacePerMile")
                if tempDictionary["PacePerKilo"] == "":
                    tempDictionary.pop("PacePerKilo")
                if tempDictionary["splits"] == ['', '', '']:
                    tempDictionary.pop("splits")

                tempRaceList.append(tempDictionary)
            # print(tempRaceList)
        else:
            # they have no races
            logging.info("no races for " + ath_object["name"])
        ath_object["races"] = tempRaceList

        return ath_object


    def attempt_list_of_ath_ids(id_list):
        # start failure list in case URL does not load
        failure_list = []

        # start result data list
        result_list = []

        for count in range(0, len(id_list)):
            # set up current id
            id = int(id_list[count])

            # fetch url data
            id_data = read_athlete_page(id)

            # check for failure
            if id_data == "URL failure":
                # add to failure list
                failure_list.append(id)
                # add to result list
                result_list.append(id_data)

            # no failure
            else:
                # add to result list
                result_list.append(id_data)


            logging.info("Progress: " + str(count + 1) + "/" + str(len(id_list)) + ", " + str(
                (round(((count + 1) / len(id_list)) * 10000)) / 100) + "%")

            # cooldown
            time.sleep(4)

        # completed list
        logging.info("Completed list. " + str(len(failure_list)) + " Failed, " + str(
            len(result_list) - len(failure_list)) + " Succeeded.")

        # save failed IDs to text file
        #with open("failed_ath_ids.txt", "a") as outfile:
        #    json.dump(failure_list, outfile)

        # return result list
        return result_list


    def previous_athlete_data(ath_id):
        # only run after list is created?
        #logging.info("locals:"+str(locals()))
        if 'new_athlete_list_without_new_events' in globals():
            index_list = []

            for item in new_athlete_list_without_new_events:
                index_list.append(item['id'])

            # print("id: "+str(ath_id)+", id_index: "+str(index_list.index(''+ath_id+'')))

            return new_athlete_list_without_new_events[index_list.index(str(ath_id))]
        else:
            logging.warning("list not created yet...")
            return


    def create_new_athlete_list(local_file, remote_list):
        # create new list based on remote list
        local_file_id_list = []
        # json.dumps([ath['id'] for ath in local_file])
        # I think this made a string, which caused issues when looking for indices

        for item in local_file:
            local_file_id_list.append(item['id'])

        output_list = remote_list

        for count in range(len(output_list)):
            if output_list[count]['id'] in local_file_id_list:
                index_in_local = local_file_id_list.index(output_list[count]['id'])
                # print("athlete data from local: ")
                # print(local_file[index_in_local])
                output_list[count] = local_file[index_in_local]
            else:
                output_list[count] = {
                    "id": output_list[count]['id'],
                    "name": output_list[count]['name'],
                    "graduationYear": output_list[count]['graduationYear'],
                    "races": []
                }

        return output_list


    def add_new_data_to_big_list(new_data, big_list):
        big_list_index = []
        for item in big_list_index:
            big_list_index.append(item['id'])

        new_data_index = []
        for item in new_data_index:
            new_data_index.append(item['id'])

        for newID in new_data_index:
            big_list[big_list_index.index(newID)] = new_data[newID]

        return big_list


    def fetch_remote_athlete_list(url):
        return fetch_remote_page(url)


    def parse_remote_athlete_list(page_data):
        # output var
        remote_athlete_list_output = []

        # read page_data
        read_data = page_data.read()

        # decode by utf-8
        html = read_data.decode("utf-8")

        # use beautifulsoup
        soup = BeautifulSoup(html, "html.parser")

        # THIS IS SPECIFIC TO THIS SPECIFIC FILLMORE.HOMELINUX.NET PAGE
        # main table
        athlete_table = soup.find("body").find_all("table")[2]

        # row array (recursive=False, just in case)
        row_list = athlete_table.find_all("tr", recursive=False)

        # remove the title row (contains search bars and other stuff not useful)
        row_list.pop(0)

        # now, the fun part
        remote_athletes_array = []

        for temp_ath in row_list:
            athlete_object = {
                "name": temp_ath.find_all("td")[0].getText(),
                "graduationYear": temp_ath.find_all("td")[1].getText(),
                "id": temp_ath.a.get('href').split("=")[1]
            }
            remote_athlete_list_output.append(athlete_object)

        # return array
        return remote_athlete_list_output


    def getOnlineAthleteOrder():

        # fetch data
        online_athlete_page = fetch_remote_athlete_list('http://fillmore.homelinux.net/cgi-bin/Athletes')

        # parse list
        online_athlete_list = parse_remote_athlete_list(online_athlete_page)

        return online_athlete_list



    #GENDER FUNCTIONS
    def getBests(season, gender):
        # load bests page
        # example:

        # BETTER EXAMPLE:
        # females indoor
        # http://fillmore.homelinux.net/cgi-bin/Bests?range=all&season=Indoor&sex=F

        # cross country season URL:
        # http://fillmore.homelinux.net/cgi-bin/Bests?range=all&season=Cross+Country
        cross_country_url = "http://fillmore.homelinux.net/cgi-bin/Bests?range=all&season=Cross+Country"
        # indoor season URL:
        # http://fillmore.homelinux.net/cgi-bin/Bests?range=all&season=Indoor
        indoor_url = "http://fillmore.homelinux.net/cgi-bin/Bests?range=all&season=Indoor"
        # outdoor season URL:
        # http://fillmore.homelinux.net/cgi-bin/Bests?range=all&season=Outdoor
        outdoor_url = "http://fillmore.homelinux.net/cgi-bin/Bests?range=all&season=Outdoor"

        both_url = "http://fillmore.homelinux.net/cgi-bin/Bests?range=all&season="

        current_url = ""
        if season == 'c':
            current_url = cross_country_url
        elif season == 'i':
            current_url = indoor_url
        elif season == "o":
            current_url = outdoor_url
        elif season == "b":
            current_url = both_url
        else:
            #print("season is bad")
            return

        # setup url of athlete
        tempUrl = current_url + "&sex=" + gender
        # open website
        #print("attempting url " + tempUrl)
        # catch errors

        tempPage = fetch_remote_page(tempUrl)

        # parse
        tempHtml_bytes = tempPage.read()
        # decode
        tempHtml = tempHtml_bytes.decode("utf-8")
        # soup
        tempSoup = BeautifulSoup(tempHtml, "html.parser")

        # set up four tables
        # NOTE: Even though cross country does not have relays, a blank table exists anyways
        table_list = tempSoup.body.find_all("table", recursive=False)
        # print(len(table_list))

        main_list = tempSoup.body.find_all("table", recursive=False)[0]
        relay_list = tempSoup.body.find_all("table", recursive=False)[1]

        # to read a main list:
        main_tr = main_list.find_all("tr", recursive=False)[0]
        # print(female_main_tr)
        main_tds = main_tr.find_all("td", recursive=False)
        main_tds_length = len(main_tds)

        list_events = []
        id_list = []
        # print("range: "+str(main_tds_length))
        for x in range(main_tds_length):
            # print("x: "+str(x))
            current_row = main_tds[x].table
            curr_row_length = len(current_row.find_all("tr", recursive=False))

            row_events = []

            current_event_name = "?"
            current_event_list = []
            current_id_list = []

            for n in range(curr_row_length):
                current_elem = current_row.find_all("tr", recursive=False)[n]
                if current_elem.th:
                    # this is a title!
                    # save prev, create new

                    # SAVE
                    if current_event_name != "?":
                        row_events.append({
                            "name": current_event_name,
                            "list": current_event_list
                        })

                    current_event_name = current_elem.th.getText()
                    current_event_list = []
                else:
                    # this is not a title
                    current_event_list.append({
                        "year": current_elem.find_all("td", recursive=False)[0].getText(),
                        "name": current_elem.find_all("td", recursive=False)[1].getText(),
                        "mark": current_elem.find_all("td", recursive=False)[2].getText(),
                        "id": current_elem.find_all("td", recursive=False)[1].a.get('href').split("=")[1],
                        "meetID": current_elem.find_all("td", recursive=False)[2].a.get('href').split("=")[1],
                        "meetName": current_elem.find_all("td", recursive=False)[2].a.get('title').split(" ", 1)[1],
                        "meetDate": current_elem.find_all("td", recursive=False)[2].a.get('title').split(" ", 1)[0]
                    })

                    current_id_list.append(current_elem.find_all("td", recursive=False)[1].a.get('href').split("=")[1])

                    # check if last element in row
                    if n == curr_row_length:
                        # SAVE
                        row_events.append({
                            "name": current_event_name,
                            "list": current_event_list
                        })

            list_events.append(row_events)
            # logging.info("current_id_list: " + str(current_id_list))
            id_list = id_list + current_id_list
            #id_list.extend(current_id_list)

        return id_list


    def getGenderIds(inputGender):
        #print("fetching gender: " + inputGender)
        id_list = []

        # get Ids
        id_list = id_list + getBests("c", inputGender)
        id_list = id_list + getBests("b", inputGender)

        # remove duplicates
        id_list = list(set(id_list))

        return id_list


    def getGenderList(ath_data, meet_data):

        meet_index = []
        for meet in meet_data:
            meet_index.append(int(meet['id']))

        female_ids = getGenderIds("F")
        male_ids = getGenderIds("M")

        for athlete in ath_data:
            athGender = "?"
            # check bests list first...
            if athlete['id'] in male_ids:
                #male_ids.append(athlete['id'])
                continue
            elif athlete['id'] in female_ids:
                #female_ids.append(athlete['id'])
                continue
            else:
                # print(athlete['id'] + " (" + athlete['name'] + ") not in either best list...")
                # search races until gender is NOT "Both"
                athGender = "?"
                # if they have races
                if 'races' in athlete.keys():
                    # print("has races")
                    # go through races until gender found
                    # print(len(athlete['races']))
                    if athlete['races'] == "urlError":
                        # print("urlError")
                        continue
                    count = 0
                    while count < (len(athlete['races'])) and athGender == "?":
                        current_race = athlete['races'][count]
                        # print(current_race)
                        respective_meet = meet_data[meet_index.index(int(current_race['meetID']))]
                        gender = "?"
                        if 'gender' in respective_meet:
                            gender = respective_meet['gender']

                        # print(gender)
                        if gender != "Both":
                            athGender = gender
                            if athGender == "Boys":
                                male_ids.append(athlete['id'])
                            if athGender == "Girls":
                                female_ids.append(athlete['id'])
                        count += 1

                    if athGender == "?":
                        # print(athlete['id'] + " fatal err")
                        #err_list.append(athlete['id'])
                        continue

        output_object = {
            "Boys": male_ids,
            "Girls": female_ids
        }

        return output_object


    #MEET PAGE FUNC
    def createMeetPage(meet_data, ath_data):
        #get data for athletes (grad year, performance count, specific performance count?), get location data (export eventually smh), get connected meets data (not yet done)
        ath_additional_data = []
        ath_additional_data_index = []
        for ath in ath_data:

            #calculate some stuff
            ath_out_obj = {
                #graduation year
                "g": ath['graduationYear'],
                #count of races
                "c": 0 if 'races' not in ath.keys() else len(ath['races']),
                #count of seasons ran
                #use 12-line chart
                #store number for each season and each year
                #ex. [4,4,0],[1,4,3],[0,0,4],[0,0,0]
                #"s": _____
                #nth event (example: Jack's 14th 200m)
                #"n": _____
            }

            ath_additional_data.append(ath_out_obj)
            ath_additional_data_index.append(ath['id'])

        new_meet_data = copy.deepcopy(meet_data)
        meet_modified_data = []
        for meet in new_meet_data:
            #figure out date situation



            #add athlete info to every athlete within
            #may need to be modified with date structure, but not much
            for curr_categ in meet['events']['categories']:
                for curr_event in curr_categ['events']:
                    for curr_data in curr_event['data']:
                        #check if relay or not
                        if 'Team' in curr_data.keys():
                            #relay
                            for curr_relay_data in curr_data['Athletes']:
                                #check for empty
                                if curr_relay_data == "empty":
                                    continue
                                curr_relay_data['name'] = ftfy.ftfy(curr_relay_data['name'])
                                curr_relay_data['extra'] = ath_additional_data[ath_additional_data_index.index(curr_relay_data['id'])]
                        else:
                            #not relay
                            curr_data['name'] = ftfy.ftfy(curr_data['name'])
                            curr_data['extra'] = ath_additional_data[ath_additional_data_index.index(curr_data['id'])]

            meet_modified_data.append(meet)

        return meet_modified_data


    #MEETS PAGE FUNC
    def createMeetsPage(meet_data):
        listOfFiles = []

        # meetSmall.txt
        meet_small = copy.deepcopy(meet_data)
        meet_small_2 = copy.deepcopy(meet_data)
        meet_data_length = len(meet_data)
        for i in range(meet_data_length):
            meet_item = meet_small[i]
            new_meet_item = {
                "d": meet_item['date'],
                "g": meet_item['gender'],
                "n": meet_item['name'],
                "s": meet_item['season'],
                "l": meet_item['location'],
                "i": meet_item['id']
            }
            meet_small[i] = new_meet_item

            gender2 = meet_item['gender']
            if gender2 == "Girls":
                gender2 = "f"
            elif gender2 == "Boys":
                gender2 = "m"
            elif gender2 == "Both":
                gender2 = "b"
            # shorten season
            season2 = meet_item['season']
            if season2 == "Cross Country":
                season2 = "c"
            elif season2 == "Indoor":
                season2 = "i"
            elif season2 == "Outdoor":
                season2 = "o"
            new_meet_item_2 = {
                "d": meet_item['date'],
                "g": gender2,
                "n": meet_item['name'],
                "s": season2,
                "l": meet_item['location'],
                "i": meet_item['id']
            }
            meet_small_2[i] = new_meet_item_2

        #meetSmall.txt
        listOfFiles.append(meet_small_2)

        #---------------------------------------------------------------------

        # meetsListBig.txt, meetsListSmall.txt, meetsListMedium.txt
        basicList = []
        betterBasicList = []
        bigList = []
        newDict = meet_data
        #print(newDict)
        for x in range(len(newDict)):
            # each event
            # print(newDict[x])
            # get year
            year = newDict[x]['date'].split('-')[0]

            # adjust year
            # example: a cross country event in 2020 would pair with year 2021 because that's
            #         the end to the whole cross country and track season

            if newDict[x]['season'] == "Cross Country":
                year = str(int(year) + 1)
            elif newDict[x]['season'] == "Indoor" and int(newDict[x]['date'].split('-')[1]) > 9:
                year = str(int(year) + 1)

            # FOR SMALL LIST
            # set up boolean to see if never found
            bhool = False
            # check if exists
            for y in range(len(basicList)):
                if basicList[y]['y'] == year:
                    bhool = True
                    basicList[y]['v'] = basicList[y]['v'] + 1
            if not bhool:
                basicList.append({
                    "y": year,
                    "v": 1
                })

            # FOR MEDIUM LIST
            bhool3 = False
            # convert list of
            # set up boolean to see if never found

            season = newDict[x]['season']
            seasonSmall = 'o' if season == 'Outdoor' else 'i' if season == 'Indoor' else 'c'

            for y in range(len(betterBasicList)):
                if betterBasicList[y]['y'] == year:
                    bhool3 = True
                    if seasonSmall in betterBasicList[y]['s'].keys():
                        betterBasicList[y]['s'][seasonSmall] = betterBasicList[y]['s'][seasonSmall] + 1
                    else:
                        betterBasicList[y]['s'][seasonSmall] = 1
                    betterBasicList[y]['v'] = betterBasicList[y]['v'] + 1
            if not bhool3:
                betterBasicList.append({
                    "y": year,
                    "s": {
                        seasonSmall: 1
                    },
                    "v": 1
                })

            # FOR BIG LIST
            # set up boolean
            bhool2 = False
            # check if year does not exist yet
            # shorten gender
            gender2 = newDict[x]['gender']
            if gender2 == "Girls":
                gender2 = "f"
            elif gender2 == "Boys":
                gender2 = "m"
            elif gender2 == "Both":
                gender2 = "b"
            # shorten season
            season2 = newDict[x]['season']
            if season2 == "Cross Country":
                season2 = "c"
            elif season2 == "Indoor":
                season2 = "i"
            elif season2 == "Outdoor":
                season2 = "o"
            for z in range(len(bigList)):
                if bigList[z]['y'] == year:
                    bhool2 = True
                    # append
                    bigList[z]['e'].append({
                        'd': newDict[x]['date'],
                        'g': gender2,
                        'i': newDict[x]['id'],
                        'l': newDict[x]['location'],
                        'n': ftfy.ftfy(newDict[x]['name']),
                        's': season2
                    })
            if not bhool2:
                bigList.append({
                    'y': year,
                    'e': [{
                        'd': newDict[x]['date'],
                        'g': gender2,
                        'i': newDict[x]['id'],
                        'l': newDict[x]['location'],
                        'n': ftfy.ftfy(newDict[x]['name']),
                        's': season2
                    }]
                })


        #meetsListSmall.txt
        listOfFiles.append(basicList)
        #meetsListMedium.txt
        listOfFiles.append(betterBasicList)
        #meetsListBig.txt
        listOfFiles.append(bigList)

        # ---------------------------------------------------------------------

        #curr_meets
        newDict2 = meet_small
        outputDict = []
        outputDict2 = []

        # specify cutoff year

        # returns an abridged array of athletes. year (inclusive) is the lower bound of allowed years
        def cutoffMeets(year):
            #print("cutoffMeets " + str(year))
            bhool3 = True
            count = 0
            while bhool3:
                currentDict = newDict2[count]
                currentYear = int(currentDict['d'][0:4])
                currentMonth = int(currentDict['d'].split("-")[1])
                currentSeason = currentDict['s']
                #print(str(currentYear) + " - " + str(currentMonth) + " - " + str(currentSeason))
                # check if this is within current school year
                # if school year is 2021
                # --- if cross country and year is 2020
                # --- if winter track and year is 2021 and before june
                # --- if winter track and year is 2020 and after june
                # --- if spring track and year is 2021
                if (currentYear == (year - 1) and currentSeason == 'Cross Country') \
                        or (currentYear == year - 1 and currentMonth > 7 and currentSeason == 'Indoor') \
                        or (currentYear == year and currentMonth < 7 and currentSeason == 'Indoor') \
                        or (currentYear == year and currentSeason == 'Outdoor'):

                    # if int(currentDict['y'][0:4]) >= year:
                    outputDict2.append({
                        "n": ftfy.ftfy(currentDict['n']),
                        "i": currentDict['i'],
                        "g": currentDict['g'],
                        "y": currentDict['d'][0:4]
                    })
                else:
                    bhool3 = False
                count = count + 1

        #calculate current school year (2019-2020 should be 2020, and should have 2016 put in cutoffMeets()
        currentMonth = datetime.datetime.now().month
        currentYear = datetime.datetime.now().year
        tempYear = currentYear
        if currentMonth > 6:
            tempYear += 1

        cutoffMeets(tempYear)

        #curr_meets.txt
        listOfFiles.append(outputDict2)

        # ---------------------------------------------------------------------

        #search_format_meets.txt

        for x in range(len(newDict2)):
            currentDict = newDict2[x]
            currentYear = int(currentDict['d'][0:4])

            outputDict.append({
                "n": ftfy.ftfy(currentDict['n']),
                "i": currentDict['i'],
                "g": currentDict['g'],
                "y": currentDict['d'][0:4]
            })

        #search_format_meets.txt
        listOfFiles.append(outputDict)

        return listOfFiles


    #ADD CHART DATA TO ATH
    #participation chart, which is actually already a fascinating dataset to explore even though it's quite simple in context
    chart_data = {
        "part_chart": {}
    }
    part_chart_data = {}
    part_chart_typical = {}

    def get_chart_data(grad_year):
        temp_out = []
        for count in range(4):
            curr_obj = chart_data["part_chart"]['typical'][(int(grad_year) - count)]
            new_curr_obj = curr_obj.copy()
            for attr in new_curr_obj:
                new_attr = new_curr_obj[attr]
                if "list" in new_attr:
                    new_attr.pop("list")
                new_curr_obj[attr] = new_attr

            # print(new_curr_obj)
            temp_out.append(new_curr_obj)
        return temp_out

    def createChartData(ath_data, meet_data):

        m_m_u_d_index = []
        for meet in meet_data:
            m_m_u_d_index.append(int(meet['id']))

        for ath in ath_data:
            #print(ath['name'] + " " + str(ath['id']))
            part_info = {
                "f": {
                    "Cross Country": 0,
                    "Indoor": 0,
                    "Outdoor": 0
                },
                "o": {
                    "Cross Country": 0,
                    "Indoor": 0,
                    "Outdoor": 0
                },
                "j": {
                    "Cross Country": 0,
                    "Indoor": 0,
                    "Outdoor": 0
                },
                "s": {
                    "Cross Country": 0,
                    "Indoor": 0,
                    "Outdoor": 0
                }
            }

            if 'races' in ath.keys():

                # check url error please
                if ath['races'] == "urlError":
                    print("ath has urlError")
                    print(ath['id'])
                    continue

                relativeTranslation = ['f', 'o', 'j', 's']

                for race in ath['races']:
                    #determine where this race falls
                    #must get season, that's pretty helpful

                    # find season
                    if 'meetID' in race.keys():
                        #print(m_m_u_d_index.index(int(race['meetID'])))
                        #print(meet_main_updated_data[m_m_u_d_index.index(int(race['meetID']))])
                        temp_meet_season = meet_data[m_m_u_d_index.index(int(race['meetID']))]['season']
                        # determine year...
                        eventYear = -1
                        if temp_meet_season == "Cross Country":
                            eventYear = int(race['date'].split("-")[0])+1
                        if temp_meet_season == "Indoor":
                            month = int(race['date'].split("-")[1])
                            if month > 8:
                                eventYear = int(race['date'].split("-")[0]) + 1
                            else:
                                eventYear = int(race['date'].split("-")[0])
                        if temp_meet_season == "Outdoor":
                            eventYear = int(race['date'].split("-")[0])

                        #print(eventYear)
                        #print(int(ath['graduationYear']))
                        relativeYear = eventYear - int(ath['graduationYear']) + 3
                        if relativeYear > 3 or relativeYear < 0:
                            #this is a database error, an athlete can't run after they've graduated
                            continue
                        else:
                            #print(relativeYear)

                            #print(relativeTranslation[relativeYear])
                            part_info[relativeTranslation[relativeYear]][temp_meet_season] += 1

                #if ath['id'] == "181":
                #    print(ath['id'])
                #    print(part_info)
                #    for key in range(len(part_info.keys())):
                #        print(key + int(ath['graduationYear']) - 3)


                #update chart data
                #for each attr in part_info...
                for key in range(len(part_info.keys())):

                    currYear = key + int(ath['graduationYear']) - 3
                    #if ath['id'] == "280":
                        #print(str(currYear) + " " + str(part_info[relativeTranslation[key]]))
                    if currYear in part_chart_data.keys():
                        #print(part_chart_data[currYear])
                        part_chart_data[currYear][ath['id']] = part_info[relativeTranslation[key]]
                    else:
                        part_chart_data[currYear] = {
                            ath['id']: part_info[relativeTranslation[key]]
                        }

        #create typical data
        for year in part_chart_data:
            #print(year)
            totalObj = {
                "Cross Country": {
                    "athCount": 0,
                    "list": [],
                    "mean": 0,
                    "median": 0,
                    "mode": 0,
                    "stdev": 0,
                },
                "Indoor": {
                    "athCount": 0,
                    "list": [],
                    "mean": 0,
                    "median": 0,
                    "mode": 0,
                    "stdev": 0,
                },
                "Outdoor": {
                    "athCount": 0,
                    "list": [],
                    "mean": 0,
                    "median": 0,
                    "mode": 0,
                    "stdev": 0,
                },
            }
            totalCount = len(part_chart_data[year].keys())
            for ath_id in part_chart_data[year]:
                #if ath_id == "280":
                #    print(ath_id)
                #    print(part_chart_data[year][ath_id])
                #    print(year)
                for data_attr in part_chart_data[year][ath_id].keys():
                    #check for no participation:
                    if part_chart_data[year][ath_id][data_attr] == 0:
                        continue
                    #print(data_attr)
                    #totalObj[data_attr]["total"] += part_chart_data[year][ath_id][data_attr]
                    totalObj[data_attr]["athCount"] += 1
                    totalObj[data_attr]["list"].append(part_chart_data[year][ath_id][data_attr])

            for key_attr in totalObj.keys():
                #should probably round smh
                #totalObj[key_attr]["total"] /= totalCount

                #check if not empty
                if totalObj[key_attr]["athCount"] > 0:
                    totalObj[key_attr]["mean"] = statistics.mean(totalObj[key_attr]["list"])
                    #mode sometimes throws a fit because it's a bitch
                    #use Counter(a).most_common()[0][0] instead
                    # totalObj[key_attr]["mode"] = statistics.mode(totalObj[key_attr]["list"])
                    totalObj[key_attr]["mode"] = Counter(totalObj[key_attr]["list"]).most_common()[0][0]
                    totalObj[key_attr]["median"] = statistics.median(totalObj[key_attr]["list"])
                    #this is population standard deviation
                    totalObj[key_attr]["stdev"] = statistics.pstdev(totalObj[key_attr]["list"])

            part_chart_typical[year] = totalObj

            #else:
            #    part_chart_index.push(ath['graduationYear'])

        chart_data["part_chart"] = {
            "typical": part_chart_typical,
            "all": part_chart_data,
        }

        return chart_data

    #ATHLETE THINGS
    def createAthletePage(ath_data, meet_data):
        #create meet_main_updated_data index
        m_m_u_d_index = []
        for meet in meet_data:
            m_m_u_d_index.append(meet['id'])

        #add seasons to each
        #for each ath
        new_ath_data = []
        for temp_ath in ath_data:
            new_temp_ath = temp_ath
            #print(new_temp_ath['name'])
            #check for races
            if 'races' in temp_ath.keys():
                #find races
                temp_races = temp_ath['races']
                if temp_races != "urlError":
                    new_races = []
                    #for each race
                    for temp_race in temp_races:
                        #find meet id
                        temp_meet_id = temp_race['meetID']
                        #read meet_main_updated_data
                        temp_index = m_m_u_d_index.index(temp_meet_id)
                        temp_meet = meet_data[temp_index]
                        temp_meet_season = temp_meet['season']
                        temp_meet_location = temp_meet['location']
                        temp_new_race = temp_race
                        temp_new_race['season'] = temp_meet_season
                        temp_new_race['location'] = temp_meet_location
                        #get weather here at some point
                        new_races.append(temp_new_race)
                        #check for pace info and remove it
                        if 'PacePerMile' in temp_new_race.keys():
                            temp_new_race.pop('PacePerMile')
                        if 'PacePerKilo' in temp_new_race.keys():
                            temp_new_race.pop('PacePerKilo')

                    new_temp_ath['name'] = ftfy.ftfy(new_temp_ath['name'])
                    new_temp_ath['races'] = new_races
                    new_temp_ath['cd'] = get_chart_data(temp_ath['graduationYear'])
                else:
                    print("urlError", temp_ath['id'])

                new_ath_data.append(new_temp_ath)

        return new_ath_data

    def createAthletesPage(ath_data, meet_data):
        outputList = []

        #athleteSmall.txt
        ath_small = copy.deepcopy(ath_data)
        ath_small_length = len(ath_data)
        for i in range(ath_small_length):
            ath_item = ath_small[i]
            new_ath_item = {
                "i": ath_item['id'],
                "n": ftfy.ftfy(ath_item['name']),
                "g": ath_item['graduationYear']
            }
            ath_small[i] = new_ath_item

        #athleteSmall.txt
        outputList.append(ath_small)

        # -------------------------------------------------------------------

        #athletesMedium.txt

        # create meet_main_updated_data index
        m_m_u_d_index = []
        for meet in meet_data:
            m_m_u_d_index.append(meet['id'])


        ath_medium = copy.deepcopy(ath_data)
        ath_medium_length = len(ath_data)

        season_ref_list = ["Cross Country", "Indoor", "Outdoor"]

        for i in range(ath_small_length):
            ath_item = ath_medium[i]

            temp_season_list = [[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
            temp_perform_count = 0
            # check for races
            if 'races' in ath_item.keys():
                # find races
                temp_races = ath_item['races']
                if temp_races != "urlError":
                    new_races = []
                    # for each race
                    for temp_race in temp_races:
                        #find season

                        # find meet id
                        temp_meet_id = temp_race['meetID']
                        temp_index = m_m_u_d_index.index(temp_meet_id)
                        temp_meet = meet_data[temp_index]
                        temp_meet_season = temp_meet['season']

                        #find school year (0-3)
                        # find season
                        relativeYear = -1
                        if 'meetID' in temp_race.keys():
                            # print(m_m_u_d_index.index(int(race['meetID'])))
                            # print(meet_main_updated_data[m_m_u_d_index.index(int(race['meetID']))])
                            # determine year...
                            eventYear = -1
                            if temp_meet_season == "Cross Country":
                                eventYear = int(temp_race['date'].split("-")[0]) + 1
                            if temp_meet_season == "Indoor":
                                month = int(temp_race['date'].split("-")[1])
                                if month > 8:
                                    eventYear = int(temp_race['date'].split("-")[0]) + 1
                                else:
                                    eventYear = int(temp_race['date'].split("-")[0])
                            if temp_meet_season == "Outdoor":
                                eventYear = int(temp_race['date'].split("-")[0])

                            # print(eventYear)
                            # print(int(ath['graduationYear']))
                            relativeYear = eventYear - int(ath_item['graduationYear']) + 3
                            if relativeYear > 3 or relativeYear < 0:
                                # this is a database error, an athlete can't run after they've graduated
                                continue
                            # print(relativeYear)
                            # print(relativeTranslation[relativeYear])

                        #add to list
                        if relativeYear != -1:
                            temp_season_list[relativeYear][season_ref_list.index(temp_meet_season)] += 1

                        temp_perform_count += 1

            new_ath_item = {
                "i": ath_item['id'],
                "n": ftfy.ftfy(ath_item['name']),
                "g": ath_item['graduationYear'],
                #seasons
                #ex. [[0,0,0],[0,1,0],[0,2,4],[4,8,12]]
                "s": temp_season_list,
                "c": temp_perform_count
            }
            ath_medium[i] = new_ath_item

        # athleteMedium.txt
        outputList.append(ath_medium)


        # -------------------------------------------------------------------

        #put meetsMedium into small list by year
        ath_list_tiny = []
        ath_list_small = []
        ath_list_medium = []
        for aid in range(len(ath_medium)):
            athItem = ath_medium[aid]
            athItemSmall = ath_small[aid]

            year = athItem['g']
            bhool = False
            for idn in range(len(ath_list_tiny)):
                if ath_list_tiny[idn]['y'] == year:
                    bhool = True
                    ath_list_tiny[idn]['v'] = ath_list_tiny[idn]['v'] + 1
                    ath_list_small[idn]['a'].append(athItemSmall)
                    ath_list_medium[idn]['a'].append(athItem)
            if not bhool:
                ath_list_tiny.append({
                    "y": year,
                    "v": 1
                })
                ath_list_small.append({
                    "y": year,
                    "a": [athItemSmall]
                })
                ath_list_medium.append({
                    "y": year,
                    "a": [athItem]
                })

        #sort by years
        ath_list_tiny = sorted(ath_list_tiny, key=lambda d: d['y'])
        ath_list_small = sorted(ath_list_small, key=lambda d: d['y'])
        ath_list_medium = sorted(ath_list_medium, key=lambda d: d['y'])

        #write these to a file please
        #athListTiny.json
        outputList.append(ath_list_tiny)
        #athListSmall.json
        outputList.append(ath_list_small)
        #athListMedium.json
        outputList.append(ath_list_medium)


        # -------------------------------------------------------------------

        #curr_athletes.json

        outputDict2 = []
        newDict = copy.deepcopy(ath_small)
        def cutoffAthletes(year):
            bhool = True
            count = 0
            while bhool:
                if int(newDict[count]["g"]) >= year:
                    outputDict2.append(newDict[count])
                else:
                    bhool = False
                count = count + 1

        cutoffAthletes(2022)

        #curr_athletes.json
        outputList.append(outputDict2)

        return outputList


    #CALENDAR PAGE
    def createCalendarPage(meet_data):

        outputList = []
        newDict = meet_data

        basicList = []
        betterBasicList = []
        bigList = []

        for x in range(len(newDict)):
            # each event
            # print(newDict[x])
            # get year
            year = newDict[x]['date'].split('-')[0]

            # FOR SMALL LIST
            # set up boolean to see if never found
            bhool = False
            # check if exists
            for y in range(len(basicList)):
                if basicList[y]['y'] == year:
                    bhool = True
                    basicList[y]['v'] = basicList[y]['v'] + 1
            if not bhool:
                basicList.append({
                    "y": year,
                    "v": 1
                })


            # FOR BIG LIST
            # set up boolean
            bhool2 = False
            # check if year does not exist yet
            # shorten gender
            gender2 = newDict[x]['gender']
            if gender2 == "Girls":
                gender2 = "f"
            elif gender2 == "Boys":
                gender2 = "m"
            elif gender2 == "Both":
                gender2 = "b"
            # shorten season
            season2 = newDict[x]['season']
            if season2 == "Cross Country":
                season2 = "c"
            elif season2 == "Indoor":
                season2 = "i"
            elif season2 == "Outdoor":
                season2 = "o"
            for z in range(len(bigList)):
                if bigList[z]['y'] == year:
                    bhool2 = True
                    # append
                    bigList[z]['e'].append({
                        'd': newDict[x]['date'],
                        'g': gender2,
                        'i': newDict[x]['id'],
                        'l': newDict[x]['location'],
                        'n': newDict[x]['name'],
                        's': season2
                    })
            if not bhool2:
                bigList.append({
                    'y': year,
                    'e': [{
                        'd': newDict[x]['date'],
                        'g': gender2,
                        'i': newDict[x]['id'],
                        'l': newDict[x]['location'],
                        'n': newDict[x]['name'],
                        's': season2
                    }]
                })

        outputList.append(basicList)
        outputList.append(bigList)
        return outputList


    #BESTS
    def getBestsObj(meet_data, ath_data, gender_data):
        # METHODS
        def getMeet(input_id):
            return meet_data[meet_index.index(input_id)]

        # generate ath index
        ath_index = []
        for ath in ath_data:
            ath_index.append(int(ath['id']))

        def determineGender(input_id):
            if input_id in gender_data['Boys']:
                return "male"
            if input_id in gender_data['Girls']:
                return "female"
            return "?"

        def decimal_form(str):
            if str == "DNF":
                return 99999
            # split str by : if
            if ":" in str:
                mins = int(str.split(":")[0])
                secs = str.split(":")[1]
                output = (mins * 60) + float(secs)
            else:
                output = float(str)

            return output

        def feetToInches(inputStr):
            ogString = inputStr
            tempFeet = 0
            tempInches = 0
            if "'" in inputStr:
                tempFeet = int(inputStr.split("'")[0])
                tempInches = inputStr.split("'")[1].split('"')[0]
            else:
                tempInches = inputStr.split('"')[0]

            if "¼" in tempInches:
                tempInches = int(tempInches.split("¼")[0]) + 0.25
            elif "½" in tempInches:
                tempInches = int(tempInches.split("½")[0]) + 0.5
            elif "¾" in tempInches:
                tempInches = int(tempInches.split("¾")[0]) + 0.75

            # finalNum = (tempFeet * 12) + float(tempInches)
            # print(ogString+" -> "+str(finalNum))
            return (tempFeet * 12) + float(tempInches)

        def numerical_convert(str):
            if "'" in str or '"' in str:
                # mark
                # get fractions sorted out
                tempFeet = 0
                tempInches = 0
                if "'" in str:
                    tempFeet = int(str.split("'")[0])
                    tempInches = str.split("'")[1].split('"')[0]
                else:
                    tempInches = str.split('"')[0]

                if "¼" in tempInches:
                    tempInches = int(tempInches.split("¼")[0]) + 0.25
                elif "½" in tempInches:
                    tempInches = int(tempInches.split("½")[0]) + 0.5
                elif "¾" in tempInches:
                    tempInches = int(tempInches.split("¾")[0]) + 0.75

                return tempFeet * 12 + float(tempInches)
            else:
                return decimal_form(str)

        def my_custom_xc_sort(input_list):
            return sorted(input_list, key=functools.cmp_to_key(xc_sort))

        def my_custom_field_sort(input_list):
            return sorted(input_list, key=functools.cmp_to_key(indoor_field_sort))

        def my_custom_indoor_sort(input_list):
            return sorted(input_list, key=functools.cmp_to_key(indoor_sort))

        def xc_sort(a, b):
            # if equal...
            if a['l'] == b['l']:
                # print("exact same time: " + str(a['l']) + " " + str(b['l']))
                # compare by place IF SAME RACE ID (not just same meet number)
                if a['j'] == b['j'] and a['v'] == b['v']:
                    if a['p'] < b['p']:
                        return -1
                    else:
                        return 1
                # if not same race, how to compare?
                else:
                    return -1
            else:
                # first by time
                if a['l'] < b['l']:
                    return -1
                else:
                    return 1

        def indoor_field_sort(a, b):
            # if equal...
            if a['l'] == b['l']:
                # fix
                return -1
            else:
                # first by dist
                if a['l'] > b['l']:
                    return -1
                else:
                    return 1

        def indoor_sort(a, b):
            # if equal...
            if a['f'] == b['f']:
                # fix
                return -1
            else:
                # first by dist
                if a['f'] < b['f']:
                    return -1
                else:
                    return 1

        def orderXC(list):
            for event in list:
                event_list = list[event]

                # sort by time then by place...
                # new_event_list = sorted(event_list, key=lambda k: (k['p'], k['l']))
                new_event_list2 = my_custom_xc_sort(event_list)

                # remove items...
                new_event_list_3 = []
                for thingg in new_event_list2:
                    thingg.pop("p")
                    thingg.pop("l")
                    new_event_list_3.append(thingg)

                    # thingg.pop['l']

                list[event] = new_event_list_3

                # print(event)
                # if event == "Bucks Mill Varsity 5000m":
                #    print("PROBLEMATIC LITTLE PIECE OF SHIT")
                # print(new_event_list)
                #    for thing in new_event_list2:
                # print(thing)
                # else:
                # print(new_event_list2[0])

            return list

        def orderIndoor(list):
            for eventName in list.keys():
                # check if field event or
                data = list[eventName]
                sorted_data = data
                if isFieldShortAnalysis(eventName):
                    # is field, can sort
                    sorted_data = my_custom_field_sort(data)
                else:
                    # not field, do some fun FAT shit
                    temp_data = []
                    for thingg in sorted_data:
                        thingg['l'] = round(thingg['l'] * 100) / 100
                        fat = thingg['l']
                        # change FAT based on eventName?
                        if "h" in thingg.keys() and thingg['h'] == True:
                            fat = fat_convert(fat, eventName)
                        thingg['f'] = fat
                        # thingg.pop("l")
                        temp_data.append(thingg)

                    sorted_data = my_custom_indoor_sort(temp_data)

                # remove items...
                new_sorted_data = []
                for thingg in sorted_data:
                    thingg.pop("p")
                    # thingg.pop("l")
                    new_sorted_data.append(thingg)
                list[eventName] = new_sorted_data
            return list

        def fat_convert(time, eventName):
            # basic method
            return round(((math.ceil(time * 10) / 10) + 0.24) * 100) / 100

        def hasNumbers(inputString):
            return any(char.isdigit() for char in inputString)

        def removeNumbers(inputString):
            return ''.join(i for i in inputString if not i.isdigit())

        def onlyNumbers(inputString):
            return ''.join(i for i in inputString if i.isdigit())

        def isFieldShortAnalysis(title):
            tl = title.lower()

            isField = False
            # check for field events
            fieldEvents = ["shot put", "javelin", "discus", "high jump", "long jump", "triple jump", "pole vault"]
            for w in fieldEvents:
                # if the word exists
                if w in tl:
                    return True
            return False

        def getParsedName(group, individual):
            isField = isFieldShortAnalysis(group)
            #print("getParsedName, input: " + str(group) + ", indiv:" + str(individual))
            # print("getParsedName: "+group+" - "+individual)
            if "y" in individual:
                return individual
            if individual.replace('.', '', 1).isdigit():
                # assume meters
                return individual + "m"
            # so many more edge cases
            # print("edge case?")
            if individual == "":
                return betterAnalysis(group, True)
            else:
                return individual

        newEventNameList = []

        def betterAnalysis(title, relayBool):
            # either it has a unit, or it's a field event.
            # 5000m, 55m, 60yd
            # high jump, shot put

            # tl = title lower
            tl = title.lower()

            # remove offending dates. always preceeds with "  - "
            # check if date thing is present
            if "  - " in tl:
                # check if greater than 6 characters (sanity check, dates are short)
                tls = tl.split("  - ")
                if len(tls[1]) < 7:
                    # shorten string to everything before the date
                    tl = tls[0]

            # clean the string of unnecessary words, such as varsity, jv, novice, final, trial
            unnecessaryWords = ["varsity", "novice", "frosh/soph", "freshman", "frosh", "sophomore", "soph", "boys",
                                "girls", "boy", "girl", "championship", "jv", "trials", "trial", "semi finals",
                                "semi final", "finals", "final", "dual", "time"]
            # for each word in the unnecessaryWords
            for w in unnecessaryWords:
                # if the word exists
                if w in tl:
                    # remove the word
                    tl = tl.replace(w, "")

            isField = False
            # check for field events
            fieldEvents = ["shot put", "javelin", "discus", "high jump", "long jump", "triple jump", "pole vault"]
            for w in fieldEvents:
                # if the word exists
                if w in tl:
                    isField = True
                    # honestly, leave it as is. return this string.

                    # remove extraneous x2 and x3 EXCEPT WITH RELAYS!
                    if relayBool:
                        if "x" in tl:
                            tl = tl.split("x")[0]
                    tl = string.capwords(tl.strip())
                    return tl

            # if it's not a field event
            if not isField:
                # CASES:
                # 5000m
                # 55m hurdles
                # 4x400
                # 60yd hurdles
                # sprint medley of sorts

                # first, check if it's a sprint medley

                # else, look to shorten the XC name
                # remove double spaces
                tl = tl.replace("  ", " ")
                # split by spaces
                ts = tl.split()
                # go through each bit
                for i in ts:
                    # check for meters
                    if removeNumbers(i) == "m":
                        # check for hurdles
                        if "hurdles" in tl:
                            tl = i + " hurdles"
                        else:
                            # set title to this
                            tl = i
                # print("test")

            # for now, return the shortened string
            # trim whitespace from ends
            tl = string.capwords(tl.strip())
            if tl == " ":
                print("error parsing time title - " + str(title))
            return tl

        xc_sort_py3 = cmp_to_key(xc_sort)

        # open athletes, meets, genders
        # f = open('athletes_main_updated.txt', 'r')
        # with open('athletes_main_updated.txt') as f:
        #    read_data = f.read()

        # ath_data = json.loads(read_data)

        # f = open('meet_main_updated.txt', 'r')
        # with open('meet_main_updated.txt') as f:
        #    read_data2 = f.read()

        # meet_data = json.loads(read_data2)

        # f = open('genders2.txt', 'r')
        # with open('genders2.txt') as f:
        #    read_data3 = f.read()

        # gender_data = json.loads(read_data3)

        # generate meet index
        meet_index = []
        for meet in meet_data:
            meet_index.append(meet['id'])

        bestsObj = {
            "female": {
                "xc": {},
                "indoor": {
                    "indiv": {},
                    "relay": {}
                },
                "outdoor": {
                    "indiv": {},
                    "relay": {}
                }
            },
            "male": {
                "xc": {},
                "indoor": {
                    "indiv": {},
                    "relay": {}
                },
                "outdoor": {
                    "indiv": {},
                    "relay": {}
                }
            }
        }

        def getSeconds(str):
            if str == "":
                logging.info("getSeconds: empty string")
                return 0
            m = 0
            s = 0
            if ":" in str:
                m, s = str.split(":")
            else:
                s = str
            return int(m) * 60 + float(s)

        def formatSeconds(inputFloat):
            inputFloat = float(inputFloat)
            if inputFloat >= 60:
                min = math.floor(inputFloat / 60)
                seconds = Decimal(inputFloat) % 60

                if "." in str(seconds):
                    if len(str(seconds).split(".")[1]) == 2:
                        seconds = seconds.quantize(Decimal("1.00"))
                    else:
                        seconds = seconds.quantize(Decimal("1.0"))
                else:
                    seconds = seconds.quantize(Decimal("1"))

                # check for sec < 10
                if seconds < 10:
                    seconds = "0" + str(seconds)

                return str(min) + ":" + str(seconds)
            else:
                return str(inputFloat)

        def getBestsForAthlete(id):
            athlete = ath_data[int(ath_index.index(int(id)))]

            #print("Athlete: " + athlete['name'] + " (" + athlete['id'] + ")")
            # check if they have races
            if 'races' in athlete.keys() and athlete['races'] != "urlError":
                #print("athlete races: " + str(len(athlete['races'])))
                successfulRaceCount = 0
                totalWinterCount = 0
                currWinterCount = 0
                # go through each event
                for event in athlete['races']:
                    skipPersonal = False
                    # print("Ath event: "+str(event['date'])+" - '"+str(event['eventName'])+"'")
                    # print(event)
                    # if DNF, do not include
                    # if hasattr(event, 'time'):

                    # skip personal check
                    if event['time'] == "DNF" or event['time'] == "No Mark":
                        skipPersonal = True
                        #print("no personal!")

                    # h is special when it is a relay thing

                    # else:
                    # print("no time!" + event['meetID'])
                    #    continue

                    # get time (this includes the all-important "h" attribute,
                    # which tells us if something has been hand-timed

                    # get data from meet
                    respective_meet = getMeet(event['meetID'])

                    # get season, gender...
                    from_meet_season = respective_meet['season']
                    # print(from_meet_season)
                    from_meet_gender = respective_meet['gender']

                    # depending on season...
                    event_title = ""
                    if from_meet_season == "Cross Country":
                        if event['time'] == "h":
                            skipPersonal = True
                            #print("h no personal")

                        if skipPersonal:
                            #print("skipPersonal 401")
                            continue

                        # must find athlete within event thing...
                        # search for athlete id, generally only once per cross country meet
                        for category in respective_meet['events']['categories']:
                            for category_event in category['events']:
                                # CHECK IF ATHLETE IS PRESENT IN THIS
                                category_event_id_list = []
                                for entry in category_event['data']:
                                    category_event_id_list.append(entry['id'])

                                if athlete['id'] not in category_event_id_list:
                                    continue

                                # print(category_event)
                                # get event name
                                event_name = ""
                                # if two-liner (common)
                                if isinstance(category_event['title'], list):
                                    # print("is list")
                                    event_name = category_event['title'][0]
                                else:
                                    event_name = category_event['title']

                                # extract course
                                course = event_name['name']
                                division = event_name['div']
                                distance = course.rsplit(" ", 1)[1]
                                # print(course)

                                # determine gender
                                athlete_gender = determineGender(athlete['id'])

                                # add record to course
                                current_gender = bestsObj[athlete_gender]
                                current_season = current_gender['xc']

                                # attempt new course or find existing
                                if course in current_season.keys():
                                    current_course = current_season[course]
                                else:
                                    current_season[course] = []
                                    current_course = current_season[course]

                                out_obj = {
                                    # name
                                    "n": athlete['name'],
                                    # id
                                    "i": athlete['id'],
                                    # graduation year
                                    "g": athlete['graduationYear'],
                                    # mark
                                    "m": event['time'],
                                    # convert mark to decimal format...
                                    "l": decimal_form(event['time']),
                                    # meet id
                                    "j": event['meetID'],
                                    # division
                                    "v": division,
                                    # location
                                    "a": respective_meet['location'],
                                    # date
                                    "d": event['date'],
                                    # meet name
                                    "o": event['meetName'],
                                    # place
                                    # 0 if event['place'] == "DQ" else int(event['place'])
                                    "p": ((999 if event['place'] == "DQ" else int(
                                        event['place'])) if 'place' in event.keys() else 0)
                                }

                                if 'splits' in event:
                                    # print("splits!")
                                    # print(event['splits'])
                                    # print(category_event['captions'][-category_event['splits']['length']:])

                                    out_obj['splits'] = {
                                        "labels": category_event['captions'][-category_event['splits']['length']:],
                                        "values": event['splits']
                                    }

                                current_course.append(
                                    out_obj
                                )
                    elif from_meet_season == "Indoor" or from_meet_season == "Outdoor":
                        totalWinterCount += 1
                        #

                        category_ath_event_list = []

                        referencedMeetObj = {}
                        possibleMatches = []
                        currentEvent = {}

                        isRelay = False
                        tempTime = event['time']
                        legCount = -1
                        # check if this is relay from local
                        if "splits" in event.keys():
                            if "Leg" in event['splits'][0]:
                                legCount = int(event['splits'][0].split("Leg ")[1])
                                # print("legCount = "+str(legCount))
                                # print(event['splits'])
                                if len(event['splits']) >= 1:
                                    isRelay = True
                                    if len(event['splits']) > 2:
                                        tempTime = event['splits'][2]
                                    else:
                                        #print("no personal split...")
                                        skipPersonal = True
                                else:
                                    if event['time'] == "h":
                                        skipPersonal = True
                            else:
                                #print("they're just splits")
                                if event['time'] == "DNF" or event['time'].lower() == "no mark" or event['time'] == "DQ":
                                    continue
                        else:
                            if event['time'] == "h":
                                skipPersonal = True

                            if skipPersonal:
                                #print("skipPersonal 513")
                                continue

                        invalidLegCountBool = False

                        # find meet record version of local version
                        if not skipPersonal:

                            if "h" in tempTime:
                                tempTime = tempTime.split("h")[0]
                            tempTime = tempTime.strip()
                            if ".0" == tempTime[-2:] or ".00" == tempTime[-3:]:
                                tempTime = tempTime.split(".0")[0]
                            # print("'"+tempTime+"'")
                            '''onePointTempTime = tempTime
                            if "." in tempTime:
                                if ":" in tempTime:
                                    if len(tempTime.split(".")[1]) == 2:
                                        afterColonStr = (tempTime.split(":")[1].split(".")[0])
                                        endDecimal = str(round(float( "0." + (tempTime.split(":")[1]).split(".")[1])  * 10) / 10)
                                        if "1." in endDecimal:
                                            endDecimal = endDecimal.split("1.")[0]
                                            if "0" == afterColonStr[0]:
                                                afterColonStr = int((tempTime.split(":")[1].split(".")[0]))
                                            else:
                                                afterColonStr = int(tempTime.split(":")[1].split(".")[0])+1
                                        else:
                                            endDecimal = endDecimal.split("0.")[1]

                                        onePointTempTime = tempTime.split(":")[0] + ":" + afterColonStr
                                    else:
                                        onePointTempTime = tempTime
                                else:
                                    if len(tempTime.split(".")[1]) == 2:
                                        onePointTempTime = str(round(float(tempTime) * 10) / 10)
                                    else:
                                        onePointTempTime = str(round(float(tempTime) * 100) / 100)'''

                            onePointTempTime = tempTime
                            # check if seconds!
                            if "'" not in tempTime and '"' not in tempTime:
                                # find seconds now
                                secondsTemp = getSeconds(tempTime)
                                # round seconds
                                if "." in str(secondsTemp):
                                    # print(". len = "+str(len(str(secondsTemp).split(".")[1])))
                                    if len(str(secondsTemp).split(".")[1]) == 3:
                                        secondsTemp = str(round(float(secondsTemp) * 100) / 100)
                                    else:
                                        secondsTemp = str(round(float(secondsTemp) * 10) / 10)
                                # print(secondsTemp)
                                # convert back to mm:ss.ss
                                onePointTempTime = formatSeconds(secondsTemp)

                            # print("tempTime:"+str(tempTime)+", onePoint:"+str(onePointTempTime)+", respect. meet id:"+str(respective_meet['id']))

                            for category in respective_meet['events']['categories']:
                                for category_event in category['events']:
                                    for entry in category_event['data']:
                                        # relay or not
                                        if "Athletes" in entry:
                                            if entry['Athletes'] != ['empty'] and isRelay:
                                                for relayEntry in entry['Athletes']:
                                                    if relayEntry['id'] == athlete['id']:
                                                        # print(relayEntry)
                                                        tempEntryTime = relayEntry['individual'].strip()
                                                        if tempEntryTime == "" or tempEntryTime == "DNF" or tempEntryTime.lower() == "no mark" or tempEntryTime == "DQ":
                                                            continue

                                                        if "'" not in tempEntryTime + tempTime and '"' not in tempEntryTime + tempTime:
                                                            if getSeconds(tempEntryTime) == getSeconds(tempTime):
                                                                referencedMeetObj = entry
                                                                currentEvent = category_event
                                                                continue
                                                        '''if "." in tempEntryTime and tempEntryTime[-2:] != ".0":
                                                            tempEntryTime = tempEntryTime.rstrip('0')
                                                            if tempEntryTime[-1] == ".":
                                                                tempEntryTime = tempEntryTime[:-1]
                                                        altTempEntryTime = tempEntryTime
                                                        if ".0" == tempEntryTime[-2:] or ".00" == tempEntryTime[-3:]:
                                                            altTempEntryTime = tempEntryTime.split(".0")[0]'''
                                                        possibleMatches.append(tempEntryTime)
                                                        # if tempEntryTime == tempTime or altTempEntryTime == tempTime or tempEntryTime == onePointTempTime or altTempEntryTime == onePointTempTime:
                                                        if tempEntryTime == tempTime or tempEntryTime == onePointTempTime:
                                                            referencedMeetObj = entry
                                                            currentEvent = category_event
                                                            continue
                                        else:
                                            if not isRelay and entry['id'] == athlete['id']:
                                                # now check indiv.
                                                if "Time" in entry.keys():
                                                    tempEntryTime = entry['Time'].strip()
                                                    if tempEntryTime == "" or tempEntryTime == "DNF" or tempEntryTime.lower() == "no mark" or tempEntryTime == "DQ":
                                                        continue
                                                    '''if "." in tempEntryTime and tempEntryTime[-2:] != ".0":
                                                        tempEntryTime = tempEntryTime.rstrip('0')
                                                        if tempEntryTime[-1] == ".":
                                                            tempEntryTime = tempEntryTime[:-1]
                                                    altTempEntryTime = tempEntryTime
                                                    if ".0" == tempEntryTime[-2:] or ".00" == tempEntryTime[-3:]:
                                                        altTempEntryTime = tempEntryTime.split(".0")[0]
                                                    #print(entry)'''

                                                    if "'" not in tempEntryTime + tempTime and '"' not in tempEntryTime + tempTime:
                                                        if getSeconds(tempEntryTime) == getSeconds(tempTime):
                                                            referencedMeetObj = entry
                                                            currentEvent = category_event
                                                            continue

                                                    possibleMatches.append(tempEntryTime)
                                                    # if tempEntryTime == tempTime or altTempEntryTime == tempTime or tempEntryTime == onePointTempTime or altTempEntryTime == onePointTempTime:
                                                    if tempEntryTime == tempTime or tempEntryTime == onePointTempTime:
                                                        referencedMeetObj = entry
                                                        currentEvent = category_event
                                                        continue
                                                else:
                                                    # print(entry)
                                                    # print(event)
                                                    possibleMatches.append(entry['Mark'].strip());
                                                    if entry['Mark'].strip() == tempTime:
                                                        referencedMeetObj = entry
                                                        currentEvent = category_event
                                                        continue
                        else:
                            #print("checking no personal time here...")
                            # find matching relay without time
                            # use leg index:
                            # is definitely a relay now
                            for category in respective_meet['events']['categories']:
                                for category_event in category['events']:
                                    for entry in category_event['data']:
                                        # relay or not
                                        if "Athletes" in entry:
                                            # print("isRelay:"+str(isRelay)+" entry:"+str(entry['Athletes']))
                                            if entry['Athletes'] != ['empty'] and isRelay:
                                                # cehck thing
                                                # print("checking entry...")
                                                # print("entry leg count: "+str(len(entry['Athletes']))+", ath leg count:"+str(legCount))
                                                if len(entry['Athletes']) >= legCount:
                                                    # print(entry['Athletes'][legCount - 1]['id'])
                                                    variorceuhoeu = "thing"
                                                else:
                                                    # print("bad leg count 726")
                                                    # print("Ath " + athlete['id'] + ", meet " + respective_meet[
                                                    #    'id'] + ", event: " + str(event['date']) + " - '" + str(
                                                    #    event['eventName']) + "'")
                                                    invalidLegCountBool = True
                                                if len(entry['Athletes']) >= legCount and entry['Athletes'][legCount - 1][
                                                    'id'] == athlete['id']:
                                                    # print("match based solely on leg count")
                                                    # must match on more than leg count!
                                                    # check if title matches at all
                                                    # print("Ath event title: " + event['eventName'])
                                                    # print("Meet event title: " + category_event['title']['name'])
                                                    if event['eventName'] in category_event['title']['name']:
                                                        #print("found it!")
                                                        referencedMeetObj = entry
                                                        currentEvent = category_event
                                                        continue
                                                    # print("indiv:"+entry['Athletes'][legCount - 1]['individual'])
                                                    if entry['Athletes'][legCount - 1]['individual'] == "":
                                                        #print("no personal split 731")
                                                        continue

                        if invalidLegCountBool and referencedMeetObj == {}:
                            #print("bad leg count 756")
                            continue
                        elif referencedMeetObj == {}:
                            # add to fix list, DO NOT BREAK!
                            #fix_list.append(int(respective_meet['id']))
                            #print(".err.")
                            #print("Ath " + athlete['id'] + ", meet " + respective_meet['id'] + ", event: " + str(
                                #event['date']) + " - '" + str(event['eventName']) + "'")
                            continue
                            # print('!!NO MATCHES!!')
                            # print("!!possible matches:" + str(possibleMatches))
                            # print("!!tempTime: '" + tempTime + "' or '" + onePointTempTime + "'")
                        else:
                            # print("event information:")
                            # print(respective_meet)
                            # print(currentEvent)
                            # get event name
                            event_name = currentEvent['title']['name']

                            # determine name
                            # print(event_name)
                            parse_event_name = betterAnalysis(event_name, False)
                            indiv_event_name = betterAnalysis(event_name, True)
                            # print(betterAnalysis(event_name))

                            # determine division?
                            division = "?"

                            # determine gender

                            athlete_gender = "?"
                            athlete_gender = determineGender(athlete['id'])

                            # add record to course
                            current_gender = bestsObj[athlete_gender]
                            # if statement here
                            current_season = current_gender['indoor']

                            if from_meet_season == "Outdoor":
                                current_season = current_gender['outdoor']

                            typeStr = "indiv"
                            current_ev_relay = []
                            if isRelay:
                                current_type_relay = current_season["relay"]

                                if parse_event_name in current_type_relay.keys():
                                    current_ev_relay = current_type_relay[parse_event_name]
                                else:
                                    current_type_relay[parse_event_name] = []
                                    current_ev_relay = current_type_relay[parse_event_name]

                            current_type = current_season["indiv"]

                            out_obj = {}
                            # determine if time or mark
                            if "Time" in currentEvent['captions']:
                                # print("Time")
                                # print("time, not skipping")
                                # determine if relay or indiv

                                if isRelay:
                                    variable = "thing"
                                    # skipping relay for now
                                    # print("Relay:")
                                    # print(event)
                                    # print(referencedMeetObj)
                                    # print("end relay")
                                    # do 2 things:
                                    # make outobj for individual stuff
                                    # ALREADY SET current_type = current_season["indiv"]

                                    # make outobj for relay entry
                                    # ALREADY SET current_type_relay = current_season["relay"]

                                    # RELAY
                                    if referencedMeetObj["Time"] != "":
                                        # print("time relay")

                                        ogAthletes = referencedMeetObj['Athletes']
                                        # rename everything, trim everything
                                        newAthletes = []
                                        for tempAthlete in ogAthletes:
                                            newAthletes.append({
                                                "n": tempAthlete['name'],
                                                "i": tempAthlete['id'],
                                                "m": tempAthlete['individual'].strip()
                                                # will not be storing prs here
                                            })

                                        # check if hand-timed
                                        event_time = ""
                                        # print("event['time'] = "+str(event['time']))
                                        if "h" in event['time']:
                                            isHandTimed = "yes"
                                            event_time = event['time'].split("h")[0]

                                        relay_out_obj = {
                                            # athletes - a group of them
                                            "g": newAthletes,
                                            # team name
                                            "t": referencedMeetObj['Team'],
                                            # mark
                                            "m": referencedMeetObj['Time'],
                                            # convert mark to decimal format...
                                            "l": decimal_form(referencedMeetObj['Time']),
                                            # date
                                            "d": event['date'],
                                            # location
                                            "a": respective_meet['location'],
                                            # meet name
                                            "o": event['meetName'],
                                            # meet id
                                            "j": event['meetID'],
                                            # place
                                            "p": (event['place'] if "place" in event.keys() else 0),
                                            # if relay itself is hand-timed??
                                            # "h": isHandTimed
                                        }
                                        if relay_out_obj not in current_type_relay[parse_event_name]:
                                            current_type_relay[parse_event_name].append(relay_out_obj)

                                    # INDIV
                                    if event['time'] != "":
                                        if skipPersonal:
                                            #print("skipPersonal 729 - indiv time")
                                            continue

                                        # logic required:
                                        new_event_name = string.capwords(
                                            getParsedName(indiv_event_name, event['splits'][1]))

                                        current_type = current_season['indiv']

                                        if new_event_name in current_type.keys():
                                            current_ev = current_type[new_event_name]
                                        else:
                                            current_type[new_event_name] = []
                                            current_ev = current_type[new_event_name]

                                        # will not be hand timed, consider relay split always somewhat hand-timed?
                                        indiv_time = event['time']
                                        if "splits" in event.keys() and len(event['splits']) > 2:
                                            isRelay = True
                                            indiv_time = event['splits'][2]
                                        #else:
                                            #print(indiv_time)
                                            #print("indiv time problem")
                                        indiv_time = indiv_time.strip()

                                        out_obj = {
                                            # name
                                            "n": ftfy.ftfy(athlete['name']),
                                            # id
                                            "i": athlete['id'],
                                            # graduation year
                                            "g": athlete['graduationYear'],
                                            # mark
                                            "m": indiv_time,
                                            # convert mark to decimal format...
                                            "l": decimal_form(indiv_time),
                                            # relay mark boolean
                                            "r": True,
                                            # meet id
                                            "j": event['meetID'],
                                            # division
                                            "v": division,
                                            # location
                                            "a": respective_meet['location'],
                                            # date
                                            "d": event['date'],
                                            # meet name
                                            "o": event['meetName'],
                                            # place
                                            # 0 if event['place'] == "DQ" else int(event['place'])
                                            "p": ((999 if event['place'] == "DQ" else int(
                                                event['place'])) if 'place' in event.keys() else 0),
                                            "debug": event_name,
                                        }
                                        # print(out_obj)
                                        current_ev.append(out_obj)

                                    #else:
                                        #print("empty time, skipping individual")


                                else:
                                    if skipPersonal:
                                        #print("skipPersonal 788 - no relay")
                                        continue
                                    # current_type = current_season["indiv"]
                                    # check if hand-timed
                                    event_time = ""
                                    # print("event['time'] = "+str(event['time']))
                                    if "h" in event['time']:
                                        isHandTimed = "yes"
                                        event_time = event['time'].split("h")[0]
                                        # print(event_time)
                                    elif event['time'] == "DNF":
                                        # print("did not finish, ignore")
                                        continue
                                    else:
                                        isHandTimed = "no"
                                        event_time = event['time']

                                    event_time = event_time.strip()

                                    # check if empty time?
                                    if event['time'] == "":
                                        #print("empty time ... lame")
                                        continue
                                    # time_records[event_dist]

                                    # attempt new course or find existing
                                    if indiv_event_name in current_type.keys():
                                        current_ev = current_type[indiv_event_name]
                                    else:
                                        current_type[indiv_event_name] = []
                                        current_ev = current_type[indiv_event_name]

                                    out_obj = {
                                        # name
                                        "n": ftfy.ftfy(athlete['name']),
                                        # id
                                        "i": athlete['id'],
                                        # graduation year
                                        "g": athlete['graduationYear'],
                                        # mark
                                        "m": event_time,
                                        # convert mark to decimal format...
                                        "l": decimal_form(event_time),
                                        # hand-timed boolean
                                        "h": (isHandTimed == "yes"),
                                        # meet id
                                        "j": event['meetID'],
                                        # division
                                        "v": division,
                                        # location
                                        "a": respective_meet['location'],
                                        # date
                                        "d": event['date'],
                                        # meet name
                                        "o": event['meetName'],
                                        # place
                                        # 0 if event['place'] == "DQ" else int(event['place'])
                                        "p": ((999 if event['place'] == "DQ" else int(
                                            event['place'])) if 'place' in event.keys() else 0),
                                        "debug": event_name,
                                    }
                                    # print("appending something?")
                                    successfulRaceCount += 1
                                    currWinterCount += 1
                                    # print(out_obj)
                                    current_type[indiv_event_name].append(out_obj)
                            else:
                                if isRelay:
                                    variable = "thing"
                                    # skipping relay for now

                                    # do 2 things:
                                    # make outobj for individual stuff
                                    current_type = current_season["indiv"]
                                    # make outobj for relay entry
                                    current_type_relay = current_season["relay"]

                                    # RELAY
                                    if referencedMeetObj["Mark"] != "" and referencedMeetObj['Mark'] != "No Mark":
                                        # print("time relay")

                                        ogAthletes = referencedMeetObj['Athletes']
                                        # rename everything, trim everything
                                        newAthletes = []
                                        for tempAthlete in ogAthletes:
                                            newAthletes.append({
                                                "n": tempAthlete['name'],
                                                "i": tempAthlete['id'],
                                                "m": tempAthlete['individual'].strip()
                                                # will not be storing prs here
                                            })

                                        relay_out_obj = {
                                            # athletes - a group of them
                                            "g": newAthletes,
                                            # team name
                                            "t": referencedMeetObj['Team'],
                                            # mark
                                            "m": referencedMeetObj['Mark'],
                                            # convert mark to decimal format...
                                            "l": feetToInches(referencedMeetObj['Mark']),
                                            # date
                                            "d": event['date'],
                                            # location
                                            "a": respective_meet['location'],
                                            # meet name
                                            "o": event['meetName'],
                                            # meet id
                                            "j": event['meetID'],
                                            # place
                                            "p": (event['place'] if "place" in event.keys() else 0),
                                        }
                                        if relay_out_obj not in current_type_relay[parse_event_name]:
                                            current_type_relay[parse_event_name].append(relay_out_obj)

                                    # INDIV
                                    if event['time'] != "":
                                        if skipPersonal:
                                            #print("skipPersonal 906 - relay indiv mark")
                                            continue

                                        # logic required:
                                        new_event_name = string.capwords(
                                            getParsedName(indiv_event_name, event['splits'][1]))

                                        newEventNameList.append(new_event_name)
                                        #if new_event_name == "":
                                            #print("empty!")

                                        current_type = current_season['indiv']

                                        if new_event_name in current_type.keys():
                                            current_ev = current_type[new_event_name]
                                        else:
                                            current_type[new_event_name] = []
                                            current_ev = current_type[new_event_name]

                                        # will not be hand timed, consider relay split always somewhat hand-timed?
                                        indiv_time = event['time']
                                        if "splits" in event.keys() and len(event['splits']) > 2:
                                            isRelay = True
                                            indiv_time = event['splits'][2]
                                        #else:
                                            #print("indiv time problem")
                                            #print(indiv_time)
                                        indiv_time = indiv_time.strip()

                                        out_obj = {
                                            # name
                                            "n": ftfy.ftfy(athlete['name']),
                                            # id
                                            "i": athlete['id'],
                                            # graduation year
                                            "g": athlete['graduationYear'],
                                            # mark
                                            "m": indiv_time,
                                            # convert mark to decimal format...
                                            "l": feetToInches(indiv_time),
                                            # relay mark boolean
                                            "r": True,
                                            # meet id
                                            "j": event['meetID'],
                                            # division
                                            "v": division,
                                            # location
                                            "a": respective_meet['location'],
                                            # date
                                            "d": event['date'],
                                            # meet name
                                            "o": event['meetName'],
                                            # place
                                            # 0 if event['place'] == "DQ" else int(event['place'])
                                            "p": ((999 if event['place'] == "DQ" else int(
                                                event['place'])) if 'place' in event.keys() else 0),
                                            "debug": event_name,
                                        }
                                        # print(out_obj)
                                        current_ev.append(out_obj)

                                    #else:
                                        #print("whoop")
                                else:
                                    #if skipPersonal:
                                        #print("skipPersonal 966 - indiv mark")

                                    current_type = current_season["indiv"]
                                    # print("mark")

                                    # attempt new course or find existing
                                    if parse_event_name in current_type.keys():
                                        current_ev = current_type[parse_event_name]
                                    else:
                                        current_type[parse_event_name] = []
                                        current_ev = current_type[parse_event_name]

                                    out_obj = {
                                        # name
                                        "n": ftfy.ftfy(athlete['name']),
                                        # id
                                        "i": athlete['id'],
                                        # graduation year
                                        "g": athlete['graduationYear'],
                                        # mark
                                        "m": event['time'],
                                        # convert mark to decimal format...
                                        "l": feetToInches(event['time']),
                                        # meet id
                                        "j": event['meetID'],
                                        # division
                                        "v": division,
                                        # location
                                        "a": respective_meet['location'],
                                        # date
                                        "d": event['date'],
                                        # meet name
                                        "o": event['meetName'],
                                        # place
                                        # 0 if event['place'] == "DQ" else int(event['place'])
                                        "p": ((999 if event['place'] == "DQ" else int(
                                            event['place'])) if 'place' in event.keys() else 0),
                                        "debug": event_name,
                                    }

                                    successfulRaceCount += 1
                                    currWinterCount += 1
                                    # print(out_obj)
                                    current_type[parse_event_name].append(out_obj)
                                    continue

                    #else:
                        #print("weird error")

        # for each athlete...
        for athlete in ath_data:
            getBestsForAthlete(int(athlete['id']))

        # MANIPULATE BESTS ARRAYS
        # sort things

        # Cross country
        # FEMALE
        old_female_xc_list = bestsObj['female']['xc']
        # group by distance? not sure exactly what this is doing
        new_female_xc_list = {k: old_female_xc_list[k] for k in sorted(old_female_xc_list)}
        # sort properly (this works without those weird timing exceptions
        bestsObj['female']['xc'] = orderXC(new_female_xc_list)

        # MALE
        old_male_xc_list = bestsObj['male']['xc']
        # group by distance? not sure exactly what this is doing
        new_male_xc_list = {k: old_male_xc_list[k] for k in sorted(old_male_xc_list)}
        # sort properly (this works without those weird timing exceptions
        bestsObj['male']['xc'] = orderXC(new_male_xc_list)

        # Winter Track
        # FEMALE
        old_female_indoor_indiv_list = bestsObj['female']['indoor']['indiv']
        bestsObj['female']['indoor']['indiv'] = orderIndoor(old_female_indoor_indiv_list)
        # relays
        old_female_indoor_relay_list = bestsObj['female']['indoor']['relay']
        bestsObj['female']['indoor']['relay'] = orderIndoor(old_female_indoor_relay_list)

        # MALE
        old_male_indoor_indiv_list = bestsObj['male']['indoor']['indiv']
        bestsObj['male']['indoor']['indiv'] = orderIndoor(old_male_indoor_indiv_list)
        # relays
        old_male_indoor_relay_list = bestsObj['male']['indoor']['relay']
        bestsObj['male']['indoor']['relay'] = orderIndoor(old_male_indoor_relay_list)

        # Spring Track
        # FEMALE
        old_female_outdoor_indiv_list = bestsObj['female']['outdoor']['indiv']
        bestsObj['female']['outdoor']['indiv'] = orderIndoor(old_female_outdoor_indiv_list)
        # relays
        old_female_outdoor_relay_list = bestsObj['female']['outdoor']['relay']
        bestsObj['female']['outdoor']['relay'] = orderIndoor(old_female_outdoor_relay_list)

        # MALE
        old_male_outdoor_indiv_list = bestsObj['male']['outdoor']['indiv']
        bestsObj['male']['outdoor']['indiv'] = orderIndoor(old_male_outdoor_indiv_list)
        # relays
        old_male_outdoor_relay_list = bestsObj['male']['outdoor']['relay']
        bestsObj['male']['outdoor']['relay'] = orderIndoor(old_male_outdoor_relay_list)

        return bestsObj


    #REPORT
    def createReportPage(meet_data, ath_data, i_neuter, i_nuclear, i_textarg):
        # find timestamp
        timestamp = start_time

        # convert unix timestamp to EST yyyy-mm-dd hh:mm:ss
        textTimestamp = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        out_text = "<br>Report file for "+str(textTimestamp)+"<br>"

        #print arguments

        out_text += "Arguments: nuclear: "+str(i_nuclear)+", neuter: "+str(i_neuter)+", text: "+str(i_textarg)+"<br>"


        out_text += "------<br>"

        #fresh_ids:
        out_text += "fresh_ids: "+str(len(fresh_ids))+"<br>"
        for id in fresh_ids:
            out_text += str(id)+"<br>"

        out_text += "------<br>"

        #new online meets
        out_text += "new online meets: "+str(len(new_ids))+"<br>"
        for id in new_ids:
            out_text += str(id)+"<br>"

        out_text += "<br>------<br>"

        #calculate all new meets changed
        out_text += "new meets changed: "+str(len(meet_scan_list))+"<br>"
        for id in meet_scan_list:
            out_text += "<a href='https://sxctrack.com/meet/"+str(id)+"'>"+str(id)+"</a><br>"

        out_text += "<br>------<br>"

        #calculate all new athletes changed
        out_text += "new athletes changed: "+str(len(ath_scan_list))+"<br>"
        for id in ath_scan_list:
            out_text += "<a href='https://sxctrack.com/athlete/"+str(id)+"'>"+str(id)+"</a><br>"

        out_text += "<br>------<br>"

        return out_text


    #sort_meet_data
    def sort_meet_data(meet_data):
        #check null
        if meet_data == None:
            return None
        #sort meet data by date
        #want to convert 1987-05-16 to epoch time
        meet_data.sort(key=lambda x: int(time.mktime(datetime.datetime.strptime(x['date'], "%Y-%m-%d").timetuple())), reverse=True)
        return meet_data

    def ftpStor(filename, file_json):
        #convert file_json to bytesIO
        file = io.BytesIO(json.dumps(file_json, separators=(',', ':')).encode('utf-8'))

        #attempt to store file max 3 times
        for i in range(3):
            try:
                ftpObject.storbinary('STOR ' + filename, file)
                logging.info("successfully stored " + filename)
                return
            except socket.timeout:
                # Retry the socket operation if a timeout error occurs
                logging.info("failed to store " + filename + " on attempt " + str(i))
                continue
            else:
                # Break the loop if the socket operation succeeds
                break


    #READ CURR ATH AND MEET
    #navigate to curr if no textarg set
    print(textarg)
    if textarg == None:
        chdir("/files/curr/")
    else:
        logging.info("nav. to "+textarg+" bc. textarg set")
        chdir("/debug/file_dump_area/"+textarg+"/")

    #navigate to designated blank if nuclear is true
    if nuclear:
        logging.info("nuclear option activated")
        chdir("/debug/file_dump_area/blank/")


    logging.info("navigating to specified directory...")
    ath_data = json.loads(getFileFTP("athletes_main_updated.txt"))
    logging.info("downloaded ath_data")
    meet_data = json.loads(getFileFTP("meet_main_updated.txt"))
    logging.info("downloaded meet_data")


    #READ HOMELINUX ONLINE FOR ALL IDS
    remote_basic_data = parse_remote_meet_page(fetch_remote_page('http://fillmore.homelinux.net/cgi-bin/Meets?year=*'))
    all_meet_ids = get_ids(remote_basic_data)
    logging.info("external meet count:"+str(len(all_meet_ids)))
    # logging.info("external list:"+str(all_meet_ids))

    #READ SXCTRACK ONLINE FOR BROKEN MEET IDS
    meet_ids_to_scan = []
    #meet_ids_to_scan = parse_sxctrack_meet_page(fetch_remote_page('https://sxctrack.com/files/curr/meetIdsToScan.txt'))

    #READ LOCAL IDS
    local_meet_ids = get_ids(meet_data)
    logging.info("local meet count:"+str(len(local_meet_ids)))
    # logging.info("local list:"+str(local_meet_ids))

    #READ LOCAL IDS FOR FRESH MEETS
    #check meet dates, any < 2 weeks old be scanned
    fresh_ids = findFreshIDs(meet_data);
    
    #remove duplicate fresh_ids
    fresh_ids = list(set(fresh_ids))

    logging.info("fresh_ids: " + str(len(fresh_ids)))
    for id in fresh_ids:
        logging.info("fresh_id: " + str(id))


    #CHECK NEW
    new_ids = find_new_ids(local_meet_ids, all_meet_ids)
    logging.info("new ids:" + str(len(new_ids)))
    for id in new_ids:
        logging.info("new_id: " + str(id))

    #TOTAL SCAN LIST
    meet_scan_list = new_ids + meet_ids_to_scan + fresh_ids

    #remove duplicates...
    meet_scan_list = list(set(meet_scan_list))

    logging.info("meet_scan_list: " + str(len(meet_scan_list)) + " id" + ("s" if len(meet_scan_list) != 1 else ""))

    ftp_out_path = "/debug/file_dump_area/" + str(start_time) + "/"

    #check if there are ids to scan...
    if len(meet_scan_list) == 0:
        #escape!
        logging.info("difference = 0; my job here is done.")

        # write to report.txt...
        # where should daily report go?
        # chdir("/files/curr/")
        # chdir(ftp_out_path)
        chdir("/debug/reports/")
        #report.txt
        # set report.txt to logging output

        # print(log_stream.getvalue())
        # report_txt = logging.getLogger().handlers[0].stream.getvalue()
        report_txt = log_stream.getvalue()

        # replace "\n" with <br>
        report_txt = report_txt.replace("\n", "<br>")

        if not neuter:
            ftpStor("daily_report.txt", report_txt)
            logging.info("successfully stored daily report")
        else:
            logging.info("neuter option activated, not storing daily report")

        exit()

    #SCAN THESE MEETS
    scanned_meet_data = attempt_list_of_ids(meet_scan_list)

    #APPEND MEETS TO LOCAL VAR
    # meet_data = addToLocal(meet_data, scanned_meet_data)
    meet_data = merge_meet_data(meet_data, scanned_meet_data)

    #SORT meet_data by date
    meet_data = sort_meet_data(meet_data)

    #GET ONLINE ATH ORDER
    remote_athlete_page_data = getOnlineAthleteOrder()


    #FIND ATH IDS TO SCAN
    ath_ids_to_scan = getAthleteIdsFromData(scanned_meet_data)

    #READ SXCTRACK ONLINE FOR BROKEN ATH IDS
    sxc_ath_ids_to_scan = []

    #combine lists
    ath_scan_list = ath_ids_to_scan + sxc_ath_ids_to_scan
    #remove dupes
    ath_scan_list = list(set(ath_scan_list))



    #tomfoolery leftover from when I scanned meets after athletes
    new_athlete_list_without_new_events = create_new_athlete_list(ath_data, remote_athlete_page_data)

    #SCAN THESE ATHLETES
    new_athlete_data = attempt_list_of_ath_ids(ath_scan_list)

    final_athlete_data = add_new_data_to_big_list(new_athlete_data, new_athlete_list_without_new_events)

    #gender list
    genderList = getGenderList(final_athlete_data, meet_data)
    #where can gender be added? should it be added to athsmall?

    chdir(ftp_out_path)
    logging.info("successfully navigated to dir...")



    ftpStor("meet_main_updated.txt", meet_data)
    logging.info("successfully stored meet")

    ftpStor("athletes_main_updated.txt", final_athlete_data)
    logging.info("successfully stored athlete")

    ftpStor("gender_main_updated.txt", genderList)
    logging.info("successfully stored gender")


    #meetBig.txt
    chdir(ftp_out_path+"output/")
    chdir(ftp_out_path+"output/meet/")
    ftpStor("meetBig.txt", createMeetPage(meet_data, final_athlete_data));
    logging.info("successfully stored meetBig")

    #this is a list and a mess
    chdir(ftp_out_path+"output/meets/")
    meets_file_list = createMeetsPage(meet_data)

    #meetSmall.txt
    ftpStor("meetSmall.txt", meets_file_list[0])
    logging.info("successfully stored meetSmall")
    #meetsListSmall.txt
    ftpStor("meetsListSmall.txt", meets_file_list[1])
    logging.info("successfully stored meetsListSmall")
    #meetsListMedium.txt
    ftpStor("meetsListMedium.txt", meets_file_list[2])
    logging.info("successfully stored meetsListMedium")
    #meetsListBig.txt
    ftpStor("meetsListBig.txt", meets_file_list[3])
    logging.info("successfully stored meetsListBig")
    #curr_meets.txt
    ftpStor("curr_meets.txt", meets_file_list[4])
    logging.info("successfully stored curr_meets")
    #search_format_meets.txt
    ftpStor("search_format_meets.txt", meets_file_list[5])
    logging.info("successfully stored search_format_meets")

    chdir(ftp_out_path+"output/athlete/")
    #chartData.txt
    chart_json = createChartData(final_athlete_data, meet_data)
    ftpStor("chartData.txt", chart_json)
    logging.info("successfully stored chartData")

    #athlete stuff...

    athlete_json = createAthletePage(final_athlete_data, meet_data)
    # #athletesBig.txt
    ftpStor("athletesBig.txt", athlete_json)
    logging.info("successfully stored chartData")

    #redirect
    chdir(ftp_out_path+"output/athletes/")
    #athletes page
    athletes_list = createAthletesPage(final_athlete_data, meet_data)
    #work with list

    #athleteSmall.txt
    ftpStor("athleteSmall.txt", athletes_list[0])
    logging.info("successfully stored athleteSmall")
    #athletesMedium.txt
    ftpStor("athleteMedium.txt", athletes_list[1])
    logging.info("successfully stored athletesMedium")
    #athListTiny.json
    ftpStor("athListTiny.json", athletes_list[2])
    logging.info("successfully stored athListTiny")
    #athListSmall.json
    ftpStor("athListSmall.json", athletes_list[3])
    logging.info("successfully stored athListSmall")
    #athListMedium.json
    ftpStor("athListMedium.json", athletes_list[4])
    logging.info("successfully stored athListMedium")
    #curr_athletes.json
    ftpStor("curr_athletes.json", athletes_list[5])
    logging.info("successfully stored curr_athletes")

    #redirect
    chdir(ftp_out_path+"output/calendar/")
    calendar_list = createCalendarPage(meet_data)
    #calendarSmall.txt
    ftpStor("calendarSmall.txt", calendar_list[0])
    logging.info("successfully stored calendarSmall")
    #calendarBig.txt
    ftpStor("calendarBig.txt", calendar_list[1])
    logging.info("successfully stored calendarBig")


    #redirect
    chdir(ftp_out_path+"output/bests/")
    #bests.txt
    best_json = getBestsObj(meet_data, final_athlete_data, genderList)
    ftpStor("bests.txt", best_json)
    logging.info("successfully stored bests")


    #report
    chdir(ftp_out_path)
    #report.txt
    report_txt = createReportPage(meet_data, final_athlete_data, neuter, nuclear, textarg)


    ftpStor("report.txt", report_txt)
    logging.info("successfully stored report 1")

    # also write report in /debug/reports/

    chdir("/debug/reports/")

    ftpStor("report"+str(start_time)+".txt", report_txt)


    ## IF NEUTER IS TRUE, DO NOT SHUFFLE

    if not neuter:
        # write daily report
        ftpStor("daily_report.txt", report_txt)

        #shuffle

        #delete contents in /files/old/
        deleteFilesInDir("/files/old/")

        #move contents of /files/curr/ to /files/old/
        moveContents("/files/curr/", "/files/old/")

        #delete contents of /files/curr/ (there shouldn't be any there but whatever)
        #deleteFilesInDir("/files/curr/")

        #copy contents of /*timestamp*/ to /files/curr/
        copyContents(str(ftp_out_path), "/files/curr/")

    else:
        logging.info("neuter is true, not shuffling")



    ftpObject.quit()

    time_taken = int(time.time()) - start_time
    logging.info("took " + str(time_taken) + " seconds")
    logging.info("finished.")


    # do something here
except Exception as e:
    logging.critical(e, exc_info=True)
    time_taken = int(time.time()) - start_time
    logging.info("took " + str(time_taken) + " seconds")
    logging.info("finished with error (see above).")