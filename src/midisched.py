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
        from SystemScheduler object
        """

        self.midi_man = midi_driver


    #-----------------------------------------

    def close(self):
        """
        close the midi scheduler
        from SystemScheduler object
        """

        if self.midi_man:
            self.midi_man = None

    #-----------------------------------------

    def set_player(self, player):
        """ 
        set midi player through the midi scheduler
        from SystemScheduler object
        """

        if player:
            self._player = player
            self._seq = player.curseq
            self._base = player.curseq.base

    #-----------------------------------------

    def is_running(self):
        """
        whether the Midi Engine is running
        from SystemScheduler object
        """

        return self._thread_running

    #-----------------------------------------

    def init_clock(self):
        """
        returns absolute time
        from SystemScheduler object
        """

        return time.time()

    #-----------------------------------------
    
    def reset_clock(self):
        """
        resetting time parameters
        from SystemScheduler object
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
        from SystemScheduler object
        """

        return (time.time() - self.start_time) + self.last_time

    #-----------------------------------------

    def poll_out0(self):
        """
        Deprecated Function
        polling out midi data
        from SystemScheduler object
        """

        # Todo: dont init click_lst
        msg_ev = None
        msg_timing =0
        msg_pending =0
        finishing =0
        click_lst = []
        click_ev = None
        click_pending =0
        click_timing =0

        # scheduling time
        curpos = self._seq.get_position()
        self.last_time = self._base.tick2sec(curpos)
        seq_len = self._seq.get_length()
        self.start_time = self.init_clock()

        while 1:
            # debug("")
            if not self._thread_running: break
            if not self._player.is_playing() and not self._player.is_paused():
                if finishing:
                    self._thread_running =0
                    break

            # get timing in msec
            ### Note: its depend for tick2sec function, sec_per_tick, sec_per_beat, and tempo variable
            self.curtime = self.get_relclock() # (time.time() - self.start_time) + self.last_time
            # Values in tick
            self.playpos = self._base.sec2tick(self.curtime) # in tick
            seq_pos = self._seq.get_position() # in tick
            seq_len = self._seq.get_length() # in tick
            # print(f"curtime: {self.curtime:.3f}, curtick: {self.playpos}, seq_pos: {seq_pos}")
            if not self._player.is_playing():
                finishing =1
            else: # playing
                finishing =0
                if self._player.is_recording():
                    self._player.set_play_pos(self.playpos)
                else: # not recording
                    if self._seq.looping:
                        if seq_len >0:
                            self._player.set_play_pos(self.playpos)
                    else: # not looping
                        if seq_pos < seq_len:
                            self._player.set_play_pos(self.playpos)
                 
                # whether is looping
                if self._seq.loop_manager():
                    self.start_time = self.init_clock()
                    # self._player.check_rec_data()
                    msg_ev = None
                    msg_timing =0
                    msg_pending =0
                    self.msg_lst = []
                    # click part
                    click_ev = None
                    click_pending =0
                    click_timing =0
                    click_lst = []
                
                # msg part
                if not msg_timing and not msg_pending:
                    finishing =1
                    # msg_lst can be saved
                    if not self.msg_lst:
                        self.playpos = self._base.sec2tick(self.curtime)
                        # self._base.update_tempo_params()
                        self.msg_lst = self._seq.get_midi_data(self.playpos)
                        # debug("voici playpos: {}".format(self.playpos))
                        if self.msg_lst:
                            msg_pending =1
                            finishing =0
                    else: # msg_lst can be saved
                        msg_pending =1
                        finishing =0
               
                # msg part
                # whether is msg_lst or ev is pending
                if msg_ev is None and msg_pending and self.msg_lst:
                    msg_ev = self.msg_lst[0]
                    msg_timing =1
                    # there is data in the list
                    msg_pending =1
                    # debug("count_msg: {}".format(count))
                
              
                # msg part
                if msg_ev:
                    """
                    if self.curtime >= msg_ev.msg.time:
                    # waiting time
                    # while self.curtime < msg_ev.msg.time:
                        time.sleep(0.001)
                        msg_timing =1
                        # there is an ev in the list, cause not yet poped
                        msg_pending =1
                    """

                    # send ev
                    tracknum = msg_ev.tracknum
                    track = self._seq.get_track(tracknum)
                   
                    if not track.muted and not track.sysmuted:
                        # Todo: changing channel and patch message dynamically or statically
                        
                        # """
                        # dont modify drum track
                        if tracknum != 0:
                            # only for recording   ???
                            # changing channel dynamically: during playback
                            msg_ev.msg.channel = track.channel_num
                            pass
                        # """
                        
                        self.midi_man.output_message(msg_ev.msg)
                    # delete msg in the buffer after sending
                    try:
                        self.msg_lst.pop(0)
                    except IndexError:
                        pass
                    msg_ev = None
                    msg_timing =0
                    if not self.msg_lst:
                        msg_pending =0                
                
                    """
                    elif self.curtime < msg_ev.msg.time: 
                        # debug("msg_lst len: {}".format(len(self.msg_lst)))
                        msg_timing =1
                        # there is an ev in the list, cause not yet poped
                        msg_pending =1
                    """

            # click part
            if not self._player.click_track.is_active():
                finishing =1
            else:
                finishing =0
                if not click_timing and not click_pending:
                    if not click_lst:
                        click_lst = self._seq.get_click_data()
                        if click_lst:
                            click_pending =1
                    else: # there is ev in click_lst
                        click_pending =1

                # getting click_ev
                if click_ev is None and click_pending and click_lst:
                    click_ev = click_lst[0]
                    click_timing =1
                    click_pending =1
                
                if click_ev:
                    if self.curtime >= click_ev.msg.time:
                        # send ev
                        track = self._seq.get_track(0)
                        if not track.muted and not track.sysmuted:
                            # print("voici: ", click_ev.msg)
                            self.midi_man.output_message(click_ev.msg)
                        # delete msg in the buffer after sending
                        try:
                            click_lst.pop(0)
                        except IndexError:
                            pass
                        click_ev = None
                        click_timing =0
                        if not click_lst:
                            click_pending =0                
                    elif self.curtime < click_ev.msg.time: 
                        click_timing =1
                        # maybe there is an ev in the list, cause not yet poped
                        click_pending =1

    #-----------------------------------------
    
    def poll_out(self):
        """
        polling out midi data
        from SystemScheduler object
        """

        """
        # Todo: dont init click_lst
        msg_ev = None
        msg_timing =0
        msg_pending =0
        finishing =0
        click_lst = []
        click_ev = None
        click_pending =0
        click_timing =0
        """

        # scheduling time
        curpos = self._seq.get_position()
        self.last_time = self._base.tick2sec(curpos)
        seq_len = self._seq.get_length()
        self.start_time = self.init_clock()
        

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
        from SystemScheduler object
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
        from SystemScheduler object
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
