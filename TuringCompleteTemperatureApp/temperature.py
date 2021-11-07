#!/usr/bin/python

import os
import time
import glob
import sys
from threading import Thread
from notification import Notification
from collections import deque

from read_sensor import get_readings

MAC_ADDRESS = 'REPLACE_HERE'

def get_temp():
    readings = get_readings(mac_address=MAC_ADDRESS)
    if not readings:
        return None
    temp_c, humidity =  readings

    temp_f = temp_c * 9.0 / 5.0 + 32.0
    return temp_c, temp_f

class Temperature:
    # current value is degrees F, the default
    current_value = 0
    current_value_c = 0;
    historical_values = deque(maxlen=50)
    counter = 0

    # target value is degrees F, the default   
    target_value = None
    increasing_target = True
    target_reached = False

    notifications = []

    should_stop = False

    def __init__(self):
        print("Temperature init")
        self.read_value()

    def read_value(self):
        val = get_temp();
        if val != None:
            self.current_value_c = val[0]
            self.current_value = int(val[1])
            self.add_history(time.time(), self.current_value)
            self.check_target()

    def add_history(self, timestamp, value):
        if self.counter == 5:
            #print "adding value to history " + timestamp + "  " + str(value)
            self.historical_values.append( [timestamp, value] )
            self.counter = 0
        else:
            self.counter += 1

    def print_history(self):
        for elem in self.historical_values:
            #print "%s  %i" % elem[0], elem[1]
            #print str(elem)
            print(elem[0] + "  " + str(elem[1]))

    def set_target(self, target_temp):
        print("setting target to " + str(target_temp))
        self.target_value = target_temp
        self.increasing_target = True if target_temp > self.current_value else False
        self.target_reached = False

    def clear_target(self):
        self.target_value = None
        self.target_reached = False

    def check_target(self):
        if self.target_value and not self.target_reached:
            if (self.increasing_target and self.current_value >= self.target_value) or (not self.increasing_target and self.current_value <= self.target_value):
                self.target_reached = True
                self.fire_target_reached()

    def fire_target_reached(self):
        msg = "Target temp of %i F was reached!" % (self.target_value)
        print(msg)
        for notification in self.notifications[:]:
            print("notifying " + notification.email)
            notification.send(msg)
            self.notifications.remove(notification)

    def add_notification(self, notification):
        # don't add duplicate
        if not [x for x in self.notifications if x.email == notification.email]:
        #if not notification in self.notifications:
            print("adding notification for " + notification.email)
            self.notifications.append(notification)
        else:
            print("not adding duplicate notification")

    def loop(self):
        while self.should_stop is False:
          self.read_value()
          time.sleep(5)
        print("Loop exited")

    def start(self):
        self.should_stop = False
        print("Starting thread")
        t = Thread(target=self.loop)
        t.start()

    def stop(self):
        print("Stop requested")
        self.should_stop = True

    def _test_notification(self):
        print("%i F" % (self.current_value))
        time.sleep(1)
        print("target %i F" % (self.current_value + 2))
        self.set_target(self.current_value+2)
        self.add_notification(Notification("todd@quessenberry.com"))
        self.current_value = self.current_value + 3
        self.check_target()

    def _test_history(self):
        for i in range(60):
            #print "reading..."
            self.read_value()
            time.sleep(1)
        self.print_history()

if '__main__' == __name__:
    temp = Temperature()
    temp.read_value()
    #temp.start()
    #time.sleep(2)
    temp.set_target(75)
    temp.read_value()
    temp.set_target(-1)
    #for i in range(10):
    #    print "%i F " % (temp.current_value)
    #    time.sleep(2)
    #temp.stop()
    #temp._test_notification()
    #temp.add_notification(Notification("todd@quessenberry.com"))
    #temp.add_notification(Notification("todd@quessenberry.com"))
    #temp._test_history()

    #while True:
    #    print(get_temp())
    #    time.sleep(1)
