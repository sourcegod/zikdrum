#python3
"""
    File: interfaceapp.py
    Module Application Interface for zikdrum
    Date: Mon, 04/07/2022
    Author: Coolbrother
"""
import os
import midiplayer as midp
import midimanager as midman
import miditools as midto
import utils as uti
import logger as log


# log.set_level(log._DEBUG)
class InterfaceApp(object):
    """ manage interface application"""
    def __init__(self, parent):
        self.parent = parent
        self.midi_man = None
        self.midplay = None
        self.player = None
        self.curseq = None
        self.filename = ""
        self.msg_app = ""
        self.window_num =0
        self.undoman = midto.UndoManager()
        self.tools =  midto.MidiTools()
        self.clip = None
        self._tracks_sel = []

    #-----------------------------------------

    def player_is_ready(self):
        """
        Test the player
        from InterfaceApp object
        """
        
        if self.player and self.player.is_ready:
            return True
        msg = "Error: Player is not Ready"
        # self.notify(msg)
        return False

    #-----------------------------------------

    def init_app(self, midin_port=0, midout_port=0, synth_type=0, midi_filename="", audio_device=""):
        """
        init application
        from InterfaceApp object
        """

        log.init_logfile()
        self.midi_man = midman.MidiManager(self)
        self.midi_man.init_midi(midin_port, midout_port, synth_type, self.filename, audio_device)
        self.midplay = midp
        self.player = midp.MidiPlayer(self)
        self.player.init_player(self.midi_man)
        self.curseq = self.player.curseq
        # self.midi_man.receive_from(port=1, callback=self.midi_man.input_callback)
        # Not receive messages temporary to test External Synth with Timidity ports.
        # self.midi_man.receive_from(port=1, callback=self.player.input_callback)
        self.player.start_midi_engine()
        self.clip = midto.MidiClipboard(self.player)
        self.select = midto.MidiSelector(self.player)
        msg = "Init player"
        self.make_undo(msg)
        self.msg_app = "Groovit Synth..."
        self.notify(self.msg_app)
        if midi_filename:
            self.autoplay(midi_filename)
        else:
            # self.test_synth_engine()
            pass

    #------------------------------------------------------------------------------
        
    def close_app(self):
        """
        close application
        from InterfaceApp object
        """

        self.midi_man.close_midi()

    #------------------------------------------------------------------------------

    def notify(self, msg):
        """
        notify the parent application
        from InterfaceApp object
        """
        if self.parent:
            self.parent.notify(msg)

    #------------------------------------------------------------------------------

    def get_message(self):
        """
        returns the message application
        from InterfaceApp object
        """

        return self.msg_app

    #------------------------------------------------------------------------------

    def program_change(self, prog=0, chan=0, *args, **kwargs):
        """
        Send program change
        from InterfaceApp object
        """

        try:
            prog = int(prog)
            chan = int(chan)
        except ValueError:
            prog =0
            chan =0

       
        self.msg_app = ""
        
        if self.midi_man and self.midi_man.is_active():
            self.midi_man.program_change(chan, prog)
            self.msg_app = f"Program Change, prog: {prog}, chan: {chan}"
        else:
            self.msg_app = "No Synth Engine is available."

        self.notify(self.msg_app)

    #------------------------------------------------------------------------------


    def note(self, key=69, vel=100, dur=4, chan=0, *args, **kwargs):
        """
        play one note to the synth engine
        from InterfaceApp object
        """

        try:
            key = int(key)
            vel = int(vel)
            dur = float(dur)
            chan = int(chan)
        except ValueError:
            key =69
            vel =100
            dur = 4
            chan =0

       
        self.msg_app = ""
        
        if self.midi_man and self.midi_man.is_active():
            self.midi_man.note(key, vel, dur, chan) # play one note
            self.msg_app = "Note"
        else:
            self.msg_app = "No Synth Engine is available."

        self.notify(self.msg_app)

    #------------------------------------------------------------------------------


    def demo(self, prog=None, chan=None, *args, **kwargs):
        """
        play notes to the synth engine
        from InterfaceApp object
        """

        if prog is None: 
            prog =16
        else:
            try:
                prog = int(prog)
            except ValueError:
                prog =16
        if chan is None: 
            chan =0
        else:
            try:
                chan = int(chan)
            except ValueError:
                chan =0
        
        self.msg_app = ""
        
        if self.midi_man and self.midi_man.is_active():
            self.midi_man.demo(prog, chan) # demo test for the synth
            self.msg_app = "Test Synth Engine"
        else:
            self.msg_app = "No Synth Engine is available."

        self.notify(self.msg_app)

    #------------------------------------------------------------------------------



    def test_synth_engine(self, *args, **kwargs):
        """
        play notes to the synth engine
        from InterfaceApp object
        """
        
        self.msg_app = ""
        
        # """
        if self.midi_man and self.midi_man.is_active():
            self.midi_man.play_notes() # demo test for the synth
            self.msg_app = "Test Synth Engine"
        else:
            self.msg_app = "No Synth Engine is available."
        # """

        self.notify(self.msg_app)

    #------------------------------------------------------------------------------


    def format2bar(self, nb_tick=-1):
        """
        convert tick to bar
        from InterfaceApp object
        """
        
        # current position
        if nb_tick == -1: nb_tick = self.player.get_position()
        (nb_bar, nb_beat, nb_tick) = self.curseq.base.tick2bar(nb_tick)
        nb_bar +=1 # for user friendly
        nb_beat +=1
        # nb_ticks +=1
        bar = "{}:{:02d}:{:03d}".format(nb_bar, nb_beat, nb_tick)
        
        return bar
    
    #-------------------------------------------

    def format2beat(self, nb_tick=-1):
        """
        Format tick to beat
        from InterfaceApp object
        """
        
        # current position
        if nb_tick == -1: nb_tick = self.player.get_position()
        beat = self.curseq.base.tick2beat(nb_tick)
        beat +=1
        msg = f"{beat}"
        
        return msg
    
    #-------------------------------------------

    def format2time(self, nb_tick=-1):
        """
        convert tick to time
        from InterfaceApp object
        """
        
        # current position
        if nb_tick == -1: nb_tick = self.player.get_position()
        sec = self.curseq.base.tick2sec(nb_tick)
        msg = f"{sec:.3f}"
        
        return msg
    
    #-------------------------------------------

    def new_player(self, *args, **kwargs):
        """
        create new player
        from InterfaceApp
        """

        if not self.player: return
        self.player.new_player()
        self.msg_app = "New Player is Created"
        self.notify(self.msg_app)

    #-------------------------------------------

    def autoplay(self, filename=None, *args, **kwargs):
        """
        Play automatically midi file
        from InterfaceApp object
        """
        
        if filename:
            self.player.open_midi_file(filename)
            self.player.play()

    #-------------------------------------------

    def play_pause(self, *args, **kwargs):
        """ 
        play from Interface App 
        """
        
        if not self.player.is_playing():
            self.player.play()
            self.msg_app = f"Play"
        else:
            self.player.pause()
            (nb_bars, nb_beats, nb_ticks) = self.player.get_bar()
            self.msg_app = "Pause at bar: {}:{}:{}".format(nb_bars, nb_beats, nb_ticks)
        
        self.notify(self.msg_app)
    #------------------------------------------------------------------------------

    def stop(self, *args, **kwargs):
        """
        stop from Interface App object
        """

        self.player.stop()
        (nb_bars, nb_beats, nb_ticks) = self.player.get_bar()
        self.msg_app = "Stop at bar: {}:{}:{}".format(nb_bars, nb_beats, nb_ticks)
        self.notify(self.msg_app)

    #-------------------------------------------

    def toggle_record(self, *args, **kwargs):
        """
        toggle record 
        from Interface App object
        """

        if not self.player.is_recording():
            self.player.start_record()
            self.msg_app = "Record"
        else:
            self.player.stop_record()
            self.msg_app = "Stop Record"
        self.notify(self.msg_app)

    #-------------------------------------------

    def goto_start(self, *args, **kwargs):
        """
        goto start
        from Interface App object
        """
        
        pos = self.player.goto_start()
        bar = self.format2bar(-1)
        self.msg_app = "Goto Start at bar: {}".format(bar)
        self.notify(self.msg_app)
    #------------------------------------------------------------------------------

    def goto_end(self, *args, **kwargs):
        """
        goto end
        from Interface App object
        """
        
        self.player.goto_end()
        bar = self.format2bar(-1)
        self.msg_app = "Goto End at bar: {}".format(bar)
        self.notify(self.msg_app)

    #------------------------------------------------------------------------------

    def goto_bar(self, num=None, *args, **kwargs):
        """
        goto bar number
        from Interface App object
        """
        
        # temporary take only the bar number
        if num is None: pos = self.player.get_position()
        else:
            try:
                num = int(num)
            except ValueError:
                num =0
            if num >0: num -=1 # for friendly formatting 
            self.player.goto_bar(num)

        bar = self.format2bar(-1)
        self.msg_app = "Bar at: {}".format(bar)
        self.notify(self.msg_app)

    #------------------------------------------------------------------------------

    def goto_time(self, num=None, *args, **kwargs):
        """
        goto sec number
        from Interface App object
        """
        
        # temporary take only seconds number
        if num is None: pos = self.player.get_position()
        else:
            try:
                num = float(num)
            except ValueError:
                num =0
            tick = self.curseq.base.sec2tick(num)
            pos = self.player.set_position(tick)
        
        pos = self.format2time(-1)
        self.msg_app = f"Time at: {pos}"
        self.notify(self.msg_app)

    #------------------------------------------------------------------------------

    def goto_beat(self, pos=None, *args, **kwargs):
        """
        goto beat number
        from Interface App object
        """
        
        if pos is None: pos =-1 # take current position
        else:
            try:
                pos = int(pos)
            except ValueError:
                pos =0
            if pos >0: pos -=1 # temporary, before calculate beat to tick
            pos = self.curseq.base.beat2tick(pos)
            self.player.set_position(pos)
        
        pos = self.format2beat(-1)
        self.msg_app = f"Beat at: {pos}"
        self.notify(self.msg_app)

    #------------------------------------------------------------------------------
      
    def set_position(self, num=None, *args, **kwargs):
        """
        Gets, sets, or goto tick position
        from Interface App object
        """
        
        if num is None: pos = self.player.get_position()
        else:
            try:
                num = int(num)
            except ValueError:
                num =0
            pos = self.player.set_position(num)
        
        self.msg_app = f"Tick At: {pos}"
        self.notify(self.msg_app)

    #------------------------------------------------------------------------------
     
    def rewind(self, step=1, *args, **kwargs):
        """
        rewind to previous bar
        from InterfaceApp object
        """

        self.player.rewind(step)
        bar = self.format2bar(-1)
        self.msg_app = "Bar: {}".format(bar)
        self.notify(self.msg_app)

    #-------------------------------------------

    def forward(self, step=1, *args, **kwargs):
        """
        next bar
        from Interface App object
        """

        self.player.forward(step)
        bar = self.format2bar(-1)
        self.msg_app = "Bar: {}".format(bar)
        self.notify(self.msg_app)

    #-------------------------------------------

    def set_left_locator(self, *args, **kwargs):
        """
        set left locator
        from Interface App object
        """

        pos = self.player.get_position()
        self.curseq.set_left_locator(pos)
        bar = self.format2bar(-1)
        self.msg_app = "Set Left Locator at bar: {}".format(bar)
        self.notify(self.msg_app)

    #-------------------------------------------

    def set_right_locator(self, *args, **kwargs):
        """
        set right locator
        from Interface App object
        """

        pos = self.player.get_position()
        self.curseq.set_right_locator(pos)
        bar = self.format2bar(-1)
        self.msg_app = "Set Right Locator at bar: {}".format(bar)
        self.notify(self.msg_app)

    #-------------------------------------------

    def goto_left_locator(self, *args, **kwargs):
        """
        """

        pos = self.player.goto_left_locator()
        bar = self.format2bar(-1)
        self.msg_app = "Goto Left Locator at bar: {}".format(bar)
        self.notify(self.msg_app)

    #-------------------------------------------

    def goto_right_locator(self, *args, **kwargs):
        """
        """

        pos = self.player.goto_right_locator()
        bar = self.format2bar(-1)
        self.msg_app = "Goto Right Locator at bar: {}".format(bar)
        self.notify(self.msg_app)

    #-------------------------------------------

    def set_start_loop(self, *args, **kwargs):
        """
        """

        pos = self.player.get_position()
        self.curseq.set_start_loop(pos)
        bar = self.format2bar(-1)
        self.msg_app = "Set start loop at bar: {}".format(bar)
        self.notify(self.msg_app)

    #-------------------------------------------

    def set_end_loop(self, *args, **kwargs):
        """
        """

        pos = self.player.get_position()
        self.curseq.set_end_loop(pos)
        bar = self.format2bar(-1)
        self.msg_app = "Set end loop at bar: {}".format(bar)
        self.notify(self.msg_app)

    #-------------------------------------------

    def toggle_loop(self, *args, **kwargs):
        """
        """

        looping = self.curseq.toggle_loop()
        if looping:
            self.msg_app = "Loop On"
        else:
            self.msg_app = "Loop Off"
        self.notify(self.msg_app)

    #-------------------------------------------

    def toggle_click(self, *args, **kwargs):
        """
        """

        if self.player.is_clicking():
            clicking = self.player.stop_click()
        else:
            clicking = self.player.start_click()
        if clicking:
            self.msg_app = "Click On"
        else:
            self.msg_app = "Click Off"
        self.notify(self.msg_app)

    #-------------------------------------------

    def toggle_mute(self, *args, **kwargs):
        """
        toggle mute
        from InterfaceApp object
        """

        muted = self.curseq.toggle_mute()
        tracknum = self.curseq.get_tracknum()
        if muted:
            self.msg_app = "Track {}: Muted".format(tracknum)
        else:
            self.msg_app = "Track {}: unmuted".format(tracknum)
        self.notify(self.msg_app)

    #-------------------------------------------

    def toggle_solo(self, *args, **kwargs):
        """
        toggle solo
        from InterfaceApp object
        """

        soloed = self.curseq.toggle_solo()
        tracknum = self.curseq.get_tracknum()
        if soloed:
            self.msg_app = "Track {}: soloed".format(tracknum)
        else:
            self.msg_app = "Track {}: unsoloed".format(tracknum)
        self.notify(self.msg_app)

    #-------------------------------------------

    def toggle_quantize(self, *args, **kwargs):
        """
        toggle quantize
        from InterfaceApp object
        """

        res = self.curseq.toggle_quantize()
        if res:
            self.msg_app =  "Autoquantize: On"
        else:
            self.msg_app =  "Autoquantize: Off"
        self.notify(self.msg_app)

    #-------------------------------------------

    def quantize(self, *args, **kwargs):
        """
        toggle quantize
        from InterfaceApp object
        """

        self.curseq.quantize_track()
        self.msg_app =  "Quantize to: {}".format(self.player.quan_res)
        self.notify(self.msg_app)

    #-------------------------------------------

    def erase_track(self, tracknum=-1, startpos=0, endpos=0, *args, **kwargs):
        """
        erase events track between time
        from Interface App object
        """

        title = "Erase track"
        if startpos == 0  and endpos == -1:
            (res, tracknum) = self.curseq.erase_track(tracknum, startpos, endpos)
        else:
            (left_loc, right_loc) = self.curseq.get_locators()
            (res, tracknum) = self.curseq.erase_track(tracknum, left_loc, right_loc)
        if res:
            self.make_undo(title)
            self.msg_app = "Erase track {}: ".format(tracknum)
        else:
            self.msg_app = "Track {}: not erased".format(tracknum)
        self.notify(self.msg_app)

    #-------------------------------------------

    def delete_track(self, tracknum=-1):
        """
        delete track to track list
        from Interface App object
        """

        title = "Delete track"
        (res, tracknum) = self.curseq.delete_track(tracknum)
        if res:
            self.make_undo(title)
            self.msg_app = "Delete track {}".format(tracknum)
        else:
            self.msg_app = "Track {}: not deleted".format(tracknum)
        self.notify(self.msg_app)

    #-------------------------------------------

    def arm_track(self, tracknum=-1, armed=0):
        """
        arm or desarm track
        from Interface App object
        """

        (tracknum, armed) = self.curseq.arm(tracknum, armed)
        if armed:
            self.msg_app = "Track {}: Armed".format(tracknum)
        else:
            self.msg_app = "Track {}: Desarmed".format(tracknum)
        self.notify(self.msg_app)

    #-------------------------------------------

    def get_bar(self, *args, **kwargs):
        """
        display the position in bar
        from Interface App object
        """
        
        # getting current position
        bar = self.format2bar(-1)
        self.msg_app = f"Bar: {bar}"
        self.notify(self.msg_app)

    #-------------------------------------------


    def print_status(self, *args, **kwargs):
        """
        display the status bar
        from Interface App object
        """
        
        # getting current position
        curbar = self.format2bar(-1)
        lastpos = self.player.get_length()
        lastbar =  self.format2bar(lastpos)
        start_loop = self.curseq.get_start_loop()
        start_loop = self.format2bar(start_loop)
        end_loop = self.curseq.get_end_loop()
        end_loop = self.format2bar(end_loop)
        bpm = self.curseq.get_bpm()
        self.msg_app = "Bar Position: {} / {}, start_loop: {}, end_loop: {},\
                Bpm: {:.2f}".format(curbar, lastbar, start_loop, end_loop, bpm)
        self.notify(self.msg_app)

    #-------------------------------------------

    def print_info(self, param1=None, *args, **kwargs):
        """
        display midi file information
        from Interface App object
        """

        if param1 is None:
            self.msg_app = self.curseq.get_properties()
        elif param1 == "bpm":
            bpm = self.curseq.get_bpm()
            self.msg_app = f"Bpm: {bpm:.2f}"

        self.notify(self.msg_app)
    
    #-------------------------------------------
    
    def print_midi_ports(self):
        """
        prints Midi Ports
        from InterfaceApp object
        """

        if self.midi_man:
            self.midi_man.print_ports()

    #-------------------------------------------

    def make_undo(self, title):
        """
        create a player copy
        from Interface App object
        """

        player = None        
        player = self.tools.duplicate_player_obj(self.player)
        if player:
            self.undoman.add_undo(title, player)

        return player
    
    #-------------------------------------------

    def undo(self):
        """
        Undo track
        from InterfaceApp object
        """
        
        curtitle = self.undoman.title
        (title, player) = self.undoman.prev_undo()
        if player:
            # copy player to not modify the saved
            new_player = self.tools.duplicate_player_obj(player)
            self.player = new_player
            self.player.update_player()
            self.curseq = self.player.curseq
            # self.curseq.update_length()
            # debug("voici player tracks: {}".format(len(track_lst)))
            self.msg_app = "Undo {}".format(curtitle)
        else:
            self.msg_app = "No Undo available"
        self.notify(self.msg_app)

    #-------------------------------------------

    def redo(self):
        """
        redo track
        from Interface App object
        """

        (title, player) = self.undoman.next_undo()
        if player:
            # copy player to not modify the saved
            new_player = self.tools.duplicate_player_obj(player)
            self.player = new_player
            self.player.update_player()
            self.curseq = self.player.curseq
            # self.curseq.update_length()
            self.msg_app = "Redo {}".format(title)
        else:
            self.msg_app = "No Redo available"
        self.notify(self.msg_app)

    #-------------------------------------------

    def delete_event(self):
        """
        delete events
        from Interface App object
        """

        self.player.delete_event(evobj=None)
        self.msg_app = "Delete events"
        self.notify(self.msg_app)

    
    #-------------------------------------------

    def panic(self, *args, **kwargs):
        """
        Set panic
        from Interface App object
        """

        if self.player:
            self.player.midi_man.panic()
            self.msg_app = "Panic"
            self.notify(self.msg_app)
    
    #-------------------------------------------

    def reset(self, *args, **kwargs):
        """
        Reset the Synths
        from Interface App object
        """

        if self.midi_man and self.midi_man.is_active():
            self.midi_man.reset()
            self.msg_app = "Reset..."
        else:
            self.msg_app = "No Synth Engine is available."

        self.notify(self.msg_app)
    
    #-------------------------------------------

    def open_file(self, filename, *args, **kwargs):
        """
        open midi file 
        from InterfaceApp object
        """

        if filename: filename = str(filename)
        else: return
        if os.path.exists(filename):
            if self.player.open_midi_file(filename):
                self.undoman.init()
                msg = "Init player"
                self.make_undo(msg)
                self.msg_app = "File name: {} imported".format(filename)
            else: # no midi data
                self.msg_app  = "Error: No midi data"
        else: # no file
            self.msg_app = f"Error: File not found: {filename}"
        self.notify(self.msg_app)
     
     #-------------------------------------------

    def save_file(self, filename):
        """
        save midi file
        from InterfaceApp object
        """
        
        # if os.path.isfile(filename):
        if filename:
            res = self.curseq.save_midi_file(filename)
            if res:
                self.msg_app = "File name: {} saved".format(filename)
            else: # file not saved
                self.msg_app = "File not saved"
        else: # not a file
            self.msg_app = "{} is not a file".format(filename)
        self.notify(self.msg_app)
    
    #-------------------------------------------
 
    def change_bpm(self, bpm=None, *args, **kwargs):
        """
        change the bpm
        from InterfaceApp object
        """

        if bpm is None: 
            bpm = self.curseq.get_bpm()
            self.msg_app = f"Bpm: {bpm:.2f}"
        else:
            try:
                bpm = float(bpm)
            except ValueError:
                return
            self.player.change_bpm(bpm)
            self.msg_app = f"Change Bpm: {bpm:.2f}"
        self.notify(self.msg_app)

    #-------------------------------------------

    def quantize_track(self, type, tracknum, reso):
        """
        quantize track
        from InterfaceApp object
        """
        
        self.msg_app = "Quantize: {}".format(reso)
        self.notify(self.msg_app)
        self.player.quantize_track(type, tracknum, reso)

    #-------------------------------------------

    def change_window(self, num):
        """ 
        change window number
        from Interface object
        """
        
        self.window_num = num
        if self.window_num == 0:
            self.msg_app = "Track Window"
        elif self.window_num == 1:
            self.curseq.init_event_task()
            self.msg_app = "Event list Window"
        self.notify(self.msg_app)

    #-------------------------------------------

    def change_one_ev(self, step=0, adding=0):
        """
        change event in event list window
        from InterfaceApp object
        """
        
        # calling get_playable_ev
        self.msg_app = ""
        evobj = self.curseq.select_one_ev(step, adding)
        if evobj is not None:
            try:
                self.curseq.group_ev.play_ev(evobj)
                self.msg_app = evobj.desc
            except:
                pass
        else:
            self.msg_app = "No event"
        self.notify(self.msg_app)

    #-------------------------------------------

    def play_one_ev(self):
        """
        play event
        from Interface App object
        """

        self.curseq.group_ev.play_ev(evobj=None)
    #-------------------------------------------

    def change_note_group(self, step=0, adding=0, timing=0):
        """
        change notes list window
        -- timing: to play simultaneously notes or not.
        from InterfaceApp object
        """
        
        self.msg_app = ""
        ev_lst = self.curseq.select_note_group(step, adding)
        if ev_lst:
            self.curseq.group_ev.play_note_group(ev_lst, timing)
        else:
            self.msg_app = "No event group"
        self.notify(self.msg_app)

    #-------------------------------------------

    def play_note_group(self, timing=0):
        """
        play event
        from Interface App object
        """

        self.curseq.group_ev.play_note_group(timing=timing)

