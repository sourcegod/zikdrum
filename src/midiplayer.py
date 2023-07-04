#!/usr/bin/python3
"""
    File: midiplayer.py:
    Module for playing midi events 
    Date: Mon, 04/07/2022
    Author: Coolbrother
"""

import time
import threading
import miditools as midto
import midisequence as midseq

DEBUG =1
_logfile = None

def debug(msg="", title="", bell=True, write_file=False, stdout=True, endline=False):
    if DEBUG:
        if stdout:
            txt = ""
            if title and not msg:
                txt = "{}".format(title)
            elif msg and not title:
                txt = "{}".format(msg)
            elif msg and title:
                txt = "{}: {}".format(title, msg)
            print(txt)

        if bell:
            # curses.beep()
            print("\a")
        if write_file:
            with open('/tmp/zikdrum.log', 'a') as fh:
                # _logfile.write("{}:\ {}\n".format(title, msg))
                txt = ""
                if title and not msg:
                    txt = "{}:".format(title)
                elif msg and not title:
                    txt = "{}".format(msg)
                elif title and msg:
                    txt = "{}:\n{}".format(title, msg)

                print(txt, file=fh) 

                if endline:
                    print("", file=fh)

#------------------------------------------------------------------------------

def beep():
    # curses.beep()
    print("\a")

#-------------------------------------------

def limit_value(val, min_val=0, max_val=127):
    """ limit value """
    
    if val < min_val: val = min_val
    elif val > max_val: val = max_val
    
    return val

#-------------------------------------------

class SystemScheduler(object):
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

