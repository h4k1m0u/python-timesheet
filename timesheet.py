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
FILENAME = 'timesheet.dat'

# get mode (start|stop)
if len(sys.argv) > 1:
    mode = sys.argv[1]
else:
    print 'Usage: timesheet.py start|stop'
    exit()

# TODO: Format Seconds in H:M:S format.
# TODO: Create file (start counting) and delete file (compute difference)
#
# TODO: Upload automatically to Dropbox with: `dropbox_uploader.sh upload test Timesheet`

if mode == 'start':
    # timer is already started
    if os.path.isfile(FILENAME):
        print 'Timer is already started!!!'
        exit()

    # record start time
    f = open(FILENAME, 'wb')

    # save current time
    current_time = datetime.datetime.now()
    pickle.dump(current_time, f)
    f.close()

    # print current time
    print 'Start time:', current_time
elif mode == 'stop':
    try:
        # get previously saved time
        f = open(FILENAME, 'rb')
        previous_time = pickle.load(f)
        f.close()

        # compute elapsed time & delete file
        os.remove(FILENAME)
        current_time = datetime.datetime.now()
        elapsed_time = current_time - previous_time
        print 'Stop time:', current_time
        print 'Elapsed time:', format_seconds(elapsed_time.seconds)
    except IOError:
        # timer needs to be started first
        print 'Timesheet needs a start date!!!'
else:
    print 'Usage: timesheet.py start|stop'
    exit()
