import logging
import copy
import urllib.request as urllib
from urllib.request import urlopen
import socket
import argparse
import ftplib
import time
import pytz
import sys
import os


parser = argparse.ArgumentParser(description='silent checking script')
parser.add_argument('link', action='store', type=str, help='FTP Link')
parser.add_argument('user', action='store', type=str, help='FTP Username')
parser.add_argument('passo', action='store', type=str, help='FTP Password')

parse_results = parser.parse_args()


#LOG INTO FTP
ftpHost = parse_results.link
ftpUser = parse_results.user
ftpPassword = parse_results.passo


# set up logger
logging.basicConfig(filename='ftp_relogin_test.log', level=logging.INFO, format='%(asctime)s %(message)s')


ftpObject = ftplib.FTP(ftpHost)

def ftpLogin():
    logging.info("attempting ftp login")
    # should I make sure that we're not already logged in / kill any existing FTP work?
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
    logging.info("login successful")

# define failed FTP login class so it looks nice
class FTPLoginFailed(Exception):
    pass

def ftpLoginThrow():
    logging.info("attempting ftp login")
    # ftpObject = ftplib.FTP(ftpHost)
    # should I make sure that we're not already logged in / kill any existing FTP work?
    for i in range(3):
        try:
            ftpObject.login(user=ftpUser, passwd=ftpPassword)
            break
        except Exception as e:
            logging.info("failed to login, trying again...")
            logging.info("specific error: "+str(e)+".")
            time.sleep(1)
            if i == 2:
                logging.info("failed to login, exiting...")
                raise FTPLoginFailed("couldn't log in")

    logging.info("login successful")

def ftpLogout():
    logging.info("ftp logging out...")
    ftpObject.quit()
    logging.info("ftp logged out")

def navigateToRoot():
    logging.info("navigating to root...")
    try:
        ftpObject.cwd("/")
    except Exception as e:
        logging.info("caught exception: "+str(e)+".")
    logging.info("navigated to root")

# try it out

ftpLogin()

navigateToRoot()

ftpLogout()

ftpObject = ftplib.FTP(ftpHost)
ftpLogin()

navigateToRoot()