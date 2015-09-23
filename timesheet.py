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
DROPBOX_CLIENT = 'dropbox_uploader.sh'

def file_to_array(f):
    """ Get an associative array (date => timesheet) from the given file

        Args:
            f (file)
        Return:
            arr (dict)
    """
    d = {}
    for line in f:
        l = line.split()
        d[l[0]] = l[1]

    return d

def format_seconds(seconds):
    """ Format # of seconds given as parameters into hh:mm:ss format
        Convert days to hours (1 day = 24 hours)

        Args:
            seconds(int)
        Returns:
            date(str): hh:mm:ss formated string
    """
    time = datetime(1, 1, 1) + timedelta(seconds=seconds)
    return "%02d:%02d:%02d" % ((time.day - 1)*24 + time.hour, time.minute, time.second)

def str_to_seconds(s):
    """ Get number of seconds from time string ('HH:MM:SS')

        Args:
            s(str)
        Returns:
            seconds(int)
    """
    time = datetime.strptime(s, '%H:%M:%S')
    dt = timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
    return dt.total_seconds()

def add_timesheets(*args):
    """ Add timesheets given in %H:%M:%S format and returned in the same format

        Args:
            timesheet (str)
        Return:
            total (str)
    """
    total_seconds = sum([str_to_seconds(arg) for arg in args])
    return format_seconds(total_seconds)

def timesheet_weekdays(d):
    """ Get timesheet for the seven weekdays preceding current day

        Args:
            d (dict)
        Return:
            l (list)
    """
    l = [[-1, '00:00:00']]*7
    for i in xrange(6, -1, -1):
        # get max date each time
        current_date = max(d.keys())
        current_timesheet = d[current_date]
        current_weekday =  datetime.strptime(current_date, '%Y-%m-%d').weekday()
        l[i] = [current_weekday, current_timesheet]

        del d[max(d.keys())]

        # quit loop if no more dates
        if not d:
            break

    return l

def timesheet_per_week(d):
    """ Get total timesheets in current week (starting monday)

        Args:
            d (dict)
        Return:
            total (int)
    """
    # get current day & six previous days timesheets
    l = timesheet_weekdays(d)
    current_weekday = l[6][0]

    # add timesheets in current week (from monday) according to current weekday
    return {
        0 : lambda: add_timesheets(l[6][1]),
        1 : lambda: add_timesheets(l[6][1], l[5][1]),
        2 : lambda: add_timesheets(l[6][1], l[5][1], l[4][1]),
        3 : lambda: add_timesheets(l[6][1], l[5][1], l[4][1], l[3][1]),
        4 : lambda: add_timesheets(l[6][1], l[5][1], l[4][1], l[3][1], l[2][1]),
        5 : lambda: add_timesheets(l[6][1], l[5][1], l[4][1], l[3][1], l[2][1], l[1][1]),
        6 : lambda: add_timesheets(l[6][1], l[5][1], l[4][1], l[3][1], l[2][1], l[1][1], l[0][1]),
    }[current_weekday]()

def get_number_lines(f):
    """ Get the number of lines of a given file

        Args:
            f (file)
        Return:
            n (int)
    """
    return sum(1 for line in f)

def remove_line(line_number):
    """ Remove line <line_number> from file

        Args:
            line_number (int)
    """
    i = 0

    for line in fileinput.input(FILENAME_TIMESHEET, inplace=True):
        i += 1
        if i != line_number:
            print line.strip()

def save_time(seconds):
    """ Add elapsed time to timesheet file

        Args:
            seconds(int): elapsed time in seconds
    """
    f_timesheet = open(FILENAME_TIMESHEET, 'a+')
    timesheet_last_line = subprocess.check_output(['tail', '-n', '1', FILENAME_TIMESHEET]).strip().split()
    today_date = datetime.now().strftime("%Y-%m-%d")

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
        old_num_lines = get_number_lines(f_timesheet)
        f_timesheet.write(today_date + " " + format_seconds(total_seconds) + "\n")
        f_timesheet.close()
        remove_line(old_num_lines)

# get mode (start|stop)
if len(sys.argv) > 1 and sys.argv[1] in ('start', 'stop', 'status', 'new'):
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

    # download timesheet file from dropbox account
    subprocess.call(['bash', DROPBOX_CLIENT, 'download', 'Timesheet', FILENAME_TIMESHEET])

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

        # delete time file
        os.remove(FILENAME_TIME)

        # upload timesheet file to dropbox account
        subprocess.call(['bash', DROPBOX_CLIENT, 'upload', FILENAME_TIMESHEET, 'Timesheet'])
    except IOError:
        # timer needs to be started first
        print 'Timer needs to be started first!!!'

# check if started or stopped
elif mode == 'status':
    # get timer status
    if os.path.isfile(FILENAME_TIME):
        print 'Timer started!!!'
    else:
        print 'Timer stopped!!!'

    # hours worked this week
    with open(FILENAME_TIMESHEET, 'r') as f:
        d = file_to_array(f)
        print 'Current week:', timesheet_per_week(d)

# new timesheet today
elif mode == 'new':
    with open(FILENAME_TIMESHEET, 'a') as f:
        today_date = datetime.now().strftime("%Y-%m-%d")
        f.write('%s 00:00:00\n' % today_date)
