#!/usr/bin/python3
"""
    File: midiplayer.py:
    Module for playing midi events 
    Date: Mon, 04/07/2022
    Author: Coolbrother
"""

import time
import miditools as midto
import midisequence as midseq
import midisched as midsch
import logger as log
import eventqueue as evq

log.set_level(log._OFF)
# log.set_level(log._DEBUG)
_evq_instance = evq.get_instance()

_DEBUG =1
_LOGFILE = "/tmp/zikdrum.log"
_BELL =1
_WRITING_FILE =1

def debug(msg="", title="", bell=True, writing_file=False, stdout=True, endline=False):
    if not _DEBUG: return
    txt = ""
    if title: txt = f"{title}: "
    if msg: txt += f"{msg}"
    
    if stdout: print(txt)
    if _BELL or bell: print("\a")

    if _WRITING_FILE or writing_file:
        # open file in append mode
        with open(_LOGFILE, 'a') as fh:
            # _logfile.write("{}:\ {}\n".format(title, msg))
            print(txt, file=fh) 
            if endline: print("", file=fh)

#------------------------------------------------------------------------------

class MidiPlayer(object):
    """
    Player manager
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.curseq = None
        self._base = None # MidiBase object in the sequencer
        self.midi_man = None
        self._midi_sched = None # for midi scheduler
        self.trackedit = midto.MidiTrackEdit()
        self.playpos =0 # in tick
        self.msg_lst = []
        self._playing =0
        self._start_playing =0
        self._paused =0
        self._recording =0
        self.incoming =0 # for incoming messages
        self._play_thread = None
        self.rec_track = None
        self.start_time =0
        self.curtime =0
        self.last_time =0
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
        self._bpm_changed =0
        self._count =0
        self._loop_count =0
        self._bpm =0
        self._delay_time = 0.010


    #-----------------------------------------

    def set_sequencer(self, seq):
        """
        set the current sequencer
        from MidiPlayer object
        """

        self.curseq = seq
        if self.curseq:
            self._base = self.curseq.base
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
            self._base = self.curseq.base
            # self.curseq.gen_default_data()
            self.curseq.init_sequencer(self.midi_man)
            # self.click_track = self.curseq.click_track
        self._midi_sched = midsch.MidiSched()
        self._midi_sched.init(self.midi_man)
        self._midi_sched.set_player(self)
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
        
        """
        state = self._playing
        if state: 
            self._playing =0
            self.midi_man.panic()
            pass
        """

        self.curseq.set_bpm(bpm)
        
        # Note: Normally, without panic function, needing a pause after set_bpm function, 
        # time.sleep(0.1)
        # Sets the Sequencer to the current position
        self.set_position(-1)
        
       
    #-----------------------------------------

    def play(self):
        """
        play midi events
        from MidiPlayer object
        """
           
        if self.curseq is None: return
        if not self._playing:
            self._playing =1
            self._start_playing =1
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
        self._start_playing =0
        self._paused =1
        if self._recording:
            self.stop_record()
        # self.stop_midi_engine()
        self.midi_man.panic()
        self.init_click()
        # check whether recording data is waiting before generate the track line
        self.check_rec_data()
        
        # Updating tracks with the current position
        self.curseq.update_tracks_position(-1)
       
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
        self._start_playing =0
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
        played = self._playing
        clicked = self._clicking
        if pos == -1: pos = self.get_position()
        if played:
            self._playing =0
            # self.stop_engine()
            # Note: Panic function is very important, to pause the Midi system
            self.midi_man.panic()
        if clicked:
            self.stop_click()
        if played or clicked:
            ### Note: Delay is necessary to pause the loop callback, and go out
            time.sleep(self._delay_time)

        self.init_pos()
        self.curseq.set_position(pos)
        
        if played:
            self._playing =1
            self._start_playing =1
            # self.start_engine()
            # time.sleep(0.1)
        if clicked:
            self.start_click()
        
        return pos
    #-----------------------------------------

    def get_length(self):
        """
        returns length player
        from MidiPlayer
        """
        
        if self.curseq is None: return 0
        # position in trackline is in time
        # log.debug("voici len player : {} ".format(val))
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
        # Saving the sequencer current position
        self.curseq.curpos = pos
    
    #-----------------------------------------

    def get_bar(self, pos=-1):
        """
        TODO: this function can be replaced by tick2bar in MidiBase object
        convert pos in tick to bar
        from MidiPlayer
        """
 
        (nb_bars, nb_beats, nb_ticks) = self.curseq.get_bar(pos)

        return (nb_bars, nb_beats, nb_ticks)
       
    #-----------------------------------------


    def goto_bar(self, pos):
        """
        Goto bar number
        from MidiPlayer
        """
        
        pos = self._base.bar2tick(pos)
        self.set_position(pos)

    #-----------------------------------------

    def prev_bar(self, step=1):
        """
        set prev bar 
        from MidiPlayer object
        """
        
        if step <=0: step =1
        pos = self.get_position() # in ticks
        nb_tick = self._base.bar2tick(step)
        if nb_tick <=0: return # avoid Zero Division Error
        (div, rest) = divmod(pos, nb_tick)
        if rest == 0:
            pos -= nb_tick
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
        nb_tick = self._base.bar2tick(step)
        if nb_tick <=0: return # avoid Zero Division Error
        (div, rest) = divmod(pos, nb_tick)
        if rest == 0:
            pos += nb_tick
        else:
            pos += nb_tick - rest
        
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
        self.last_time =-1
        self.msg_lst = []
        
    #-----------------------------------------
    
    def init_click(self):
        """
        init click
        from MidiPlayer
        """

        if self.click_track is None:
            # debug("init click: click_track is None")
            self.click_track = self.curseq.click_track
        assert self.click_track, "click_track is None"
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
            # log.debug("voici start_recpos: {}, end_recpos: {}".format(self.start_recpos, self.end_recpos))
            # regenerate midi time set
            # tracknum = self._tracks_arm[0]
            # tracknum = self._tracks_arm[0]
            # on current track
            tracknum = self.tracknum
            rec_track = self.get_track()
            ev_lst = rec_track.get_list()
            if self.rec_mode == 1: # replace mode
                # log.debug("voici list: {}".format(msg_lst))
                for (i, ev)  in enumerate(ev_lst):
                    # log.debug("msg_time: {}".format(msg.time))
                    msg = ev.msg
                    if msg.time >= self.start_recpos and msg.time <= self.end_recpos:
                        del ev_lst[i]
                        # log.debug("voici : {}".format(i))
            val = len(self.rec_lst)
            # log.debug("len rec_lst: {}".format(val))
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
            # log.debug("je suis la")

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

    def get_time(self):
        """
        Returns real time
        from MidiPlayer object
        """
        
        return time.time()

    #-----------------------------------------

    def set_reltime(self, pos=-1):
        """
        resetting time parameters
        from MidiPlayer object
        """
        # scheduling time
        if pos == -1: 
            pos = self.get_position()
            self.last_time = self._base.tick2sec(pos)
        else:
            self.last_time = pos

        self.start_time = time.time()
        
        return self.last_time
    #-----------------------------------------

    def init_start_time(self):
        """
        init start_time
        from MidiPlayer object
        """
        
        self.start_time = time.time()

    #-----------------------------------------

    def get_reltime(self):
        """
        returns relatif timing since start_time
        from MidiPlayer object
        """

        return (time.time() - self.start_time) + self.last_time

    #-----------------------------------------
    def set_last_time(self, _time):
        """
        Sets the last time position
        from MidiPlayer object
        """

        self.last_time = _time

    #-----------------------------------------


    def _midi_callback0(self):
        """
        Deprecated function
        polling out midi data
        from MidiPlayer object
        """

        _is_running = self._midi_sched.is_running
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

        log.debug("")
        while self._playing and _is_running():
            # log.debug("In Loop")
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
                        self.msg_lst = self.curseq.get_playable_data(self.playpos)
                        # log.debug("voici playpos: {}".format(self.playpos))
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
                    # log.debug("count_msg: {}".format(count))
                
              
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
   
    def _midi_callback(self):
        """
        polling out midi data
        from MidiPlayer object
        """

        msg_lst = []
        click_lst = []

        _is_running = self._midi_sched.is_running
        _get_playable_data = self.curseq.get_playable_data
        _tick2sec = self._base.tick2sec
        _sec2tick = self._base.sec2tick
        _get_click_data = self.curseq.get_click_data
        _timeline = self.curseq._timeline

        _out_queue = self.midi_man.get_out_queue()
        _deq_push_item = self.midi_man.push_item
        _deq_is_pending = self.midi_man.is_pending
        _deq_count = self.midi_man.count
        _deq_poll_out = self.midi_man.poll_out

        # debug(f"is_clicking: {self._clicking}")
        if not (_is_running()): return
        if not (self._playing or self._clicking): return
       
        seq_pos = self.get_position()
        seq_len = self.get_length()
        curtick = seq_pos # curtick = self.get_position()
        curtime = _tick2sec(curtick)
        next_tick =0
        next_time =0
        reltime =0 # relative clock timing
        _bpm_changed =0
        _delay_time = self._delay_time
        if self.last_time == -1:
            self.set_last_time(curtime)

        if self._start_playing:
            self.init_start_time() # time.time()
            _out_queue.clear()
            self._count =0
            self._loop_count =0
            self._start_playing =0
            self._bpm_changed =0

        if self._clicking:        
            self.init_start_time() # time.time()
            # self.set_last_time(0)
            self.set_reltime(0)
            if _out_queue: _out_queue.clear()

        log.debug("\nFunc: Enter in _midi_callback", "MidiPlayer Info")
        log.debug(f"\nBefore the loop, curtick: {curtick}, next_tick: {next_tick}, last_time: {self.last_time:.3f}")
        debug("")
        # if self._playing and _is_running():
        while (_is_running()\
                and (self._playing or self._clicking)):
            # debug("")
            # First, Getting the relatif position timing in msec when playing
            ### Note: its depend for tick2sec function, sec_per_tick, sec_per_beat, and tempo variable
            reltime = self.get_reltime() # (time.time() - self.start_time) + self.last_time
            
            if self._playing:
                # Convert this position in tick to get midi events
                seq_pos = self.get_position() # in tick
                seq_len = self.get_length() # in tick
                self.set_play_pos(curtick)
                # print(f"curtime: {self.curtime:.3f}, curtick: {self.playpos}, seq_pos: {seq_pos}")
                if not self._playing: pass # break # exit the loop
                if self._recording:
                    self.set_play_pos(curtick)
                else: # not recording
                    pass

                # Whether is looping
                if self.curseq.looping:
                    curtick = _sec2tick(reltime)
                    self.set_play_pos(curtick)
                else: # not looping
                    pass
                    
                    """
                    # manage player position in time without changing tracks position
                    if seq_pos < seq_len:
                        self.set_play_pos(curtick)
                    """
             
               
                # Getting msg from data list
                if not _out_queue: # test whether the queue is empty
                    
                    """
                    log.debug(f"\nStarting Loop at loop_count: {self._loop_count}", bell=0)
                    log.debug(f"No data in the buffer, at reltime: {reltime:.3f},\n"
                            f"    curtick: {curtick}, curtime: {curtime:.3f}, next_tick: {next_tick}", bell=0)
                    log.debug(f"Before retrieve data, curtick: {curtick}", bell=0)
                    """

                    # play_pos = _sec2tick(curtime)
                    msg_lst = _get_playable_data(curtick)
                    _deq_push_item(*msg_lst)
                    # log.debug(f"After retrieve data, curtick: {curtick},  _deq_data count: {_deq_count()}", bell=0)

                    # """
                    if _evq_instance.is_pending():
                        evmsg = _evq_instance.pop_event()
                        if evmsg.type == evq.EVENT_BPM_CHANGED: # and evmsg.value <= 83:
                            self._bpm_changed =1
                            self._bpm = evmsg.value
                            # curtime = _tick2sec(curtick)

                            """
                            debug(f"Bpm Changed: {evmsg.value:.3f}, at curtick: {curtick},\n"
                                    f"    cur_reltime: {reltime:.3f}, curtime: {curtime:.3f}") 
                            """

                            _bpm_changed =1
                            # self._playing =0
                            # break
                    # """

                    """
                    if not _out_queue:
                        self._count += 1
                        # log.debug(f"No data retrieved from the playable, At curtick: {curtick}, next_tick: {next_tick}, _count: {self._count}")
                    else:
                        if self._count: 
                            # log.debug(f"There was data in the buffer, Total Count: {self._count}, at curtick: {curtick}", bell=0)
                        # self._count =0
                    """

          
                # Drain out the queue
                if reltime >= curtime: 
                    # Sending ev
                    # log.debug(f"Sending message, and Drain out _deq_data with count: {_deq_count()}, at reltime: {reltime:.3f},\n" 
                    #        f"    curtick: {curtick}, curtime: {curtime:.3f}\n", bell=0)
                    _deq_poll_out(extra_proc=None)
                
                    # Manage next events
                    if not _out_queue:
                        # log.debug(f"Now _deq_data is empty at curtick: {curtick}, next_tick:  {next_tick}", bell=0)
                        # Getting next tick
                        next_tick = _timeline.next_ev_time()
                        # debug(f"Last Tick: {next_tick}", writing_file=True)
                        # (_, next_tick) = _timeline.next_group_time()
                        if next_tick == -1: 
                            
                            """
                            # self.pause()
                            log.debug(f"Stopping the Loop at: "
                                    f"curtick: {curtick}, curtime: {curtime:3.3f},\n")
                            # debug(f"Last Tick: {next_tick}", writing_file=True)
                            """
                            # Saving the player position
                            self.set_play_pos(curtick)
                            # break
                            self._playing =0
                            return -1
                            
                        next_time = _tick2sec(next_tick)
                        # log.debug(f"After forward timeline, next_tick: {next_tick}, next_time: {next_time:.3f}", bell=0)
                        if _bpm_changed:
                            old_reltime = reltime
                            jumptime = _tick2sec(curtick)
                            reltime = self.set_reltime(jumptime)
                            _bpm_changed =0
                            
                            """
                            debug(f"After Tempo changed: old_reltime: {old_reltime:.3f}, curtick: {curtick}, curtime: {curtime:.3f},\n"
                                    f"    new reltime: {reltime:.3f}, next_tick: {next_tick}, next_time: {next_time}")
                            """

                        curtick = next_tick
                        curtime = next_time
                        # Saving the player position
                        # self.set_play_pos(curtick)
                        # break
                        # debug(f"reltime: {reltime:.3f}, curtime: {curtime:.3f}")
            # Not playing
            # click part
            elif self._clicking: # not playing
                if not _out_queue:
                    click_lst = _get_click_data()
                    # debug(f"reltime: {reltime:.3f}, click len: {len(click_lst)}")
                    _deq_push_item(*click_lst)
                # getting click_ev
                try:
                    click_ev = click_lst[0]
                except IndexError:
                    click_ev = None
                
                if click_ev:
                    if reltime >= click_ev.time:
                        # debug(f"reltime: {reltime:.3f}, click_time: {click_ev.time}")
                        # send ev
                        _deq_poll_out()
                
                        # for click_ev in click_lst:
                        #     self.midi_man.send_imm(click_ev.msg)
                        # delete msg in the buffer after sending
                        click_lst = []
                    pass

            self._loop_count +=1
            time.sleep(_delay_time)

        # Out of loop
        log.debug(f"\nOut of loop, clearing _deq_data with count: {_deq_count()}")
        
        # Saving the curtime position
        last_tick = curtick # _sec2tick(curtime) # in tick
        last_time = reltime
        if not self._playing:
            self.set_last_time(reltime)
        # self.set_play_pos(last_tick)
        log.debug(f"After the loop, last_tick: {last_tick}, next_tick: {next_tick},\n" 
                f"    curtime: {curtime:.3f}, reltime: {reltime:.3f}, last_time: {last_time:.3f}")
    #-----------------------------------------
   


    def start_midi_engine(self):
        """
        start the midi engine
        from MidiPlayer object
        """

        self._midi_sched.start_play_thread()
        # self._midi_sched.reset_clock()
        self.init_click()
            
    #-----------------------------------------

    def stop_midi_engine(self):
        """
        stop the midi engine
        from MidiPlayer object
        """

        self._midi_sched.stop_play_thread()
            
    #-----------------------------------------

    def is_running(self):
        """
        Tests the Midi Engine
        from MidiPlayer object
        """

        return self._midi_sched.is_running()
            
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
        
        # self.init_click()
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
        log.debug(msg, title, writing_file=True, stdout=False, endline=True)
        
        # display track names
        for (i, name) in enumerate(self.curseq.track_names):
            msg = "Track {}@{} {}".format(i, name[0], name[1])
            log.debug(msg, "", writing_file=True, stdout=False, endline=False)
        log.debug("", writing_file=True, stdout=False, endline=False)
        
        
        # display all events
        if type == 0: # from interl midi tracks
            title = "From internal midi tracks "
            log.debug("", title, writing_file=True, stdout=False)
            for (i, track) in enumerate(self.curseq.track_lst):
                title = "Track {}".format(i)
                log.debug("", title, writing_file=True, stdout=False)
                ev_lst = track.get_list()
                ev_len = len(ev_lst)
                ev_total += ev_len
                for (j, ev) in enumerate(ev_lst):
                    msg = ev.msg
                    log.debug(repr(msg), writing_file=True, stdout=False)
                msg = "Track ev count: {}".format(ev_len)
                log.debug(msg, writing_file=True, stdout=False, endline=False)
                
            msg = "Total ev count: {}".format(ev_total)
            log.debug(msg, writing_file=True, stdout=False, endline=True)
        else: # from midi file tracks
            ev_len =0
            ev_total =0
            title = "From Midi file tracks "
            log.debug("", title, writing_file=True, stdout=False)
            for (i, track) in enumerate(self.curseq.mid.tracks):
                title = "Track {}".format(i)
                log.debug("", title, writing_file=True, stdout=False)
                ev_len = len(track)
                ev_total += ev_len
                for (j, ev) in enumerate(track):
                    msg = ev
                    log.debug(repr(msg), writing_file=True, stdout=False)
                msg = "Track ev count: {}".format(ev_len)
                log.debug(msg, writing_file=True, stdout=False, endline=False)
                
            msg = "Total ev count: {}".format(ev_total)
            log.debug(msg, writing_file=True, stdout=False, endline=True)


    #-----------------------------------------
    
    def log_ev_count(self, tracknum=-1):
        """
        returns total ev count for each track
        from MidiPlayer object
        """

        ev_count =0
        title = "Event count from internal tracks"
        log.debug("", title, writing_file=True, stdout=False, endline=False)
        for (i, track) in enumerate(self.track_lst):
            ev_lst = track.get_list()
            ev_len = len(ev_lst)
            ev_count += ev_len
            try:
                name = self.track_names[i][0]
            except IndexError:
                name = ""
            msg = "Track {}@{} {} events".format(i, name, ev_len)
            log.debug(msg, "", writing_file=True, stdout=False, endline=False)
            # log.debug(msg)
        msg = "Total evs count: {}".format(ev_count)
        log.debug(msg, writing_file=True, stdout=False, endline=True)
        
        # from midi file tracks
        ev_count =0
        title = "Event count from midi file tracks"
        log.debug("", title, writing_file=True, stdout=False, endline=False)
        for (i, track) in enumerate(self.mid.tracks):
            # ev_lst = track.get_list()
            ev_len = len(track)
            ev_count += ev_len
            try:
                name = self.track_names[i][0]
            except IndexError:
                name = ""
            msg = "Track {}@{} {} events".format(i, name, ev_len)
            log.debug(msg, "", writing_file=True, stdout=False, endline=False)
        msg = "Total evs count: {}".format(ev_count)
        log.debug(msg, writing_file=True, stdout=False, endline=True)
     
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
#-----------------------------------------
