#!/usr/bin/python3
"""
    File: evenqueue.py:
    Singleton object for transmitting midi events between objects
    Date: Wed, 19/07/2023
    Author: Coolbrother
"""

class EventQueue(object):
    """ 
    Singleton object
    Midi Event queue between objects
    """
    _single_instance = None
    @staticmethod
    def get_instance():
        """ Static access method """
        if EventQueue._single_instance is None:
            EventQueue()
        return EventQueue._single_instance

    #-----------------------------------------

    def __init__(self):
        if EventQueue._single_instance is None:
            EventQueue._single_instance = self
        else:
            # raise Exception("This Klass is a singleton klass.")
            print("Error: this Klass is a singleton klass.")
            return
        
    #-----------------------------------------

#========================================

if __name__ == "__main__":
    evq = EventQueue.get_instance()
    evq = EventQueue()
    input("It's OK...")
#-----------------------------------------

