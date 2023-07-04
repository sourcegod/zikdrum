#!/usr/bin/python3
"""
    File: midisched.py:
    Module for scheduling midi events 
    Last update: Tue, 04/07/2023
    Date: Mon, 04/07/2022
    Author: Coolbrother
"""

import time
import threading

class MidiSched(object):
    """ 
    Midi scheduler manager with mido module and time clock system
    """
    def __init__(self):
        self._player = None
        self._seq = None
        self._base = None
        self.midi_man = None
        self.playpos =0 # in tick
        self.msg_lst = []
        self._playing =0
        self._paused =0
        self._recording =0
        self.incoming =0 # for incoming messages
        self._play_thread = None
        self.rec_track = None
        self.start_time =0
        self.curtime =0
        self.end_rectime =0
        self.start_recpos =0
        self.end_recpos =0
        self.first_rectime = None # for recorded message
        self.first_recpos = None
        self.rec_lst = [] # temporary recorded list
        self.rec_mode =0 # mix mode
        self.rec_waiting =0
        self.click_track = None
        self._clicking =0
        self._thread_running =0
        self.click_recording =0
        self.click_playing =0
        self.last_time =0
        self.start_time =0

    #-------------------------------------------

    def init(self, midi_driver):
        """ 
        init the midi driver to the midi scheduler
        from MidiSched object
        """

        self.midi_man = midi_driver


    #-----------------------------------------

    def close(self):
        """
        close the midi scheduler
        from MidiSched object
        """

        if self.midi_man:
            self.midi_man = None

    #-----------------------------------------

    def set_player(self, player):
        """ 
        set midi player through the midi scheduler
        from MidiSched object
        """

        if player:
            self._player = player
            self._seq = player.curseq
            self._base = player.curseq.base

    #-----------------------------------------

    def is_running(self):
        """
        whether the Midi Engine is running
        from MidiSched object
        """

        return self._thread_running

    #-----------------------------------------

    def init_clock(self):
        """
        returns absolute time
        from MidiSched object
        """

        return time.time()

    #-----------------------------------------
    
    def reset_clock(self):
        """
        resetting time parameters
        from MidiSched object
        """
        # scheduling time
        curpos = self._seq.get_position()
        self.last_time = self._base.tick2sec(curpos)
        seq_len = self._seq.get_length()
        self.start_time = self.init_clock()

    #-----------------------------------------


    def get_relclock(self):
        """
        returns relatif timing since start_time
        from MidiSched object
        """

        return (time.time() - self.start_time) + self.last_time

    #-----------------------------------------

    def poll_out(self):
        """
        polling out midi data
        from MidiSched object
        """

        # scheduling time
        midi_callback = self._player._midi_callback
        while self._thread_running:
            # debug("")
            midi_callback()
            # pauses the system, necessary to change position
            time.sleep(0.1)
    
    #-----------------------------------------
   
 
    def start_play_thread(self):
        """
        start sending  midi data thread
        from MidiSched object
        """

        if self._thread_running: return
        # self.stop_play_thread()
        if self._play_thread is None:
            self._thread_running =1
            self._playing =1
            self._play_thread = threading.Thread(target=self.poll_out, args=())
            self._play_thread.daemon = True
            self._play_thread.start()
            # debug("Je passe en start_play_thread")

    #-----------------------------------------

    def stop_play_thread(self):
        """
        stop sending midi data thread
        from MidiSched object
        """

        self._thread_running =0
        self._playing =0
        self._play_thread = None
        time.sleep(0.1)
        

    #-----------------------------------------

#========================================

if __name__ == "__main__":
    sch = MidiSched()
    input("It's Ok")
#-----------------------------------------