#-------------------------------------------

    def filter_notes(tracknum, start_note, end_note):
        """
        filter notes range in event list
        from InterfaceApp object
        """
        
        self.msg_app = "Filter Notes"
        self.notify(self.msg_app)
        self.curseq.filter_notes(tracknum, start_note, end_note)

    #-------------------------------------------

    def move_notes(self, tracknum, start_note, end_note):
        """
        move notes
        move notes range in event list on a new track
        Note: Temporary function
        from InterfaceApp object
        """

        self.msg_app = "Move Notes"
        self.notify(self.msg_app)
        tracknum =-1; start_note = "C5"; end_note = "C8"
        self.curseq.move_notes(tracknum, start_note, end_note)
    
    #-------------------------------------------
    
       
    def change_tracknum(self, step=0, adding=0):
        """
        changing track number from the sequencer
        from InterfaceApp object
        """

        tracknum = self.curseq.change_tracknum(step, adding)
        track = self.curseq.get_track(tracknum)
        track_name = track.track_name
        instrument_name = track.instrument_name
        if track_name:
            self.msg_app = "{}: {} - {}".format(tracknum, track_name, instrument_name)
        else:
            self.msg_app = "{}: Track {}".format(tracknum, tracknum)
        
        self.notify(self.msg_app)
        
    #-------------------------------------------

    def change_channel(self, step=0, adding=0):
        """
        changing channel object list
        """

        track = self.curseq.get_track()
        chan_num = track.select_channel(step, adding)
        # print(f"voici chan_num: {chan_num}")
        self.msg_app  = "Channel : {}".format(chan_num+1)
        self.notify(self.msg_app)
       
        return self.msg_app
    #-------------------------------------------

    def change_bank(self, step=0, adding=0):
        """
        changing bank object list
        from InterfaceApp
        """

        track = self.curseq.get_track()
        # returns formated message
        self.msg_app = track.select_bank(step, adding)
        self.notify(self.msg_app)

    #-------------------------------------------

    def change_preset(self, step=0, adding=0):
        """
        changing preset object list
        from InterfaceApp
        """

        track = self.curseq.get_track()
        # returns formated message
        self.msg_app = track.select_preset(step, adding)
        self.notify(self.msg_app)

    #-------------------------------------------

    def change_patch(self, step=0, adding=0):
        """
        changing patch object list
        from InterfaceApp
        """

        track = self.curseq.get_track()
        # returns formated message
        self.msg_app = track.select_patch(step, adding)
        self.notify(self.msg_app)

    #-------------------------------------------
    
    def change_midi_in(self, port_num=None, *args, **kwargs):
        """
        changing Midi Out Port
        from InterfaceApp
        """

        if not self.midi_man: return

        if port_num is None:
            (num, name) = self.midi_man.get_inport_id()
            self.msg_app = f"Midi In Port num: {num}, name: {name}"
        else:
            try:
                port_num = int(port_num)
                self.midi_man.open_input(port_num)
                (num, name) = self.midi_man.get_inport_id()
                self.msg_app = f"Midi In Port num: {num}, name: {name}"
            except ValueError:
                pass

        self.notify(self.msg_app)

    #-------------------------------------------

    def change_midi_out(self, port_num=None, *args, **kwargs):
        """
        changing Midi Out Port
        from InterfaceApp
        """

        if not self.midi_man: return

        if port_num is None:
            (num, name) = self.midi_man.get_outport_id()
            self.msg_app = f"Midi Out Port num: {num}, name: {name}"
        else:
            try:
                port_num = int(port_num)
                self.midi_man.open_output(port_num)
                (num, name) = self.midi_man.get_outport_id()
                self.msg_app = f"Midi Out Port num: {num}, name: {name}"
            except ValueError:
                pass

        self.notify(self.msg_app)

    #-------------------------------------------

    def change_synth(self, synth_type=None, outport_num=None, audio_out=None, *args, **kwargs):
        """
        changing Synth type
        from InterfaceApp
        """

        initing =0
        if not self.midi_man: return
        if synth_type is not None:
            try:
                synth_type = int(synth_type)
                initing =1
            except ValueError:
                synth_type = None

        if outport_num is not None: 
            try:
                outport_num = int(outport_num)
            except ValueError:
                outport_num = None
        if not initing:
            # getting only Synth values
            (synth_type, outport_num, audio_out) = self.midi_man.get_synth_id()
            self.msg_app = f"Synth State, type: {synth_type}, Midi Out Port: {outport_num}, Audio Output: {audio_out}"
        else:
            self.midi_man.init_midi(synth_type=synth_type, outport_num=outport_num, audio_out=audio_out)
            (synth_type, outport_num, audio_out) = self.midi_man.get_synth_id()
            self.msg_app = f"Init Synth, type: {synth_type}, Midi Out Port: {outport_num}, Audio Output: {audio_out}"
        
        self.notify(self.msg_app)

    #-------------------------------------------

    def change_midi_engine(self, param=None, *args, **kwargs):
        """
        Change the midi engine
        from Interfaceapp object
        """
        
        if param == "on":
            self.player.start_midi_engine()
        elif param == "off":
            self.player.stop_midi_engine()
        
        if self.player.is_running():
            self.msg_app = f"Midi Engine is Running"
        else:
            self.msg_app = f"Midi Engine is Stopped"
        
        self.notify(self.msg_app)


    #-------------------------------------------


    def add_track_selection(self, tracknum):
        """
        adding track index to the tracks selection
        from InterfaceApp object
        """

        (res, tracknum) = self.select.add_track_selection(tracknum)
        if res:
            self.select.select_all_time()
            msg = "Add track selection: {}".format(tracknum)
        else:
            msg = "No track selection added"
        self.msg_app = msg
        self.notify(self.msg_app)

    #-------------------------------------------

    def del_track_selection(self, tracknum):
        """
        delete track number to the tracks selection
        from InterfaceApp object
        """

        (res, tracknum) = self.select.del_track_selection(tracknum)
        if res:
            msg = "Delete track selection: {}".format(tracknum)
        else:
            msg = "No track selection deleted"
        self.msg_app = msg
        self.notify(self.msg_app)

    #-------------------------------------------

    def select_cur_track(self):
        """
        select current track
        from InterfaceApp object
        """

        if self.select.select_cur_track():
            self.select.select_all_time()
            tracknum = self.curseq.get_tracknum()
            msg = "Select current track: {}".format(tracknum)
        else:
            msg = "No track selected"
        self.msg_app = msg
        self.notify(self.msg_app)
 
    #-------------------------------------------

    def unselect_cur_track(self):
        """
        unselect current track
        from InterfaceApp object
        """

        if self.select.unselect_cur_track():
            tracknum = self.curseq.get_tracknum()
            msg = "Unselect current track: {}".format(tracknum)
        else:
            msg = "No track unselected"
        self.msg_app = msg
        self.notify(self.msg_app)
            
    #-------------------------------------------

    def select_all_tracks(self):
        """
        select all tracks
        from InterfaceApp object
        """

        if self.select.select_all_tracks():
            self.select.select_all_time()
            msg = "Select all tracks"
        else:
            msg = "No track selected"
        self.msg_app = msg
        self.notify(self.msg_app)
    
    #-------------------------------------------

    def unselect_all_tracks(self):
        """
        unselect all tracks
        from InterfaceApp object
        """

        if self.select.unselect_all_tracks():
            msg = "Unselect all tracks"
        else:
            msg = "No track unselected"
        self.msg_app = msg
        self.notify(self.msg_app)

    #-------------------------------------------

    def select_time(self, start_pos, end_pos=-1):
        """
        select time from start_pos to end_pos, 
        from InterfaceApp object 
        """

        self.select.select_time(start_pos, end_pos)
        
    #-------------------------------------------

    
    def select_all_time(self):
        """
        select all time 
        from InterfaceApp object 
        """
        
        self.select.select_all_time()

    #-------------------------------------------

    def copy_to_clip(self):
        """
        copy to clipboard
        from InterfaceApp object
        """
        
        tracks_sel = self.select.get_tracks_selection()
        # tracknum = self.curseq.get_tracknum()
        if not tracks_sel:
            msg = "No track selected"
        else:
            (l_loc, r_loc) = self.curseq.get_locators()
            self.clip.copy_to_clip(tracks_sel, l_loc, r_loc)
            l_loc = self.format2bar(l_loc)
            r_loc = self.format2bar(r_loc)
            msg = "Copying tracks from {}, to {}".format(l_loc, r_loc)
        self.msg_app = msg
        self.notify(self.msg_app)

    #-------------------------------------------
         
    def cut_to_clip(self):
        """
        cut to clipboard
        from InterfaceApp object
        """
        
        tracks_sel = self.select.get_tracks_selection()
        # tracknum = self.curseq.get_tracknum()
        if not tracks_sel:
            msg = "No track selected"
        else:
            (l_loc, r_loc) = self.curseq.get_locators()
            self.clip.cut_to_clip(tracks_sel, l_loc, r_loc)
            title = "Cut tracks"
            self.make_undo(title)
            l_loc = self.format2bar(l_loc)
            r_loc = self.format2bar(r_loc)
            msg = "Cutting tracks from {}, to {}".format(l_loc, r_loc)
        self.msg_app = msg
        self.notify(self.msg_app)

    #-------------------------------------------
     
    def erase_to_clip(self):
        """
        erase to clipboard
        from InterfaceApp object
        """
        
        tracks_sel = self.select.get_tracks_selection()
        if not tracks_sel:
            msg = "No track selected"
        else:
            (l_loc, r_loc) = self.curseq.get_locators()
            self.clip.erase_to_clip(tracks_sel, l_loc, r_loc)
            title = "Erase tracks"
            self.make_undo(title)
            l_loc = self.format2bar(l_loc)
            r_loc = self.format2bar(r_loc)
            msg = "Erasing track from {}, to {}".format(l_loc, r_loc)
        self.msg_app = msg
        self.notify(self.msg_app)

    #-------------------------------------------
    
    def paste_replace(self):
        """
        paste replace from clipboard
        from InterfaceApp object
        """
        
        pos = self.curseq.get_position()
        self.clip.paste_replace(pos)
        title = "Paste replace tracks"
        self.make_undo(title)
        pos = self.format2bar(pos)
        msg = "Paste replace tracks at  {}".format(pos)
        self.msg_app = msg
        self.notify(self.msg_app)

    #-------------------------------------------
     
    def paste_merge(self):
        """
        paste merge from clipboard
        from InterfaceApp object
        """
        
        pos = self.curseq.get_position()
        self.clip.paste_merge(pos)
        title = "Paste merge tracks"
        self.make_undo(title)
        pos = self.format2bar(pos)
        msg = "Paste merge tracks at  {}".format(pos)
        self.msg_app = msg
        self.notify(self.msg_app)

    #-------------------------------------------
    
    def log_info(self, type=0):
        """
        logging midi informations
        from InterfaceApp object
        """

        self.player.log_info(type)
        msg = "Logging info"
        self.msg_app = msg
        self.notify(self.msg_app)
    
    #-------------------------------------------

    def test(self):
        """
        test function
        from InterfaceApp object
        """
        
        self.msg_app = "Test from InterfaceApp"
        self.notify(self.msg_app)
      
        """
        ev_lst = self.curseq.get_note_group(-1, 1)
        if ev_lst:
            self.curseq.play_note_group(ev_lst)
        else:
            self.msg_app = "No event group"
        self.notify(self.msg_app)
        """


        """
        tracknum = self.curseq.tracknum
        track = self.curseq.get_track(tracknum)
        self.msg_app =f"voici1 tracknum, pos, count: {tracknum, track.pos, track.count()}"
        # ev = track.next_ev()
        ev = track.get_ev()
        msg1 = f"type: {ev.msg.type}"
        self.msg_app =f"voici2 tracknum, pos, count: {tracknum, track.pos, msg1, track.count()}, msg.time: {ev.msg.time}"
        # ev = track.next_ev()
        """

        
        """
        # getting notes list
        note_lst = self.player.get_notes(tracknum)
        for note in note_lst:
            uti.debug("voici track: {}, note_on: {}, note_off: {}".format(note[0], note[1], note[2]))
        """


    #------------------------------------------------------------------------------

#========================================
if __name__ == "__main__":
    app = InterfaceApp(None)
    app.init_app()
    input("It's OK...")

#------------------------------------------------------------------------------
