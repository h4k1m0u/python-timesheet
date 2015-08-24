#!/usr/bin/env
import pickle
from datetime import datetime, timedelta
import os
import sys
import subprocess
import re
import fileinput

# constants & inputs
FILENAME_TIME = 'time.dat'
FILENAME_TIMESHEET = 'timesheet.dat'

def get_number_lines(f):
    """ Get the number of lines of a given file

        Args:
            f (file)
        Return:
            n (int)
    """
    return sum(1 for line in open(f))

def remove_replaced_line(filename):
    """ Remove second-to-last line (replaced line) from file

        Args:
            filename (str)
    """
    num_lines = get_number_lines(filename)
    i = 0

    for line in fileinput.input(filename, inplace=True):
        i += 1
        if i != num_lines - 1:
            print line.strip()

def format_seconds(seconds):
    """ Format # of seconds given as parameters into hh:mm:ss format

        Args:
            seconds(int)
        Returns:
            date(str): hh:mm:ss formated string
    """
    time = datetime(1, 1, 1) + timedelta(seconds=seconds)
    return "%02d:%02d:%02d" % (time.hour, time.minute, time.second)

def save_time(seconds):
    """ Add elapsed time to timesheet file

        Args:
            seconds(int): elapsed time in seconds
    """
    f_timesheet = open(FILENAME_TIMESHEET, 'a+')
    timesheet_last_line = subprocess.check_output(['tail', '-n', '1', 'timesheet.dat']).strip().split()
    today_date = datetime.now().strftime("%d-%m-%Y")

    if not timesheet_last_line or timesheet_last_line[0] != today_date:
        # if no time has been recorded today
        f_timesheet.write(today_date + " " + format_seconds(seconds) + "\n")
        f_timesheet.close()
    else:
        # extract # of seconds from timesheet file & from current time
        timesheet_today = timesheet_last_line[1]
        timesheet_today_hms = re.findall('^(\d{2}):(\d{2}):(\d{2})$', timesheet_today)[0]
        today_seconds = 3600*int(timesheet_today_hms[0]) + 60*int(timesheet_today_hms[1]) + int(timesheet_today_hms[2])
        total_seconds = today_seconds + seconds

        # replace last line by updated time in a temporary file
        f_timesheet.write(today_date + " " + format_seconds(total_seconds) + "\n")
        f_timesheet.close()
        remove_replaced_line(FILENAME_TIMESHEET)

# get mode (start|stop)
if len(sys.argv) > 1 and sys.argv[1] in ('start', 'stop', 'status'):
    mode = sys.argv[1]
else:
    print 'Usage: timesheet.py start|stop'
    exit()

# start counting
if mode == 'start':
    # timer is already started
    if os.path.isfile(FILENAME_TIME):
        print 'Timer is already started!!!'
        exit()

    # save start time
    with open(FILENAME_TIME, 'wb') as f_time:
        current_time = datetime.now()
        pickle.dump(current_time, f_time)

    # print current time
    print 'Start time:', current_time

# stop counting
elif mode == 'stop':
    try:
        # get previously saved time
        with open(FILENAME_TIME, 'rb') as f_time:
            previous_time = pickle.load(f_time)

        # compute elapsed time
        current_time = datetime.now()
        elapsed_time = current_time - previous_time
        elapsed_seconds = elapsed_time.total_seconds()
        print 'Stop time:', current_time
        print 'Elapsed time (seconds):', elapsed_seconds

        # save the elapsed time to a timesheet file
        save_time(elapsed_seconds)

        # upload timesheet file to dropbox account
        subprocess.call(['dropbox_uploader.sh', 'upload', FILENAME_TIMESHEET, 'Timesheet'])

        # delete time file
        os.remove(FILENAME_TIME)
    except IOError:
        # timer needs to be started first
        print 'Timer needs to be started first!!!'

# check if started or stopped
elif mode == 'status':
    if os.path.isfile(FILENAME_TIME):
        print 'Timer started!!!'
    else:
        print 'Timer stopped!!!'
