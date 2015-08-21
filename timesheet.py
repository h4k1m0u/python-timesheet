#!/usr/bin/env
import pickle
import datetime
import os
import sys

def format_seconds(seconds):
    """ Format # of seconds given as parameters into hh:mm:ss format

        Args:
            seconds(int): number of seconds
        Returns:
            date(str): hh:mm:ss formated string
    """
    dt = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=seconds)
    return "%02d:%02d:%02d" % (dt.hour, dt.minute, dt.second)

# constants & inputs
FILENAME_TIME = 'time.dat'
FILENAME_TIMESHEET = 'timesheet.dat'

# get mode (start|stop)
if len(sys.argv) > 1 and sys.argv[1] in ('start', 'stop'):
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

    # record start time
    fd = open(FILENAME_TIME, 'wb')

    # save current time
    current_time = datetime.datetime.now()
    pickle.dump(current_time, fd)
    fd.close()

    # print current time
    print 'Start time:', current_time

# stop counting
elif mode == 'stop':
    try:
        # get previously saved time
        fd = open(FILENAME_TIME, 'rb')
        previous_time = pickle.load(fd)
        fd.close()

        # compute elapsed time
        current_time = datetime.datetime.now()
        elapsed_time = current_time - previous_time
        formatted_elapsed_time = format_seconds(elapsed_time.seconds)
        print 'Stop time:', current_time
        print 'Elapsed time:', formatted_elapsed_time

        # save the elapsed time to a timesheet file
        ft = open(FILENAME_TIMESHEET, 'a+')
        ft.write(datetime.datetime.now().strftime("%d-%m-%Y") + " " + formatted_elapsed_time + "\n")
        ft.close()

        # upload timesheet file to dropbox account
        os.system('dropbox_uploader.sh upload %s Timesheet' % FILENAME_TIMESHEET)

        # delete time file
        os.remove(FILENAME_TIME)
    except IOError:
        # timer needs to be started first
        print 'Timer needs to be started first!!!'
