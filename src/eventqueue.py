#!/usr/bin/python3
"""
    File: evenqueue.py:
    Implement a Singleton object and a ring buffer for transmitting midi events between objects
    Inspired from Hydrogen Drumkit v0.9
    Date: Wed, 19/07/2023
    Author: Coolbrother
"""

### Enum EventType
EVENT_NONE =0
EVENT_STATE =1
EVENT_MIDI_ACTIVITY =2
EVENT_NOTEON =3
EVENT_ERROR =4
EVENT_TEMPO_CHANGED =5
EVENT_BPM_CHANGED =6
EVENT_PROGRESS =7

#-----------------------------------------

class EventMessage(object):
    type = EVENT_NONE
    value =0

#========================================

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
        
        self._max_ev =1024
        self._ev_buffer = [EventMessage] * self._max_ev
        self._read_index =0
        self._write_index =0

    #-----------------------------------------

    def push_event(self, type, value):
        self._write_index +=1 # We will be able to count number of writings
        index = self._write_index % self._max_ev
        ev = EventMessage()
        ev.type = type
        ev.value = value
        self._ev_buffer[index] = ev

    #-----------------------------------------

    def pop_event(self):
        if self._read_index == self._write_index:
            ev = EventMessage() # None event
            return ev
        
        self._read_index +=1 # We save the read_index count
        index = self._read_index % self._max_ev
        return self._ev_buffer[index]

    #-----------------------------------------
    
    def is_pending(self):
        """
        Check whether we can read from the buffer
        from EventQueue object
        """

        return self._read_index != self._write_index

    #-----------------------------------------

#========================================

def get_instance():
    return EventQueue.get_instance()

#-----------------------------------------

if __name__ == "__main__":
    evq = EventQueue.get_instance()
    evq = EventQueue()
    input("It's OK...")
#-----------------------------------------

