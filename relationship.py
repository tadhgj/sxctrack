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
    parse_results = parser.parse_args()

    start_time = int(time.time())
    GMTTime = datetime.datetime.now()
    eastern = pytz.timezone('US/Eastern')
    ESTTime = GMTTime.astimezone(eastern)


    #FOR RUNNING ON LOCAL MAC
    root_logger= logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # or whatever
    handler = logging.FileHandler(filename=str(start_time)+'.log', mode='w', encoding='utf-8')
    handler2 = handler
    handler.setFormatter(logging.Formatter('%(name)s %(message)s')) # or whatever
    root_logger.addHandler(handler)
    root_logger.addHandler(handler2)
    root_logger.addHandler(logging.StreamHandler(sys.stdout))

    #SEE HERE
    #to run on macbook...
    #filename=str(start_time)+'.log',

    #BEGIN
    logging.info("starting time: " + str(start_time))
    logging.info("GMT Time: " + GMTTime.strftime("%Y-%m-%d, %H:%M:%S"))
    logging.info("EST Time: " + ESTTime.strftime("%Y-%m-%d, %H:%M:%S"))
    logging.info("Starting relationshipcreator...")

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



    def get_ids(objList):
        outputArr = []
        for objTemp in objList:
            outputArr.append(int(objTemp['id']))

        return outputArr

    adv_ath_relationship_dict = {}

    grad_year_range = [2023, 2022, 2021]

    def addToAdv(loc, new, type):
        #force loc to be an int
        loc = int(loc)

        typeConvert = {
            "meets": "m",
            "categories": "c",
            "events": "e"
        }

        type = typeConvert[type]

        #DEBUG
        #only add new if graduationYear is 2022
        #find new in ath_data
        for ath in ath_data:
            if int(ath['id']) == int(new):
                if int(ath['graduationYear']) not in grad_year_range:
                    # print("skipping "+str(new)+" because grad year is "+str(ath['graduationYear']+", not in "+str(grad_year_range)))
                    return

        # print("adding to adv: "+str(loc)+" - "+str(new)+" - "+str(type))
        if loc not in adv_ath_relationship_dict.keys():
            adv_ath_relationship_dict[loc] = {}
            adv_ath_relationship_dict[loc][new] = {}
            adv_ath_relationship_dict[loc][new][type] = 1
        else:
            if new not in adv_ath_relationship_dict[loc].keys():
                adv_ath_relationship_dict[loc][new] = {}
                adv_ath_relationship_dict[loc][new][type] = 1
            else:
                if type not in adv_ath_relationship_dict[loc][new].keys():
                    adv_ath_relationship_dict[loc][new][type] = 1
                else:
                    adv_ath_relationship_dict[loc][new][type] += 1

        #calculate score...

        #consider that 'meets' indicate that they did NOT share categories or events
        #consider that 'categories' indicate that they did NOT share events
        # but also remember that 'categories' is pretty broad, so it is not much more valuable than 'meets' in comparison to 'events'

        

        #weight here:
        # weight = {
        #     'meets': 1,
        #     'categories': 2,
        #     'events': 3
        # }

        # with respect to comments above...
        weight = {
            'm': 1,
            'c': 1.1,
            'e': 3
        }

        tempThis = adv_ath_relationship_dict[loc][new]
        
        score = 0

        for key in tempThis.keys():
            #ignore key 'score'
            if key == 's':
                continue

            score += tempThis[key] * weight[key]

        #round score to 1 decimal place
        score = round(score, 1)

        adv_ath_relationship_dict[loc][new]['s'] = score
            

    chdir("/files/curr/")

    logging.info("navigating to specified directory...")
    ath_data = json.loads(getFileFTP("athletes_main_updated.txt"))
    logging.info("downloaded ath_data")
    meet_data = json.loads(getFileFTP("meet_main_updated.txt"))
    logging.info("downloaded meet_data")
    gender_data = json.loads(getFileFTP("gender_main_updated.txt"))
    logging.info("downloaded gender data")

    #READ LOCAL IDS
    local_meet_ids = get_ids(meet_data)
    # logging.info("local meet count:"+str(len(local_meet_ids)))
    # logging.info("local list:"+str(local_meet_ids))

    #APPEND MEETS TO LOCAL VAR
    # meet_data = addToLocal(meet_data, scanned_meet_data)

    #SORT meet_data by date
    # meet_data = sort_meet_data(meet_data)



    #RELATIONSHIP PROCESS
    # how should I go about this?
    # for each athlete in ath_data, get meet_id list
    #    remove duplicates, but remember how many times each meet_id appears
    #    for each meet_id, find corresponding meet in meet_data
    #    within this meet:
    #        create 3 lists:
    #            other ath_ids in a specific event with this athlete
    #            other ath_ids in the same category as this athlete
    #            other ath_ids in the same meet (do not count self)
    # now, add scores (weights) to each of these lists
    # same event: 3
    # same category: 2
    # same meet: 1
    # put this into a dictionary, with the key being the ath_id, and the content being
    # a list of other ath_ids and their scores.

    ath_relationship_dict = {}

    for ath in ath_data:

        #convert to int
        ath['id'] = int(ath['id'])

        # print("scanning athlete "+str(ath['id']))

        #DEBUG
        # if int(ath['id']) != 271:
        #     continue

        if int(ath['graduationYear']) not in grad_year_range:
            continue

        # print("processing athlete "+str(ath['id']))



        #get event list
        event_list = ath['races']

        # print(str(len(event_list)) + " events found for athlete "+str(ath['id']))

        #add entry to dict...
        ath_relationship_dict[ath['id']] = {}

        adv_ath_relationship_dict[ath['id']] = {}

        #skip if no events
        if len(event_list) == 0:
            continue

        #map event_list to array of meetID's
        meet_id_list = []
        for event in event_list:
            meet_id_list.append(event['meetID'])

        #create frequency map of meet_id_list
        meet_id_freq = {}
        for meet_id in meet_id_list:
            meet_id_freq[meet_id] = meet_id_freq.get(meet_id, 0) + 1

        # print("meet_id_freq: "+str(meet_id_freq))

        #for each meet_id, find corresponding meet in meet_data, and remember freq.
        for meet_id_key in meet_id_freq.keys():
            currMeetFreq = meet_id_freq[meet_id_key]
            # print("processing meet "+str(meet_id_key)+" ("+str(currMeetFreq)+" entries)")

            currMeet = "err"
            #find meet in meet_data
            for meet in meet_data:
                if meet['id'] == meet_id_key:
                    currMeet = meet
                    break

            if currMeet == "err":
                print("ERROR: meet not found in meet_data!")
                continue

            #create lists

            #traverse currMeet now...
            currMeetEventCategories = currMeet['events']['categories']

            for currMeetEventCategory in currMeetEventCategories:
                same_event_id_list = []
                same_category_list = []
                isInCategory = False
                #find list of events
                currMeetEventList = currMeetEventCategory['events']

                currMeetIndex = 0
                for currMeetEvent in currMeetEventList:
                    
                    #if regular event
                    for dataPoint in currMeetEvent['data']:
                        if 'Athletes' in dataPoint:
                            #relay...
                            for relayAth in dataPoint['Athletes']:
                                #check if this is empty
                                if relayAth == "empty":
                                    continue

                                #convert to int
                                relayAth['id'] = int(relayAth['id'])

                                #check self
                                if relayAth['id'] == ath['id']:
                                    same_event_id_list.append(currMeetIndex)
                                else:
                                    same_category_list.append([relayAth['id'], currMeetIndex])
                        else:
                            #convert to int
                            dataPoint['id'] = int(dataPoint['id'])

                            if dataPoint['id'] == ath['id']:
                                same_event_id_list.append(currMeetIndex)
                            else:
                                same_category_list.append([dataPoint['id'], currMeetIndex])

                    currMeetIndex += 1

                # look at same category list...
                for item in same_category_list:
            
                    # if length of same_event_id_list is 0, then add every item in same_category_list to ath_relationship_dict with score 1
                    if len(same_event_id_list) == 0:
                        ath_relationship_dict[ath['id']][item[0]] = ath_relationship_dict[ath['id']].get(item[0], 0) + 1

                        addToAdv(ath['id'], item[0], 'meets')

                    else:
                        if item[1] in same_event_id_list:
                            ath_relationship_dict[ath['id']][item[0]] = ath_relationship_dict[ath['id']].get(item[0], 0) + 3

                            addToAdv(ath['id'], item[0], 'events')

                        else:
                            ath_relationship_dict[ath['id']][item[0]] = ath_relationship_dict[ath['id']].get(item[0], 0) + 2

                            addToAdv(ath['id'], item[0], 'categories')


    #create d3 lists (nodes), and (source, target)
    d3_obj = {
        'nodes': [],
        'links': []
    }
    

    for ath_id in adv_ath_relationship_dict.keys():
        #find ath
        localAth = False
        for ath in ath_data:
            if int(ath['id']) == int(ath_id):
                localAth = ath
                break

        #find ath in gender list if events are not empty
        if len(localAth['races']) != 0:
            if str(ath_id) in gender_data['Boys']:
                localAth['gender'] = "m"
            else:
                localAth['gender'] = "f"
        else:
            localAth['gender'] = "n"

        #add node
        d3_obj['nodes'].append({
            'id': str(ath_id),
            #this is where I can add arbitrary things to decorate with, things such as
            # name
            'name': localAth['name'],
            # grad Year
            'gradYear': localAth['graduationYear'],
            # athlete's event count

            # athlete gender
            # actually I need to download the gender file for that
            'gender': localAth['gender']
            
        })

        #add links
        for target_id in adv_ath_relationship_dict[ath_id].keys():
            #round score ('s')
            score = round(round(adv_ath_relationship_dict[ath_id][target_id]['s']) / 20, 1)

            #filter
            for ath in ath_data:
                if int(ath['id']) == int(target_id):
                    if int(ath['graduationYear']) not in grad_year_range:
                        continue

            d3_obj['links'].append({
                'source': str(ath_id),
                'target': str(target_id),
                'value': score
            })
            
                   
    #store file locally
    with open('basic_ath_relationship_dict.json', 'w') as outfile:
        json.dump(ath_relationship_dict, outfile, separators=(',', ':'))

    with open('adv_ath_relationship_dict.json', 'w') as outfile:
        json.dump(adv_ath_relationship_dict, outfile, separators=(',', ':'))

    with open('d3_obj.json', 'w') as outfile:
        json.dump(d3_obj, outfile, separators=(',', ':'))

    
    








    # ftp_out_path = "/debug/file_dump_area/" + str(start_time) + "/"
    # chdir(ftp_out_path)
    # logging.info("successfully navigated to dir...")

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

    # ftpStor("meet_main_updated.txt", meet_data)
    # logging.info("successfully stored meet")

    # ftpStor("athletes_main_updated.txt", final_athlete_data)
    # logging.info("successfully stored athlete")

    # ftpStor("gender_main_updated.txt", genderList)
    # logging.info("successfully stored gender")

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