class MidiPlayer(object):
    """
    Player manager
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.curseq = None
        self.midi_man = None
        self.midi_sched = None # for midi scheduler
        self.trackedit = midto.MidiTrackEdit()
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
        self.is_ready = False


    #-----------------------------------------

    def set_sequencer(self, seq):
        """
        set the current sequencer
        from MidiPlayer object
        """

        self.curseq = seq
        if self.curseq:
            self.midi_man = self.curseq.midi_man

    #-----------------------------------------

    def update_player(self):
        """
        update player
        from MidiPlayer object
        """
        
        self.curseq.update_sequencer()
        self.is_ready = False
        
        """
        for track in self.track_lst:
            track.midi_man = self.midi_man
            # track.channel_num =9 # drum channel
            track.set_pos(0)
        # update player length
        self.update_length()
        """

    #-----------------------------------------

    def init_player(self, midi_driver):
        """
        init midi player
        from MidiPlayer object
        """

        self.midi_man = midi_driver
        self.curseq = midseq.MidiSequence(self)
        if self.curseq:
            self.click_track = self.curseq.gen_default_data()
            self.curseq.init_sequencer(self.midi_man)
        self.midi_sched = SystemScheduler()
        self.midi_sched.init(self.midi_man)
        self.midi_sched.set_player(self)
        # generate data for tempo track
        # pass the midi driver to all tracks
        # click on recording
        self.click_recording =1
        self.is_ready = False # True

    #-----------------------------------------

    def close_player(self):
        """
        set the player not ready
        from MidiPlayer object
        """
        self.is_ready = False

    #-----------------------------------------

    def change_bpm(self, bpm):
        """
        set the bpm (beat per minute) and changing the tempo track
        from MidiPlayer object
        """

        if self.curseq is None: return 0
        clicked =0
        if self.is_clicking():
            clicked =1
            self.stop_click()

        
       
        self.curseq.set_bpm(bpm)
        # Sets the Sequencer to the current position
        self.set_position(-1)

        if clicked:
            self.start_click()
        
    #-----------------------------------------

    def update_bpm0(self, bpm):
        """
        Deprecated function
        update the bpm (beat per minute) without changing tempo track
        from MidiPlayer object
        """

        clicked =0
        if self.is_clicking():
            clicked =1
            self.stop_click()
        self.curseq.update_bpm(bpm)
        if clicked:
            self.start_click()
    
    #-----------------------------------------

    def play(self):
        """
        play midi events
        from MidiPlayer object
        """
           
        if self.curseq is None: return
        if not self._playing:
            self._playing =1
            self._paused =0
            if not self.is_running():
                # self.start_midi_engine()
                print(f"Midi Engine is not Running.")

    #-----------------------------------------
    
    def pause(self):
        """
        pause midi events
        from MidiPlayer object
        """
        
        if self.curseq is None: return
        self._playing =0
        self._paused =1
        if self._recording:
            self.stop_record()
        # self.stop_midi_engine()
        self.midi_man.panic()
        self.init_click()
        # check whether recording data is waiting before generate the track line
        self.check_rec_data()
        
        self.curseq.update_tracks_position(self.playpos)
       
    #-----------------------------------------

    def stop(self):
        """
        stop the player
        from MidiPlayer object
        """

        if self.curseq is None: return
        if self._playing or self._paused:
            # self.stop_midi_engine()
            pass
        # self.init_params()
        if self._recording:
            self.stop_record()
        self.finishing =0
        self._playing =0
        self._paused =0
        self._recording =0
        self.midi_man.panic()
        self.check_rec_data()
        self.set_position(0)
        debug()

    #-----------------------------------------
    
    def is_playing(self):
        """
        returns playing state
        from MidiPlayer object
        """
        
        return self._playing

    #-----------------------------------------

    def is_paused(self):
        """
        returns paused state
        from MidiPlayer object
        """
        
        return self._paused

    #-----------------------------------------

    def get_position(self):
        """
        returns player position
        from MidiPlayer object
        """
        
        if self.curseq is None: return 0
        return self.curseq.get_position()

    #-----------------------------------------

    def set_position(self, pos):
        """
        Toggle Engine State whether playing,
        and set player position
        from MidiPlayer object
        """

        if self.curseq is None: return 0
        state = self._playing
        if pos == -1: pos = self.get_position()
        if state:
            self._playing =0
            # self.stop_engine()
            self.midi_man.panic()
        
        self.init_pos()
        self.curseq.set_position(pos)
        
        if state:
            self._playing =1
            # self.start_engine()
            # time.sleep(2)
        
        return pos
    #-----------------------------------------

    def get_length(self):
        """
        returns length player
        from MidiPlayer
        """
        
        if self.curseq is None: return 0
        # position in trackline is in time
        # debug("voici len player : {} ".format(val))
        return self.curseq.get_length()

    #-----------------------------------------

    def set_play_pos(self, pos):
        """
        set player and sequence position without changing tracks position
        Note: useful to passing scheduler position to player and current sequence
        from MidiPlayer object
        """

        if self.curseq is None: return
        self.playpos = pos
        self.curseq.curpos = pos
    
    #-----------------------------------------

    def get_bar(self, pos=-1):
        """
        convert pos in tick to bar
        from MidiPlayer
        """
 
        (nb_bars, nb_beats, nb_ticks) = self.curseq.get_bar(pos)

        return (nb_bars, nb_beats, nb_ticks)
       
    #-----------------------------------------

    def set_bar(self, num=0):
        """
        set bar number
        from MidiPlayer object
        """
        
        try:
            num = int(num)
        except ValueError:
            return

        if num <=0: num =0
        else: num -=1 # temporary, before calculate tick to bar
        # position is in ticks
        pos = self.curseq.base.bar * num
        self.set_position(pos)

        return pos

    #-----------------------------------------

    def prev_bar(self, step=1):
        """
        set prev bar 
        from MidiPlayer object
        """
        
        if step <=0: step =1
        pos = self.get_position() # in ticks
        bar = self.curseq.base.bar * step
        (div, rest) = divmod(pos, bar)
        if rest == 0:
            pos -= bar
        else:
            pos -= rest
        
        # Note: waiting before rewind to not block only on previous bar
        time.sleep(0.1)
        self.set_position(pos)

    #-----------------------------------------

    def next_bar(self, step=1):
        """
        set next bar 
        from MidiPlayer object
        """
        
        pos = self.get_position() # in ticks
        if step <=0: step =1
        bar = self.curseq.base.bar * step
        (div, rest) = divmod(pos, bar)
        if rest == 0:
            pos += bar
        else:
            pos += bar - rest
        
        self.set_position(pos)

    #-----------------------------------------
 
    def rewind(self, step=1):
        """
        rewind player to previous bar
        from MidiPlayer object
        """
        
        self.prev_bar(step)
        
    #-----------------------------------------

    def forward(self, step=1):
        """
        forward player to next bar
        from MidiPlayer object
        """
        
        self.next_bar(step)
        

    #-----------------------------------------

    def goto_start(self):
        """
        goto start player
        from MidiPlayer object 
        """
        
        pos =0
        self.set_position(pos)
        
        return pos

    #-----------------------------------------

    def goto_end(self):
        """
        goto end player
        from MidiPlayer object
        """
        
        pos = self.get_length()
        self.set_position(pos)

        return pos

    #-----------------------------------------
    
    def goto_bar(self, num=0):
        """
        goto Bar
        from MidiPlayer object
        """
        
        pos = self.set_bar(num)

        return pos

    #-----------------------------------------


    def goto_left_locator(self):
        """
        goto left locator 
        from MidiPlayer object
        """
        
        pos = self.curseq.left_loc
        self.set_position(pos)

        return pos

    #-----------------------------------------

    def goto_right_locator(self):
        """
        goto right locator
        from MidiPlayer object
        """
        
        pos = self.curseq.right_loc
        self.set_position(pos)

        return pos

    #-----------------------------------------

    def goto_start_loop(self):
        """
        goto start loop
        from MidiPlayer object 
        """
        
        pos = self.curseq.start_loop
        self.set_position(pos)

        return pos

    #-----------------------------------------

    def goto_end_loop(self):
        """
        goto end loop
        from MidiPlayer
        """
        
        pos = self.curseq.end_loop
        self.set_position(pos)

        return pos

    #-----------------------------------------

    def init_params(self):
        """
        init midi params
        from MidiPlayer object
        """

        self.playpos =0
        # self.msg_lst = []
        # track = self.track_lst[0]
        # track.repeat_count =0
        self.set_position(0)

    #-----------------------------------------

    def init_pos(self):
        """
        init player position
        from MidiPlayer object
        """

        # self.iter_time.cur(0)
        self.init_click()
        # self.trackline.set_pos(0)
        # self.trackline.lastpos =-1
        self.playpos =0
        self.msg_lst = []
        
    #-----------------------------------------
    
    def init_click(self):
        """
        init click
        from MidiPlayer
        """

        self.click_track.set_pos(0)
        self.click_track.lastpos =-1
        self.click_track.repeat_count =0

    #-----------------------------------------

       
    def arrange_rec_data(self):
        """
        arrange recorded data
        from MidiPlayer object
        """

        if self.incoming:
            self.end_rectime = (time.time() - self.first_rectime) 
            self.end_recpos = self.sec2tick(self.end_rectime) + self.start_recpos
            # debug("voici start_recpos: {}, end_recpos: {}".format(self.start_recpos, self.end_recpos))
            # regenerate midi time set
            # tracknum = self._tracks_arm[0]
            # tracknum = self._tracks_arm[0]
            # on current track
            tracknum = self.tracknum
            rec_track = self.get_track()
            ev_lst = rec_track.get_list()
            if self.rec_mode == 1: # replace mode
                # debug("voici list: {}".format(msg_lst))
                for (i, ev)  in enumerate(ev_lst):
                    # debug("msg_time: {}".format(msg.time))
                    msg = ev.msg
                    if msg.time >= self.start_recpos and msg.time <= self.end_recpos:
                        del ev_lst[i]
                        # debug("voici : {}".format(i))
            val = len(self.rec_lst)
            # debug("len rec_lst: {}".format(val))
            # quantize rec_lst for incoming messages
            if self.quantizing:
                self.quantize_track(type=1)
            # convert msg to midi events
            ev_lst = []
            for msg in self.rec_lst:
                newev = MidiEvent()
                newev.msg = msg
                newev.tracknum = tracknum
                ev_lst.append(newev)
            rec_track.add_evs(*ev_lst)
            # update recorded track position
            ev_lst = rec_track.get_list()
            ev_lst.sort(key=lambda x: x.msg.time)
            # self.gen_time_set()
            # there is data recorded in waiting
            self.rec_waiting =1
            self.incoming =0
            self.first_rectime = None
            self.end_rectime = None
            self.start_recpos =0
            self.end_recpos =0

    #-----------------------------------------

    def check_rec_data(self):
        """
        checking the recorded track for data waiting
        from MidiPlayer
        """

        if self.incoming:
            self.arrange_rec_data()
        if self.rec_waiting:
            self.gen_trackline()
            # debug("je suis la")

    #-----------------------------------------
 
    def start_record(self):
        """
        starting record 
        from MidiPlayer
        """
        
        """
        if not self._tracks_arm:
            return
        """
        
        # for input_callback function
        self._recording =1
        self.rec_lst = []

        if self.click_recording:
            self.click_track.active =1
        if not self._playing:
            self.play()

    #-----------------------------------------

    def stop_record(self):
        """
        stop record 
        from MidiPlayer
        """
        
        self._recording =0
        if self.click_recording and not self.click_playing:
            self.click_track.active =0
        # dont generate trackline yet
        # it is done in Pause function when calling check_rec_data
        self.arrange_rec_data()
        
    #-----------------------------------------

    def is_recording(self):
        """
        returns recording state
        from MidiPlayer
        """
        
        return self._recording

    #-----------------------------------------

    def input_callback(self, msg):
        """
        manage incoming midi data
        from MidiPlayer object
        """
        
        if self._recording:
            if self.first_rectime is None:
                self.rec_lst = []
                self.first_rectime = self.playpos # self.curtime # time.time()
                # in tick
                self.start_recpos = self.playpos
                timepos = self.start_recpos
                # timepos is already in tick
                msg.time = timepos
                self.incoming =1
            else:
                # rec_pos = self.tick2sec(self.start_rec_pos)
                timepos = self.playpos - self.first_rectime + self.start_recpos
                # start_recpos is already in tick
                # msg.time = self.sec2tick(time_pos) + self.start_recpos
                msg.time = timepos

            self.rec_lst.append(msg)

        self.midi_man.send_message(msg)
       
        if self.parent:
            self.parent.notify(msg)

    #-----------------------------------------

    def reset_time(self):
        """
        resetting time parameters
        from MidiPlayer object
        """
        # scheduling time
        curpos = self.get_position()
        self.last_time = self.curseq.base.tick2sec(curpos)
        seq_len = self.curseq.get_length()
        self.start_time = time.time()

    #-----------------------------------------

    def get_reltime(self):
        """
        returns relatif timing since start_time
        from MidiPlayer object
        """

        return (time.time() - self.start_time) + self.last_time

    #-----------------------------------------


    def _midi_callback(self):
        """
        polling out midi data
        from MidiPlayer object
        """

        _is_running = self.midi_sched.is_running
        if not (self._playing and _is_running()): return
        # Todo: dont init click_lst
        msg_ev = None
        msg_timing =0
        msg_pending =0
        finishing =0
        click_lst = []
        click_ev = None
        click_pending =0
        click_timing =0

        curpos = self.get_position()
        self.last_time = self.curseq.base.tick2sec(curpos)
        seq_len = self.curseq.get_length()
        # start_time = time.time() # self.init_clock()
        self.start_time = time.time() # self.init_time()

        debug("")
        while self._playing and _is_running():
            # debug("In Loop")
            # get timing in msec
            ### Note: its depend for tick2sec function, sec_per_tick, sec_per_beat, and tempo variable
            curtime = self.get_reltime() # (time.time() - self.start_time) + self.last_time
            # Values in tick
            self.playpos = self.curseq.base.sec2tick(curtime) # in tick
            seq_pos = self.get_position() # in tick
            seq_len = self.get_length() # in tick
            # print(f"curtime: {self.curtime:.3f}, curtick: {self.playpos}, seq_pos: {seq_pos}")
            if not self._playing:
                finishing =1
            else: # playing
                finishing =0
                if self._recording:
                    self.set_play_pos(self.playpos)
                else: # not recording
                    if self.curseq.looping:
                        if seq_len >0:
                            self.set_play_pos(self.playpos)
                    else: # not looping
                        if seq_pos < seq_len:
                            self.set_play_pos(self.playpos)
                 
                # whether is looping
                if self.curseq.loop_manager():
                    start_time = time.time() # self.init_clock()
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
                        self.playpos = self.curseq.base.sec2tick(curtime)
                        # self._base.update_tempo_params()
                        self.msg_lst = self.curseq.get_midi_data(self.playpos)
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
                    # send ev
                    tracknum = msg_ev.tracknum
                    track = self.curseq.get_track(tracknum)
                    if not track.muted and not track.sysmuted:
                        # Todo: changing channel and patch message dynamically or statically
                        
                        # dont modify drum track
                        if tracknum != 0:
                            # only for recording   ???
                            # changing channel dynamically: during playback
                            msg_ev.msg.channel = track.channel_num
                        
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
                
            # click part
            if not self.click_track.is_active():
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
                        track = self.curseq.get_track(0)
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
                    elif self.curtime < click_evcurmsg.time: 
                        click_timing =1
                        # maybe there is an ev in the list, cause not yet poped
                        click_pending =1
            # time.sleep(0.001)

    #-----------------------------------------
   

    def start_midi_engine(self):
        """
        start the midi engine
        from MidiPlayer object
        """

        self.midi_sched.start_play_thread()
        # self.midi_sched.reset_clock()
        self.init_click()
            
    #-----------------------------------------

    def stop_midi_engine(self):
        """
        stop the midi engine
        from MidiPlayer object
        """

        self.midi_sched.stop_play_thread()
            
    #-----------------------------------------

    def is_running(self):
        """
        Tests the Midi Engine
        from MidiPlayer object
        """

        return self.midi_sched.is_running()
            
    #-----------------------------------------


    def start_click(self):
        """
        start clicking
        from MidiPlayer object
        """

        if self.is_playing():
            self.click_track.active =1
        else:
            self.click_track.active =1
            # self.start_midi_engine()
        
        self.init_click()
        self._clicking =1
            
        return self._clicking

    #-----------------------------------------

    def stop_click(self):
        """
        stop clicking
        from MidiPlayer object
        """

        if self.is_playing():
            self.click_track.active =0
        else:
            self.click_track.active =0
            # self.stop_engine()
        
        self.init_click()
        self._clicking =0
            
        return self._clicking

    #-----------------------------------------

    def is_clicking(self):
        """
        returns clicking state
        from MidiPlayer object
        """

        return self._clicking

    #-----------------------------------------

    def log_info(self, type=0):
        """
        log info in a file
        type 0: from internal midi tracks
        type 1: from midi file tracks
        from MidiPlayer object
        """
        
        ev_len =0
        ev_total =0
        msg = self.curseq.get_properties()
        title = "Properties"
        debug(msg, title, write_file=True, stdout=False, endline=True)
        
        # display track names
        for (i, name) in enumerate(self.curseq.track_names):
            msg = "Track {}@{} {}".format(i, name[0], name[1])
            debug(msg, "", write_file=True, stdout=False, endline=False)
        debug("", write_file=True, stdout=False, endline=False)
        
        
        # display all events
        if type == 0: # from interl midi tracks
            title = "From internal midi tracks "
            debug("", title, write_file=True, stdout=False)
            for (i, track) in enumerate(self.curseq.track_lst):
                title = "Track {}".format(i)
                debug("", title, write_file=True, stdout=False)
                ev_lst = track.get_list()
                ev_len = len(ev_lst)
                ev_total += ev_len
                for (j, ev) in enumerate(ev_lst):
                    msg = ev.msg
                    debug(repr(msg), write_file=True, stdout=False)
                msg = "Track ev count: {}".format(ev_len)
                debug(msg, write_file=True, stdout=False, endline=False)
                
            msg = "Total ev count: {}".format(ev_total)
            debug(msg, write_file=True, stdout=False, endline=True)
        else: # from midi file tracks
            ev_len =0
            ev_total =0
            title = "From Midi file tracks "
            debug("", title, write_file=True, stdout=False)
            for (i, track) in enumerate(self.curseq.mid.tracks):
                title = "Track {}".format(i)
                debug("", title, write_file=True, stdout=False)
                ev_len = len(track)
                ev_total += ev_len
                for (j, ev) in enumerate(track):
                    msg = ev
                    debug(repr(msg), write_file=True, stdout=False)
                msg = "Track ev count: {}".format(ev_len)
                debug(msg, write_file=True, stdout=False, endline=False)
                
            msg = "Total ev count: {}".format(ev_total)
            debug(msg, write_file=True, stdout=False, endline=True)


    #-----------------------------------------
    
    def log_ev_count(self, tracknum=-1):
        """
        returns total ev count for each track
        from MidiPlayer object
        """

        ev_count =0
        title = "Event count from internal tracks"
        debug("", title, write_file=True, stdout=False, endline=False)
        for (i, track) in enumerate(self.track_lst):
            ev_lst = track.get_list()
            ev_len = len(ev_lst)
            ev_count += ev_len
            try:
                name = self.track_names[i][0]
            except IndexError:
                name = ""
            msg = "Track {}@{} {} events".format(i, name, ev_len)
            debug(msg, "", write_file=True, stdout=False, endline=False)
            # debug(msg)
        msg = "Total evs count: {}".format(ev_count)
        debug(msg, write_file=True, stdout=False, endline=True)
        
        # from midi file tracks
        ev_count =0
        title = "Event count from midi file tracks"
        debug("", title, write_file=True, stdout=False, endline=False)
        for (i, track) in enumerate(self.mid.tracks):
            # ev_lst = track.get_list()
            ev_len = len(track)
            ev_count += ev_len
            try:
                name = self.track_names[i][0]
            except IndexError:
                name = ""
            msg = "Track {}@{} {} events".format(i, name, ev_len)
            debug(msg, "", write_file=True, stdout=False, endline=False)
        msg = "Total evs count: {}".format(ev_count)
        debug(msg, write_file=True, stdout=False, endline=True)
     
    #-----------------------------------------

    def open_midi_file(self, filename):
        """
        open midi file
        from MidiPlayer object
        """
       
        ret =0
        if self.curseq is None: return
        ret = self.curseq.load_file(filename)
        if ret:
            self.click_track = self.curseq.get_click_track()
            # player is ready too
            self.update_player()
            
       
       
        return ret

    #-----------------------------------------

    def new_player(self):
        """
        create new player
        from MidiPlayer object
        """
       
        ret =0
        # self.init_player(self.midi_man)
        if self.curseq is None: return
        self.curseq.new_sequence()
        self.update_player()

        self.is_ready = True
            
        return ret

    #-----------------------------------------


#========================================

if __name__ == "__main__":
    input("It's OK")
