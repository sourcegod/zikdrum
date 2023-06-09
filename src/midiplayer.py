#!/usr/bin/python3
"""
    File: midiplayer.py:
    Module for playing midi events 
    Date: Mon, 04/07/2022
    Author: Coolbrother
"""
import time
import threading
import fluidsynth
import mido
import miditools as midto
import constants as cst

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

class CFileInfo(object):
    """ midi file information """
    filename = ""
    format =0
    nbtracks =0
    ppq =0
    track_info = []
    bpm =0
    time_per_beat =0 # in microsec
    time_per_tick =0 # in microsec
    info_lst = []

#========================================

class CChannel(object):
    """ Channel parameters """
    def __init__(self):
        self.chan =0
        self.patch =0
        self.bank =0
        self.msb_preset =0
        self.lsb_preset =0

    #-------------------------------------------

#========================================

class MidiEvent(object):
    """ Midi event structure """
    def __init__(self, type='note_on', cat=0):
        self.id =0
        if cat == 0: # category message
            self.msg = mido.Message(type)
        elif cat == 1: # metamessage category
            self.msg = mido.MetaMessage(type)

        self.tracknum =0
    
    #-----------------------------------------

#========================================

class EventObj(object):
    """ container for event """
    def __init__(self):
        self.index1 =0
        self.ev1 = None
        self.index2 =0 # for note_off
        self.ev2 = None # for note_off
        self.length =0 # for duration between note_off and note_on
        self.desc = ""

    #-----------------------------------------

#========================================

class MidiChannel(object):
    """ Midi channel manager """
    def __init__(self, type='note_on'):
        # self.midi_man = None
        self.channel_num =0 # for channel 1
        self.channel_lst = [] # contener for channel object
        self.patch_num =0
        self.volume =0

        self.menu_names = [
                    'Channel',
                    'Bank', 'Preset',
                    'Patch',
                    ]
        self.bank_lst = ["0 (MSB)", "32 (LSB)"]
        self.bank_num =0
        self.preset_lst = range(128)
        self.msb_preset_num =0
        self.lsb_preset_num =0
        self.bank_select_num =0 # result of: (msb_preset_num + msb_preset_num*128)
        self.bank_select_lst = [0, 128] # bank select allowed
        self.preset_modified =0
        self.new_patch_lst = range(128) # empty patch

    #-----------------------------------------

    def set_channels(self):
        """
        set channel list
        from MidiChannel object
        """
        
        self.channel_lst = []
        for i in range(16):
            ch = CChannel()
            ch.chan = i
            self.channel_lst.append(ch)

    #-------------------------------------------

    def change_item(self, item_num, item_lst, step=0, adding=0, min_val=0, max_val=-1):
        """
        changing item generic
        from MidiChannel object
        """

        changing =0
        val =0
        if max_val == -1:
            max_val = len(item_lst) -1
        if adding == 0:
            if step == -1:
                step = max_val
        else: # adding value
            val = item_num + step
            changing =1
        if changing:
            step = limit_value(val, min_val, max_val)
        if item_num != step:
            item_num = step
        else: # no change for item num
            # beep()
            pass
        
        return item_num

    #-------------------------------------------

    def change_channel(self, chan_num, step=0, adding=0):
        """
        changing channel object list
        from MidiChannel object
        """

        changing =0
        val =0
        max_val = len(self.channel_lst) -1
        if adding == 0:
            if step == -1:
                step = max_val
        else: # adding value
            val = chan_num + step
            changing =1
        if changing:
            step = limit_value(val, 0, max_val)
        if chan_num != step:
            chan_num = step
        else: # no change for chan num
            beep()
        
        return chan_num
    
    #-------------------------------------------

    def select_channel(self, step=0, adding=0):
        """
        select channel item by index
        from MidiChannel object
        """
        
        self.channel_num = self.change_channel(self.channel_num, step, adding)
        channel_obj = self.channel_lst[self.channel_num]
        chan_num = channel_obj.chan
        patch_num = channel_obj.patch
        self.channel_num = chan_num
        self.patch_num = patch_num
        self.midi_man.program_change(chan_num, patch_num)

        return chan_num

    #-------------------------------------------
    
    def select_bank(self, step=0, adding=0):
        """
        select bank type
        from MidiChannel object
        """

        channel_obj = self.channel_lst[self.channel_num]
        chan_num = channel_obj.chan
        bank_num = channel_obj.bank
        bank_num = self.change_item(bank_num, self.bank_lst, step, adding)
        channel_obj.bank = bank_num
        self.bank_num = bank_num
        try: 
            msg = "{}".format(self.bank_lst[self.bank_num])
        except IndexError:
            msg = "0"

        return msg

    #-------------------------------------------

    def select_preset(self, step=0, adding=0):
        """
        select bank preset
        from MidiChannel object
        """

        preset_num =0
        channel_obj = self.channel_lst[self.channel_num]
        chan_num = channel_obj.chan
        bank_num = channel_obj.bank
        msb_num = channel_obj.msb_preset
        lsb_num = channel_obj.lsb_preset
        if bank_num == 0: # msb type
            preset_num = msb_num
            preset_num = self.change_item(preset_num, self.preset_lst, step, adding)
            channel_obj.msb_preset = preset_num
            self.msb_preset_num = preset_num
        elif bank_num == 1: # lsb type
            preset_num = lsb_num
            preset_num = self.change_item(preset_num, self.preset_lst, step, adding)
            channel_obj.lsb_preset = preset_num
            self.lsb_preset_num = preset_num

        self.preset_modified =1
        self.bank_select_num = (self.msb_preset_num + (self.lsb_preset_num * 128))
        msg = "{}".format(self.preset_lst[preset_num])

        return msg

    #-------------------------------------------

    def select_patch(self, step=0, adding=0):
        """
        select patch menu by index
        from MidiChannel object
        """
        
        channel_obj = self.channel_lst[self.channel_num]
        chan_num = channel_obj.chan
        patch_num = channel_obj.patch
        if self.bank_select_num == 0: # GM patch
            patch_lst = cst._gm_patch_lst
        elif self.bank_select_num == 128: # GM2 drumkit set
            patch_lst = cst._gm2_drumkit
        else:
            patch_lst = self.new_patch_lst
        patch_num = self.change_item(patch_num, patch_lst, step, adding)
        channel_obj.patch = patch_num
        self.patch_num = patch_num
        if self.preset_modified and\
            self.bank_select_num in self.bank_select_lst:
            # change bank number before sending patch
            self.midi_man.bank_change(chan_num, self.bank_select_num)
            self.preset_modified =0
        
        self.midi_man.program_change(chan_num, patch_num)
        # debug("voici :  chan_num: {} --- patch_num: {}".format(chan_num, patch_num))
        # print("voici: -- ",chan_num,patch_num)
        msg = "{} - {}".format(patch_num, patch_lst[patch_num])

        return msg

    #-------------------------------------------

#========================================

class MidiTrack(MidiChannel):
    """
    track manager """
    def __init__(self):
        super().__init__()
        self.ev_lst = []
        self.group_lst = []
        self.group_index =0
        self.ev_grouping =0
        self.active =0
        self.pos =0
        self.lastpos =-1
        self.lasttime =-1
        self.repeating =0
        self.repeat_count =0
        self.muted =0
        self.sysmuted =0
        self.soloed =0
        self.armed =0
        self.track_name = ""
        self.instrument_name = ""
        self.set_channels()
        self.midi_man = None

    #-----------------------------------------

    def init(self, lst=[]):
        """
        init event list
        from Mtrack object
        """
        
        self.ev_lst[:] = lst

    #-----------------------------------------

    def get_length(self):
        """
        returns track length
        from MTrack object
        """
        
        val =0
        if self.ev_lst:
            ev = self.ev_lst[-1]
            val = ev.msg.time
        
        return val

    #-----------------------------------------

    def count(self):
        """
        returns event count
        from MTrack object
        """

        return len(self.ev_lst)

    #-----------------------------------------

    def append(self, ev):
        """
        adding event
        from MTrack object
        """

        if ev:
            self.ev_lst.append(ev)
    
    #-----------------------------------------

    def add_evs(self, *ev_lst):
        """
        adding events
        from MidiTrack object
        """

        if ev_lst:
            self.ev_lst.extend(ev_lst)
    
    #-----------------------------------------
    
    def insert(self, index=0, ev=None):
        """
        insert event at index
        from MidiTrack object
        """

        if ev:
            self.ev_lst.insert(index, ev)
    
    #-----------------------------------------

    def insert_evs(self, index=0, ev_lst=[]):
        """
        insert event list at index
        from MidiTrack object
        """

        if ev_lst:
            try:
                self.ev_lst[index:index] = ev_lst
            except IndexError:
                pass
    
    #-----------------------------------------

    def get_list(self):
        """
        returns ev list
        from MidiTrack object
        """

        return self.ev_lst

    #-----------------------------------------

    def get_ev(self, index=-1):
        """
        returns event
        from MTrack object
        """

        res = None
        pos =0
        if index == -1:
            pos = self.pos
        elif index >=0:
            pos = index
        try:
            res = self.ev_lst[pos]
        except IndexError:
            pass

        return res

    #-----------------------------------------

    def set_ev(self, val):
        """
        set current event and position
        from MTrack object
        """

        res = None
        for (i, ev) in enumerate(self.ev_lst):
            if ev.msg.time >= val:
                self.pos = i
                res = ev.msg.time
                break

        return res

    #-----------------------------------------

    def prev_ev(self):
        """
        set prev event
        from MTrack object
        """

        res = None
        if self.pos >0:
            self.pos -=1
            try:
                res = self.ev_lst[self.pos]
            except IndexError:
                pass

        return res

    #-----------------------------------------

    def next_ev(self):
        """
        set next event
        from MTrack object
        """

        res = None
        if self.pos < len(self.ev_lst):
            self.pos +=1
            try:
                res = self.ev_lst[self.pos]
            except IndexError:
                pass
        elif self.pos >= len(self.ev_lst):
            if self.repeating:
                self.pos =0
                self.repeat_count +=1
                self.lastpos =-1
                try:
                    res = self.ev_lst[self.pos]
                    # debug("repeat count: {}".format(self.repeat_count))
                except IndexError:
                    pass
            else:
                self.pos = len(self.ev_lst)
                # self.lastpos =-1

        return res

    #-----------------------------------------

    def search_ev_group(self, time):
        """
        returns event list <= time
        from MTrack object
        """

        lst = []
        
        if self.pos < len(self.ev_lst):
            while 1:
                ev = self.get_ev()
                if ev is not None:
                    msg = ev.msg
                    if msg.time >= self.lastpos and msg.time <= time:
                        # debug("voici ev: {}".format(ev))
                        # debug("pos: {}".format(self.pos))
                        lst.append(ev)
                        self.group_index +=1
                        self.ev_grouping =1
                        self.lasttime = msg.time
                        self.next_ev()
                    else: # msg > time
                        break
                else: # ev is None
                    self.ev_grouping =0
                    break
        
        # debug(f"voici len lst: {len(lst)}")
        return lst

    #-----------------------------------------

    def gen_group_pos(self):
        """
        generate a list of unique index of each group event
        from MidiTrack object
        """

        curtime =-1
        self.group_lst = []
        for (pos, ev) in enumerate(self.ev_lst):
            time = ev.msg.time
            if time != curtime:
                self.group_lst.append(pos)
                curtime = time
        
        return self.group_lst
    
    #-----------------------------------------

    def get_group_pos(self):
        """
        returns ev group index
        from MidiTrack object
        """
        

        res =-1
        try:
            res = self.group_lst[self.group_index]
        except IndexError:
            pass

        return res
    
    #-----------------------------------------

    def set_group_pos(self, pos):
        """
        set the index in the group list position
        from MidiTrack object
        """

        index =-1
        curpos =-1
        # group_lst contain first index of each group event
        if not self.group_lst:
            # debug("c'est ça papa")
            return
        if self.group_lst:
            last_pos = self.group_lst[-1]
            if pos >= last_pos:
                index = last_pos
            else:
                for (ind, group_pos) in enumerate(self.group_lst):
                    if group_pos == pos:
                        index = ind
                        break
                    elif group_pos > pos:
                        index = ind -1
                        break

        if index >= 0:
            self.group_index = index
            try:
                curpos = self.group_lst[self.group_index]
            except IndexError:
                pass

        return curpos
    
    #-----------------------------------------

    def get_group_range(self):
        """
        returns a tuple of start and stop positions for current group event
        from MidiTrack object
        """

        start_ind = -1
        stop_ind = -1
        start_pos =-1
        stop_pos =-1
        maxlen = len(self.group_lst) -1
        if self.group_index == maxlen:
            start_ind = self.group_index
            stop_ind = start_ind
        elif self.group_index >=0 and self.group_index < maxlen:
            start_ind = self.group_index
            stop_ind = start_ind +1
        
        if start_ind >=0:
            start_pos = self.group_lst[start_ind]
            stop_pos = self.group_lst[stop_ind]
        
        return (start_pos, stop_pos)
    
    #-----------------------------------------

    def get_ev_group(self):
        """
        returns current group event
        from MidiTrack object
        """

        res = None    
        (start_pos, stop_pos) = self.get_group_range()
        if start_pos >=0:
            res = self.ev_lst[start_pos:stop_pos]
            # update event position
            self.pos = start_pos
       
        return res

    #-----------------------------------------

    def prev_ev_group(self):
        """
        returns previous group event
        from MidiTrack object
        """

        res = None    
        # update event group position
        if not self.ev_grouping:
            self.update_group_pos(1)
        if self.group_index >0:
            self.group_index -= 1
            res = self.get_ev_group()
      
        return res

    #-----------------------------------------

    def next_ev_group(self):
        """
        returns next group event
        from MidiTrack object
        """

        res = None    
        # update event group position
        if not self.ev_grouping:
            self.update_group_pos(1)
        if self.group_index < len(self.group_lst) -1:
            self.group_index += 1
            res = self.get_ev_group()

  
        return res

    #-----------------------------------------

    def get_group_count(self):
        """
        returns length of group list
        from MidiTrack object
        """
 
        return len(self.group_lst)

    #-----------------------------------------

    def init_group_pos(self):
        """
        Update the event group index position
        from MidiTrack object
        """
        
        self.ev_grouping =0
        self.group_index = self.pos

    #-----------------------------------------


    def sort(self):
        """
        sort events list
        from MidiTrack object
        """

        self.ev_lst.sort(key=lambda x: x.msg.time)

    #-----------------------------------------

    def get_pos(self):
        """
        returns position in event list
        from Mtrack object
        """
        
        return self.pos
    
    #-----------------------------------------

    def set_pos(self, pos):
        """
        set position in event list
        from Mtrack object
        """
        
        ev_len = len(self.ev_lst)
        if pos == -1:
            self.pos = ev_len -1
        elif pos >=0 and pos < ev_len:
            self.pos = pos
        # update event group position
        if self.ev_grouping:
            self.update_group_pos(0)
    
    #-----------------------------------------
    
    def update_group_pos(self, grouping=0):
        """
        update ev group position
        from MidiTrack object
        """

        self.set_group_pos(self.pos)    
        self.ev_grouping = grouping
    
    #-----------------------------------------

    def search_pos(self, time):
        """
        search index of time position in list
        from MidiTrack object
        """

        index =0
        for (i, ev) in enumerate(self.ev_lst):
            msg = ev.msg
            if msg.time >= time:
                index = i
                break
        
        return index

    #-----------------------------------------

    def search_lastpos(self, time):
        """
        search last index of time position in list
        from MidiTrack object
        """

        index =0
        for (i, ev) in enumerate(self.ev_lst):
            msg = ev.msg
            if msg.time == time:
                index = i
            elif msg.time > time:
                index = i
                break
        
        return index

    #-----------------------------------------

    def search_ev(self, type, time):
        """
        search event by type, and time position in list
        returns event object
        from MidiTrack object
        """

        res = None
        for (i, ev) in enumerate(self.ev_lst):
            msg = ev.msg
            if msg.type == type and msg.time >= time:
                res = ev
                break
        
        return res

    #-----------------------------------------
     
    def is_active(self):
        """
        returns active state of the track
        from MidiTrack object
        """

        return self.active

    #-----------------------------------------

    def set_active(self, active):
        """ 
        set active state for this track
        from Track object
        """

        self.active = active

    #-----------------------------------------

    def is_muted(self):
        return self.muted
    
    #-----------------------------------------
 
    def set_muted(self, muted=0, chan=0):
        """
        set track mute
        from MidiTrack object
        """

        if muted:
            self.midi_man.panic(chan)
        self.muted = muted

    #-----------------------------------------
   
    def is_sysmuted(self):
        """
        return system mute state
        from MidiTrack object
        """
        
        return self.sysmuted

    #-----------------------------------------

    def set_sysmuted(self, sysmuted=0, chan=0):
        """
        set internal mute state
        from MidiTrack object
        """
        
        if sysmuted:
            self.midi_man.panic(chan)
        self.sysmuted  = sysmuted

    #-----------------------------------------

    def is_soloed(self):
        """
        return solo state 
        from MidiTrack object
        """
        
        return self.soloed

    #-----------------------------------------
     
    def set_soloed(self, soloed=0):
        """
        set solo track or no 
        from MidiTrack object
        """
        
        self.soloed = soloed

    #-----------------------------------------

    def is_armed(self):
        """
        return  arm state 
        from Track object
        """
        
        return self._armed

    #-----------------------------------------
     
    def set_armed(self, armed=0):
        """
        set arm track or no 
        from Track object
        """
        
        self._armed = armed

    #-----------------------------------------

    def is_arm_muted(self):
        """
        return internal mute state for armed track
        from Track object
        """
        
        return self._arm_muted

    #-----------------------------------------

    def set_arm_muted(self, arm_muted=0):
        """
        set internal mute state for armed track
        from Track object
        """
        
        self._arm_muted  = arm_muted

    #-----------------------------------------

    def is_selected(self):
        """
        return whether the track is selected from track object
        """

        return self._selected
    
    #-----------------------------------------

    def set_selected(self, selected=0):
        """
        set track select from track object
        """

        self._selected = selected

    #-----------------------------------------

#========================================

class MidiBase(object):
    """ midi base manager """
    def __init__(self):
        self.notes_name = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
        self.notes_lst = []
        self.tempo = 500000 # in microseconds
        self.micro_sec = 1e6
        self.format_type =0
        self.numerator =4 # time signature
        self.denominator =4 # time signature
        self.ppq = 120 # pulse per quarter, tick per beat
        self.bar = self.numerator * self.ppq # in ticks
        self.nb_beats = self.ppq * self.numerator # in ticks
        self.sec_per_beat = self.tempo / self.micro_sec # 
        self.sec_per_tick = self.sec_per_beat / float(self.ppq)
        self.bpm =0
        self.playable_lst = ['note_off', 'note_on', 'polytouch', 
                'control_change', 'program_change', 'aftertouch', 
                'pitchwheel']


    #-----------------------------------------

    def gen_notes(self):
        """
        generate notes names
        from MidiBase object
        """

        self.notes_lst = ["{}{}".format(item, i) for i in range(9) for item in self.notes_name]

    #-----------------------------------------

    def get_notename(self, note=0):
        """
        returns name of index note
        from MidiBase object
        """
        
        name = ""
        try:
            name = self.notes_lst[note]
        except IndexError:
            pass

        return name

    #-----------------------------------------

    def get_noteindex(self, note_name=""):
        """
        returns index note from note name like: C0, C8
        from MidiBase object
        """
        
        index =0
        if note_name:
            note_name = note_name.upper()
        try:
            index = self.notes_lst.index(note_name)
        except IndexError:
            pass

        return index

    #-----------------------------------------

    def tick2bar(self, nb_tick):
        """
        convert ticks to bar
        from MidiBase object
        """

        (nb_bar, nb_tick) = divmod(nb_tick, self.bar)
        (nb_beat, nb_tick) = divmod(nb_tick, self.ppq)
       
        return (nb_bar, nb_beat, nb_tick)

    #-----------------------------------------

    def tick2sec(self, nb_tick):
        """
        convert ticks to seconds
        from MidiBase object
        """

        # debug("sec_per_tick: {}".format(self.sec_per_tick))
        return nb_tick * self.sec_per_tick

    #-----------------------------------------

    def sec2tick(self, nb_sec):
        """
        convert seconds to ticks
        from MidiBase object
        """

        return int(nb_sec / self.sec_per_tick)

    #-----------------------------------------

    def tempo2bpm(self, tempo):
        """
        convert tempo to bpm
        from MidiBase object
        """
        
        val =0
        if tempo > 0:
            val = 60 * self.micro_sec / tempo
        
        return val

    #-----------------------------------------

    def bpm2tempo(self, bpm):
        """
        convert bpm to tempo
        from MidiBase object
        """
        
        val =0
        if bpm > 0:
            val = 60 * self.micro_sec / bpm
        
        return val

    #-----------------------------------------

    def update_tempo_params(self):
        """
        update the tempo parameters
        from MidiBase object
        """
        
        # self.numerator =4 # time signature
        # self.denominator =4 # time signature
        # self.ppq = 120 # pulse per quarter, tick per beat
        self.bar = self.numerator * self.ppq # in ticks
        self.nb_beats = self.ppq * self.numerator # in ticks
        self.sec_per_beat = self.tempo / self.micro_sec # 
        self.sec_per_tick = float(self.sec_per_beat) / float(self.ppq)
        # debug(self.tempo)

    #-----------------------------------------

#========================================

class MidiMetronome(object):
    """ midi metronome manager """
    def __init__(self, seq):
        self._base = seq.base
        self._count_in =0
        self._click_track = None

    #-----------------------------------------

    def set_ppq(self, ppq):
        """
        set the ppq (pulse per quarter note)
        from MidiSequence object
        """

        self.ppq = ppq
        
    #-----------------------------------------

    def set_tempo(self, tempo):
        """
        set the tempo
        from MidiSequence object
        """

        self.tempo = tempo
        
    #-----------------------------------------

    def init_click(self, bpm=100):
        """ 
        init a click patern 
        from the metronome object
        parameters :

        -- bpm
        Description: beat per minute, rate for the metronome
        Default value: 100
        """
        
        click_track = None
        if self._click_track:
            self.stop_click()
            self._click_track = None
        click_track = self._gen_click(bpm)

        return click_track

    #-----------------------------------------

    def _gen_click(self, bpm):
        """ 
        generate a click patern 
        from the metronome object
            parameters :
            -- bpm
            Description: beat per minute, rate for the metronome
            
        """
        
        val =0
        ev_lst = []
        # delete old tempo track
        click_track = None
        numerator = self._base.numerator
        ppq = self._base.ppq
        # create tempo track
        tracknum =0
        note = 67 # G5, high Cowbell
        for j in range(numerator):
            if j == 0:
                note = 67 # G5, high CowBell
                vel =120
            else:
                note =68 # G#5, low CowBell
                vel = 80
            # Note On
            evt = MidiEvent(type='note_on')
            msg0 = evt.msg # mido.Message(type='note_on')
            msg0.channel =9 # drums
            msg0.note = note
            msg0.velocity = vel
            msg0.time = val
            evt.tracknum = tracknum
            ev_lst.append(evt)
            val += ppq # in absolute tick
            
            # Note Off
            evt = MidiEvent(type='note_off')
            msg1 = evt.msg # mido.Message(type='note_off')
            msg1.channel =9 # drums
            msg1.note = note
            msg1.time = val
            evt.tracknum = tracknum
            ev_lst.append(evt)

        click_track = MidiTrack()
        click_track.add_evs(*ev_lst)
        click_track.repeating =1
        click_track.channel_num =9 # drums
            
        if click_track:
            self._click_track = click_track
            self._click_track.set_active(0)
            self.change_bpm(bpm)

        return self._click_track

    #-----------------------------------------

    def get_bpm(self):
        """ 
        returns tempo rate 
        from metronome object
        """
        
        return self.bpm

    #-----------------------------------------

    def change_bpm(self, bpm=100):
        """ 
        Change the bpm:
        convienient method for metronome
        change tempo rate 
        from metronome object
        Parameters
        -- bpm
        Description: number of Beat per minute for the tempo
        
        """

        res =0
        if bpm >0:
            self._base.tempo = 60 * self._base.micro_sec / bpm
            self._base.bpm = bpm
            self._base.update_tempo_params()
            res = bpm

            return res
            

    #-----------------------------------------

    def start_click(self):
        """ 
        start click 
        from metronome object
        """

        if self._click_track:
            self._click_track.set_active(1)

    #-----------------------------------------

    def stop_click(self):
        """ 
        stop click 
        from metronome object
        """

        if self._click_track:
            self._click_track.set_active(0)

    #-----------------------------------------

    def is_clicking(self):
        """ 
        whether clicking 
        from metronome object
        """

        res =0
        if self._click_track:
            res = self._click_track.is_active()
        
        return res
    
    #-----------------------------------------

    
    def gen_tempo_track(self):
        """
        generate tempo track
        Note: deprecated function
        from MidiMetronome object
        """

        val =0
        ev_lst = []
        # delete old tempo track
        click_track = None
        # create tempo track
        tracknum =0
        note = 67 # G5, high Cowbell
        for _ in range(1):
            for j in range(self.numerator):
                if j == 0:
                    note = 67 # G5, high CowBell
                    vel =100
                else:
                    note =68 # G#5, low CowBell
                    vel = 80
                # Note On
                evt = MidiEvent(type='note_on')
                msg0 = evt.msg # mido.Message(type='note_on')
                msg0.channel =9 # drums
                msg0.note = note
                msg0.velocity = vel
                msg0.time = val
                evt.tracknum = tracknum
                ev_lst.append(evt)
                val += self.ppq # in absolute tick
                
                # Note Off
                evt = MidiEvent(type='note_off')
                msg1 = evt.msg # mido.Message(type='note_on')
                msg1.channel =9 # drums
                msg1.note = note
                msg1.time = val
                evt.tracknum = tracknum
                ev_lst.append(evt)

        click_track = MidiTrack()
        click_track.add_evs(*ev_lst)
        click_track.repeating =1
        click_track.channel_num =9 # drums
        
        return click_track
    
    #-----------------------------------------
 #========================================

class GroupEvent(object):
    """ part or group events manager """
    def __init__(self, seq=None):
        # parent is the sequence object """
        self._seq = seq
        self.ev_lst = []
        self.ev_index =0
        self.playable_ev = None
        self.note_group = []
        self.ev_played =0 # playingone ev or group ev 

    #-------------------------------------------

    def get_playable_ev(self, trackobj, direc=0, level=1):
        """
        returns event can be sending like midi message and not metamessage
        parameters:
        -- direc: determines what function prev or next event to be applay
        -- level: to filtering events, 0: all events, 1: only notes on...
        from GroupEvent  object
        """

        res =0
        ev1 = None
        ev2 = None
        evobj = None
        evfunc = None
        length =0
        index1 =-1 # for note_on and others
        index2 =-1 # for only note_off
        # track = self.get_track(tracknum)
        if direc >=0:
            evfunc = trackobj.next_ev
        else:
            evfunc = trackobj.prev_ev
        while 1:
            ev1 = trackobj.get_ev()
            if ev1 is None:
                break
                # return evobj
            # ev is not playable
            if direc <0 and trackobj.pos == 0:
                break
            if isinstance(ev1.msg, mido.MetaMessage) or ev1.msg.type == 'sysex':
                evfunc() # goto next or previous ev
                # debug("je passe cici pos: {}".format(track.pos))
                continue
                # return evobj
            else:
                index1 = trackobj.pos
                desc = ""
                desc1 = ""
                desc2 = ""
                if ev1.msg.type == 'note_off':
                    if level == 0: # no filtering
                        type = "Note_off"
                        desc2 = "type: {}, Value: {}, Vel: {}, Length: {}".format(type, ev1.msg.note, ev1.msg.velocity, length)
                    else: # filtering notes off
                        evfunc()
                        continue
                elif ev1.msg.type == 'note_on':
                    # getting associated note_off
                    
                    # """
                    if self._seq:
                        index2 = self._seq.get_noteoff(-1, ev1.msg.note, index1, -1)
                    trackobj.set_pos(index1)
                    if index2 >=0:
                        ev2 = trackobj.get_ev(index2)
                        length = ev2.msg.time - ev1.msg.time
                    # """

                    type = "Note_on"
                    desc2 = "type: {}, Value: {}, Vel: {}, Length: {}".format(type, ev1.msg.note, ev1.msg.velocity, length)
                elif ev1.msg.type == 'polytouch':
                    desc2 = "Type: {}, Note: {}, Value: {}".format(ev1.msg.type, ev1.msg.note, ev1.msg.value)
                elif ev1.msg.type == 'control_change':
                    desc2 = "Type: {}, Control: {}, Value: {}".format(ev1.msg.type, ev1.msg.control, ev1.msg.value)
                elif ev1.msg.type == 'program_change':
                    desc2 = "Type: {}, Value: {}".format(ev1.msg.type, ev1.msg.program)
                elif ev1.msg.type == 'aftertouch':
                    desc2 = "Type: {}, Value: {}".format(ev1.msg.type, ev1.msg.value)
                elif ev1.msg.type == 'pitchwheel':
                    desc2 = "Type: {}, Pitch: {}".format(ev1.msg.type, ev1.msg.pitch)
                timepos = ev1.msg.time
                # update all tracks position
                if self._seq:
                    self._seq.set_position(timepos)
                    # and update index of current track
                    trackobj.set_pos(index1)
                (bar, beat, tick) = self._seq.get_bar(timepos)
                timestr = "{}:{:02d}:{:03d}".format(bar, beat, tick)
                desc1 = "index: {}, Bar: {}, ".format(index1, timestr)
                if desc2:
                    desc = desc1 + desc2
                    evobj = EventObj()
                    evobj.index1 = index1 
                    evobj.ev1 = ev1
                    if ev2: # note_off
                        evobj.index2 = index2
                        evobj.ev2 = ev2
                        evobj.length = length
                    evobj.desc = desc
                    self.playable_ev = evobj
                    self.ev_played =1
                
                break
            
        trackobj.init_group_pos()

        """
        # simple test playing event
        for (i, item) in enumerate(self.ev_lst):
            # print(item[1])
            self.play_msg(item[1])
            if i >= 20:
                break
        """

        return evobj

    #-----------------------------------------
     
    def play_ev(self, evobj=None):
        """
        send midi event to the midi out port
        from GroupEvent object
        """
        
        msg = None

        if evobj is None:
            evobj = self.playable_ev
        
        if evobj and self._seq:
            track = self._seq.get_track(-1)
            msg = evobj.ev1.msg
            if msg:
                self._seq.midi_man.output_message(msg)
                time.sleep(0.300)
                if msg.type == 'note_on':
                    msg1 = mido.Message(type='note_off')
                    msg1.channel = msg.channel
                    msg1.note = msg.note
                    self._seq.midi_man.output_message(msg1)
                    
            # debug(f"msg.time: {msg.time}")
            # self.set_position(msg.time)
            # track.set_pos(evobj.index1)
            # debug(f"voici curpos: {track.pos}, group_index: {track.group_index}")
    #-----------------------------------------

    def get_note_group(self, tracknum=-1, direc=0):
        """
        returns event can be sending like midi message and not metamessage
        from GroupEvent object
        """

        res =0
        ev1 = None
        ev2 = None
        evobj = None
        evfunc = None
        res_lst = []
        track = None
        
        """
        if self._seq:
            track = self._seq.get_track(tracknum)
        else:
            return res_lst
        """
        track = self._seq.get_track(tracknum)
        if direc >=0:
            evfunc = track.next_ev_group
        else:
            evfunc = track.prev_ev_group
        while 1:
            ev = track.get_ev()
            if ev is None:
                debug("ev is None...")
                break
            else:
                ev_lst = evfunc()
                # debug(f"passe par la... pos: {track.pos}")
                # ev_lst = track.search_ev_group(ev.msg.time)
            if not ev_lst:
                debug(f"No ev_lst at track: {tracknum}, index: {track.pos}, time: {ev.msg.time}... ")
                index = track.group_index
                count = track.get_group_count()
                if index <=0 or index >= count -1:
                    break
                else:
                    continue
            for (i, ev1) in enumerate(ev_lst):
                index1 = track.pos
                desc = ""
                if ev1.msg.type == 'note_on':
                    res_lst.append(ev1)
               
            if res_lst:
                # sorting notes
                res_lst.sort(key=lambda x: x.msg.note)
                self.ev_played =0 # playing only note group
                break
        self.note_group = res_lst
        # update sequencer position
        if res_lst:
            ev1 = res_lst[0]
            timepos = ev.msg.time
            pos = track.pos
            evobj = EventObj()
            evobj.ev1 = ev1
            self.playable_ev = evobj
            # update sequence position
            if self._seq:
                self._seq.set_position(timepos)
                track.set_pos(pos)
                pass

        
        return res_lst

    #-----------------------------------------
     
    def play_note_group(self, note_group=[], timing=0):
        """
        play multiple group sending midi event to the midi out port
        whether timing, sending notes with delay between each o them
        from GroupEvent object
        """
        track = None
        
        delay = 0.300
        if not note_group:
            note_group = self.note_group
        
        if note_group:
            index1 =0
            msg = None
            if self._seq:
                track = self._seq.get_track(-1)
            for (i, ev) in enumerate(note_group):
                msg = ev.msg
                index1 = i
                self._seq.midi_man.output_message(msg)
                if timing:
                    time.sleep(delay)
                    
            if not timing:
                time.sleep(delay)
            # sending notes off
            msg1 = mido.Message(type='note_off')
            for ev in note_group:
                msg1.channel = ev.msg.channel
                msg1.note = ev.msg.note
                self._seq.midi_man.output_message(msg1)
                    
            # self.set_position(msg.time)
            # debug(f"voici pos: {track.pos}, group_index: {track.group_index}")
            # track.set_pos(track.group_index)

    #-----------------------------------------

#========================================

class MidiSequence(object):
    """
    sequence manager
    """
    def __init__(self, *args, **kwargs):
        # super().__init__()
        self.base = MidiBase() # base midi object
        self.tools = midto.MidiTools()
        self.metronome = MidiMetronome(self) #
        self.midi_man = None
        self.format_type =0
        self.quan_res =0 # quantize resolution: 4th or 16th note of bar
        self.quan_step =0 # quantize step: number of tick per step
        self.track_lst = []
        self.left_loc =0
        self.right_loc =0
        self.start_loop =0
        self.end_loop =0
        self.looping =0
        self.quantizing =0
        self.tracknum =1
        self.mid = None
        self.track_names = [] # list containing track and instrument name
        self._tracks_arm = []
        self.curpos =0
        self.click_track = None
        self._length =0
        self.clipboard = []
        self.group_ev = None

    #-----------------------------------------

    def init_tempo_track(self):
        """
        init the click track
        returns click track object
        from MidiSequence object
        """

        self.click_track = self.metronome.init_click()
        return self.click_track

    #-----------------------------------------

    def get_tracks(self):
        """
        returns track list
        from MidiSequence object
        """

        return self.track_lst

    #-----------------------------------------

    def update_sequencer(self):
        """
        update sequencer
        from MidiSequence object
        """

        for track in self.track_lst:
            track.midi_man = self.midi_man
            # track.channel_num =9 # drum channel
            track.set_pos(0)
        # update sequencer length
        self.update_length()

    #-----------------------------------------

    def init_sequencer(self, midi_driver):
        """
        init midi sequencer
        from MidiSequence object
        """

        self.midi_man = midi_driver
        # generate data
        self.gen_default_data()
        # pass the midi driver to all tracks
        for track in self.track_lst:
            track.midi_man = self.midi_man
            track.channel_num =9 # drum channel
            track.set_pos(0)
        # init bar number and loop state
        self.start_loop =0
        self.end_loop = self.base.bar * 2
        self.looping =1
        # quantize at 16th notes
        self.quan_res =16 # 16th note per bar
        self.quan_step = int(self.base.bar / self.quan_res) # in ticks
        # set autoquantize
        self.quantizing =1
        # generate notes name list
        self.base.gen_notes()

    #-----------------------------------------

    def set_seq_pos(self, pos):
        """
        set the current sequence position without update tracks position
        from MidiSequence object
        """

        self.curpos = pos

    #-----------------------------------------

    def get_position(self):
        """
        returns player position
        from MidiSequence object
        """

        return self.curpos

    #-----------------------------------------

    def set_position(self, pos):
        """
        set player position
        from MidiSequence object
        """

        seq_len = self.get_length()
        pos = limit_value(pos, 0, seq_len)
        self.update_tracks_position(pos) 
        self.curpos = pos
          
    #-----------------------------------------

    def get_length(self):
        """
        returns length player
        from MidiSequence
        """
        
        # position in trackline is in time
        return self._length

    #-----------------------------------------

    def update_length(self):
        """
        returns max track length
        from MidiSequence object
        """

        val =0
        track = self.get_track(0)
        val =  track.get_length()
        
        """
        for (i, track) in enumerate(self.track_lst):
            ilen = track.get_length()
            if ilen > val:
                val = ilen
        """

        self._length = val
        return val

    #-----------------------------------------

    def update_tracks_position(self, pos=-1):
        """
        updating tracks position
        from MidiSequence object
        """

        if pos == -1: pos = self.curpos
        for (i, track) in enumerate(self.track_lst):
            track.lastpos =-1
            index = track.search_pos(pos)
            track.set_pos(index)

    #-----------------------------------------

    def set_quantize_resolution(self, quan_res):
        """
        set the quantize resolution and quantize step in tick
        from MidiSequence object
        """

        res =0
        if quan_res >0:
            self.quan_step = int(self.bar / quan_res)
            self.quan_res = quan_res
            res = self.quan_step
        
        return res

    #-----------------------------------------

    def quantize_track(self, type=0, tracknum=-1, quan_res=0):
        """
        generate quantization belong the track type:
        type 0: normal tracks
        type 1: recorded track
        type 2: incoming messages list
        from MidiSequence object
        """
        
        note_lst = []
        ind_lst = []
        # self.quan_step = self.bar / self.quan_res
        if quan_res == 0:
            quan_step = self.quan_step
        else:
            quan_step = self.set_quantize_resolution(quan_res)
        if quan_step == 0:
            return
        if type == 0:
            track = self.get_track(tracknum)
            ev_lst = track.get_list()
        elif type == 1:
            # must be modified in input callback function
            ev_lst = self.rec_track.get_list()
        else:
            # must be modified in rec_lst
            ev_lst = self.rec_lst
        
        # debug("voici list: {}".format(msg_lst))
        for (i, ev)  in enumerate(ev_lst):
            msg = ev.msg
            # debug("msg_time: {}".format(msg.time))
            if msg.type == 'note_off':
                continue
            elif msg.type == 'note_on':
                # we searching the note_off associated with this note on
                title = "Note_on"
                msg_str = "index: {}, note: {}, time: {}".format(i, msg.note, msg.time)
                # debug(msg_str, title, write_file=True)
                note_lst = []
                for (j, ev1) in enumerate(ev_lst[i:], i):
                    msg1 = ev1.msg
                    if msg1.type == 'note_off' and msg1.note == msg.note\
                            and j not in ind_lst:
                            note_lst.append((msg, i))
                            note_lst.append((msg1, j))
                            ind_lst.append(j)
                            title = "Note_off"
                            msg_str = "index: {}, note: {}, time: {}".format(j, msg1.note, msg1.time)
                            # debug(msg_str, title, write_file=True)
                            break

            # calculate quantization step
            (div, rest) = divmod(msg.time, quan_step)
            if rest >0:
                if note_lst:
                    # (note, note1) = note_lst
                    (note, ind) = note_lst[0]
                    (note1, ind1) = note_lst[1]
                    if rest <= quan_step / 2:
                        # shift note at the previous step
                        val = note.time - rest
                        val1 = note1.time - rest
                    else: # rest greater than
                        # shift note at the next step
                        val = note.time - rest + quan_step
                        val1 = note1.time - rest + quan_step
                    note.time = val
                    note1.time = val1
                    ev = ev_lst[ind] 
                    ev1 = ev_lst[ind1] 
                    # ev.msg = note
                    # ev1.msg = note1
                    note_lst = []
                    # debug("notes found")
                else: # no note_lst
                    if rest <= quan_step / 2:
                        # shift msg at the previous step
                        val = msg.time - rest
                    else:
                        # shift msg at the next step
                        val = msg.time - rest  + quan_step
                    msg.time = val
            else: # no rest
                pass
        # re generate trackline
        self.gen_trackline() 
        
        """
        debug("Liste complete", write_file=True)
        for msg in msg_lst:
            debug("Type: {}, Note: {}, Time: {}".format(msg.type, msg.note, msg.time), write_file=True)
        """

    #-----------------------------------------

    def toggle_quantize(self):
        """
        toggle auto quantize state
        from MidiSequence object
        """

        self.quantizing = not self.quantizing

        return self.quantizing
    
    #-----------------------------------------

    def get_left_locator(self):
        """
        get left locator
        from MidiSequence object
        """

        return self.left_loc

    #-----------------------------------------

    def set_left_locator(self, val):
        """
        set left locator
        from MidiSequence object
        """

        seq_len = self.get_length()
        val = limit_value(val, 0, seq_len)
        self.left_loc = val

    #-----------------------------------------

    def get_right_locator(self):
        """
        get right locator
        from MidiSequence object
        """

        return self.right_loc

    #-----------------------------------------

    def set_right_locator(self, val):
        """
        set right locator
        from MidiSequence object
        """

        seq_len = self.get_length()
        val = limit_value(val, 0, seq_len)
        self.right_loc = val

    #-----------------------------------------

    def get_locators(self):
        """
        return left and right locator
        from MidiSequence object
        """

        return (self.left_loc, self.right_loc)

    #-----------------------------------------

    def set_locators(self, l_loc, r_loc):
        """
        set left and right locator
        from MidiSequence object
        """

        self.set_left_locator(l_loc)
        self.set_right_locator(r_loc)

    #-----------------------------------------

    def get_start_loop(self):
        """
        get start loop
        from MidiSequence object
        """

        return self.start_loop

    #-----------------------------------------

    def set_start_loop(self, val):
        """
        set start loop
        from MidiSequence object
        """

        seq_len = self.get_length()
        val = limit_value(val, 0, seq_len)
        self.start_loop = val

    #-----------------------------------------

    def get_end_loop(self):
        """
        get end loop
        from MidiSequence object
        """

        return self.end_loop

    #-----------------------------------------

    def set_end_loop(self, val):
        """
        set end loop
        from MidiSequence object
        """

        seq_len = self.get_length()
        val = limit_value(val, 0, seq_len)
        self.end_loop = val

    #-----------------------------------------
    def set_looping(self, looping):
        """
        set looping state
        from MidiSequence object
        """

        self.looping = looping

    #-----------------------------------------

    def is_looping(self):
        """
        returns looping state
        from MidiSequence object
        """

        return self.looping

    #-----------------------------------------

    def toggle_loop(self):
        """
        toggle looping state
        from MidiSequence object
        """

        self.looping = not self.looping
        
        return self.looping

    #-----------------------------------------
   
    def loop_manager(self):
        """ 
        loop manager 
        from MidiSequencer object
        """

        res =0
        if self.looping:
            # seq_len = self.get_length()
            curpos = self.get_position()
            # debug("curpos: {}".format(curpos))
            if curpos >= self.end_loop: 
                self.set_position(self.start_loop)
                res =1
                # debug("curpos %d, end_loopl %d" %(self.curpos, self.end_loop))
                # if self._recording:
                # check data recording and generate trackline
       
        return res

    #-----------------------------------------
    
    def get_bar(self, pos=-1):
        """
        convert pos in tick to bar
        from MidiSequence
        """
 
        if pos == -1: 
            pos = self.get_position()
        
        bar = self.base.bar
        (nb_bars, nb_ticks) = divmod(pos, bar)
        ppq = self.base.ppq
        (nb_beats, nb_ticks) = divmod(nb_ticks, ppq)

        nb_bars +=1 # for user friendly
        nb_beats +=1
        # nb_ticks +=1
        
        return (nb_bars, nb_beats, nb_ticks)
    
    #-----------------------------------------


 
    def get_tracknum(self):
        """
        returns track index
        from MidiSequence object
        """

        return self.tracknum

    #-----------------------------------------
     
    def get_nb_tracks(self):
        """
        returns number of tracks
        from MidiSequence object
        """

        return len(self.track_lst)

    #-----------------------------------------
    
    def change_tracknum(self, step=0, adding=0):
        """
        change track number
        from MidiSequence object
        """
        
        # getting any track object
        track = self.get_track(0)
        self.tracknum = track.change_item(self.tracknum, self.track_lst, step, adding, min_val=1, max_val=-1)
        track = self.get_track(self.tracknum)
        channel_num = track.channel_num
        track.select_channel(step=channel_num, adding=0)
        
        return self.tracknum

    #-----------------------------------------

    def get_track(self, tracknum=-1):
        """
        returns current track object
        from MidiSequence object
        """

        track = None
        # current track
        if tracknum == -1:
            tracknum = self.tracknum
        try:
            track = self.track_lst[tracknum]
        except IndexError:
            pass
       
        return track

    #-----------------------------------------
    
    def mute(self, muted=0, tracknum=-1):
        """
        set track mute from sequence object
        arguments
        muted: state of mute
        default: 0, not mute
        track_num: track number
        default: -1, current track
        from MidiSequence object
        """

        if tracknum == -1:
            tracknum = self.tracknum
        track = self.get_track(tracknum)
        
        track.set_muted(muted, track.channel_num)
        
        return muted
    
    #-----------------------------------------

    def toggle_mute(self, tracknum=-1):
        """
        toggle mute from sequence object
        arguments
        track_num: track number
        default: -1, current track
        from MidiSequence object
        """
        if tracknum == -1:
            tracknum = self.tracknum
        track = self.get_track(tracknum)
        muted = not track.is_muted()
        self.mute(muted)
        
        return muted
    
    #-----------------------------------------

    def solo(self, soloed=0, tracknum=-1):
        """
        set track solo from sequence object
        arguments
        soloed: state of solo
        default: 0, not solo
        track_num: track number
        default: -1, current track
        from MidiSequence object
        """

        soloing =0
        if tracknum == -1:
            tracknum = self.tracknum
        track = self.get_track(tracknum)
        track.set_soloed(soloed)
        if soloed:
            track.set_sysmuted(0, track.channel_num)
            for (i, trk) in enumerate(self.track_lst, 1):
                if not trk.is_soloed():
                    # sysmute others tracks whether current track is soloed 
                    trk.set_sysmuted(1, trk.channel_num)
        else: # no soloed
            for (i, trk) in enumerate(self.track_lst, 1):
                if trk.is_soloed():
                    # sysmute the track whether one is soloed
                    track.set_sysmuted(1, track.channel_num)
                    soloing =1
                    break
            if not soloing: # no track is soloing
                for (i, trk) in enumerate(self.track_lst, 1):
                    trk.set_sysmuted(0, trk.channel_num)
                
        return soloed

    #-----------------------------------------

    def toggle_solo(self, tracknum=-1):
        """
        toggle solo from sequence object
        arguments
        track_num: track number
        default: -1, current track
        from MidiSequence object
        """
        
        if tracknum == -1:
            tracknum = self.tracknum
        track = self.get_track(tracknum)
        soloed = not track.is_soloed()
        self.solo(soloed)

        return soloed

    #-----------------------------------------

    def arm(self, armed=0, tracknum=-1):
        """
        set track arm 
        arguments:
        armed: state of arm track
        default: 0, not armed
        track_num: track number
        default: -1, current track
        from MidiSequence object
        """

        if tracknum == -1:
            track = self.get_track()
            tracknum = self.get_tracknum()
        else:
            track = self.get_track(tracknum)
        track.armed = armed
        if armed == 0:
            if tracknum in self._tracks_arm:
                self._tracks_arm.remove(tracknum)
        else: # arm equal 1
            if tracknum not in self._tracks_arm:
                # temporary: exclusive arm
                self._tracks_arm = []
                self._tracks_arm.append(tracknum)
                self._tracks_arm.sort()
        
        return (tracknum, armed)

    #-----------------------------------------

    def get_tracks_armed(self):
        """
        returns track armed list
        from MidiSequence object
        """

        return self._tracks_arm

    #-----------------------------------------
 
   
    def erase_track(self, tracknum=-1, start_pos=0, end_pos=-1):
        """
        erase event in track
        from MidiSequence object
        """

        res =0
        track = self.get_track(tracknum)
        if track:
            ev_lst = track.get_list()
            if start_pos == 0 and end_pos == 0:
                return (res, tracknum)
            elif start_pos >= end_pos and end_pos != -1:
                return (res, tracknum)
            
            if end_pos == -1:
                # delete all events
                ev_lst[:] = []
                res =1
            else:
                (start_ind, end_ind) = self.tools.get_track_range(track, start_pos, end_pos)
                if start_ind and end_ind != -1:
                    ev_lst[start_ind:end_ind] = []
                    debug("voici start_ind: {} et end_ind: {}".format(start_ind, end_ind))
                    res =1
            
            
        return (res, tracknum)

    #-----------------------------------------
     
    def delete_track(self, tracknum=-1):
        """
        deelete track to the track list
        from MidiSequence object
        """

        res =0
        if tracknum == -1:
            tracknum = self.tracknum
        try:
            del self.track_lst[tracknum]
            res =1
        except IndexError:
            pass
        
        """
        if res: 
            self.gen_trackline()
        """

        return (res, tracknum)

    #-----------------------------------------
    
    def get_noteoff(self, tracknum=-1, note=0, start_ind=0, end_ind=-1):
        """
        returns note off index in a range
        from MidiSequence object
        """

        res = -1
        track = self.get_track(tracknum)
        ev_lst = track.get_list()
        if end_ind == -1:
            end_ind = len(ev_lst) -1
        for (i, ev) in enumerate(ev_lst[start_ind:end_ind], start_ind):
            if ev.msg.type == 'note_off' and ev.msg.note == note: 
                res = i
                break

        return res

    #-----------------------------------------

    def get_notes(self, tracknum=-1, start_ind=0, end_ind=-1):
        """
        returns track notes list in a range
        from MidiSequence object
        """

        note_lst = []
        tmp_lst = []
        track = self.get_track(tracknum)
        ev_lst = track.get_list()
        if end_ind == -1:
            end_ind = len(ev_lst) -1
        for (i, ev) in enumerate(ev_lst[start_ind:end_ind], start_ind):
            if ev.msg.type == 'note_on':
                for (j, ev1) in enumerate(ev_lst[i:], i):
                    if ev1.msg.type == 'note_off' and ev.msg.note == ev1.msg.note\
                        and j not in tmp_lst:
                        note_lst.append((tracknum, i, j))
                        tmp_lst.append(j)
                        break

        return note_lst

    #-----------------------------------------

    def delete_notes(self, tracknum=-1, start_pos=0, end_pos=-1, min_note=0, max_note=127):
        """
        deelete notes on the track
        from MidiSequence object
        """

        res =0
        track = self.get_track(tracknum)
        ev_lst = track.get_list()
        if start_pos == 0 and end_pos == 0:
            return (res, tracknum)
        elif start_pos >= end_pos and end_pos != -1:
            return (res, tracknum)
        
        if end_pos == -1:
            # delete all events
            end_pos = len(ev_lst) -1
        (start_ind, end_ind) = self.tools.get_track_range(track, start_pos, end_pos)
        if start_ind and end_ind != -1:
            # for (i, ev) in enumerate(ev_lst[start_ind:end_ind], start_ind):
            note_lst = self.get_notes(tracknum, start_ind, end_ind)
            """
            for item in note_lst:
                # getting index of note_on and note_off
                id1 = item[1]
                id2 = item[2]
                ev = ev_lst[id1]
                if ev.msg.note >= min_note and ev.msg.note <= max_note:
                    # delete note_on and associated note_off
                    del ev_lst[id1]
                    res =1
    œ       """

        
        return (res, tracknum)

    #-----------------------------------------
    def init_event_task(self, tracknum=-1):
        """
        init events task
        from MidiSequence object
        """
        
        self.group_ev = GroupEvent(self)

        track = self.get_track(tracknum)
        track.gen_group_pos()
        # debug(f"voici len group_lst: {len(track.group_lst)} ")


    #-----------------------------------------

    def select_note_group(self, step=0, adding=0):
        """
        select notes group
        Note: not used for the moment
        from MidiSequence object
        """
        ev_lst = None
        
        if self.group_ev:
            ev_lst = self.group_ev.get_note_group(self.tracknum, step) 
        
        return ev_lst

    #-----------------------------------------
    
    def filter_notes(self, tracknum, start_note, end_note):
        """
        filter notes range in event list
        from MidiSequence object
        """
        
        track = self.get_track(tracknum)
        ev_lst = track.get_list()
        start_ind = self.get_noteindex(start_note)
        end_ind = self.get_noteindex(end_note)
        i =0
        while i < len(ev_lst): 
            
            ev = ev_lst[i]
            msg = ev.msg
            if msg.type == 'note_on' or msg.type == 'note_off':
                if msg.note >= start_ind and msg.note <= end_ind:
                    del ev_lst[i]
                    i -=1
                    continue
            
            # debug("val: {}, len_lst: {}".format(i, len(ev_lst)))
            i += 1
        
        # self.gen_trackline() 

    #-----------------------------------------

    def move_notes(self, tracknum, start_note, end_note):
        """
        move notes range in event list on a new track
        Note: Temporary function
        from MidiSequence object
        """
        
        new_lst = []
        track = self.get_track(tracknum)
        ev_lst = track.get_list()
        start_ind = self.get_noteindex(start_note)
        end_ind = self.get_noteindex(end_note)
        i =0
        while i < len(ev_lst): 
            ev = ev_lst[i]
            msg = ev.msg
            if msg.type == 'note_on' or msg.type == 'note_off':
                if msg.note >= start_ind and msg.note <= end_ind:
                    new_lst.append(ev)
                    del ev_lst[i]
                    i -=1
                    continue
            
            # debug("val: {}, len_lst: {}".format(i, len(ev_lst)))
            i += 1
        # create new track
        new_track = MidiTrack()
        new_track.add_evs(*new_lst)
        self.track_lst.append(new_track)
        self.update_player()

    #-----------------------------------------

    def select_one_ev(self, step=0, adding=0):
        """
        select event index
        from MidiSequence object
        """
        
        # getting current track object
        track = self.get_track(self.tracknum)
        # debug(f"voici tracknum et pos: {self.tracknum, track.pos}")
        if step >= 0:
            track.next_ev()
        else:
            track.prev_ev()
        if self.group_ev:
            evobj = self.group_ev.get_playable_ev(track, step)
           
        return evobj

    #-----------------------------------------
    
    def change_event_channel(self, tracknum=-1, chan=0):
        """
        change all events channel on the track
        from MidiSequence object
        """

        track = self.get_track(tracknum)
        for (i, ev) in enumerate(track.get_list()):
            ev.msg.channel = chan
        track.channel_num = chan

    #-----------------------------------------

    def change_event_program(self, tracknum, type, pos, val):
        """
        change event program on the track
        from MidiSequence object
        """

        track = self.get_track(tracknum)
        ev = track.search_ev(type, pos)
        if ev:
            ev.msg.program = val

    #-----------------------------------------

    def change_event_tempo(self, tracknum, time, val):
        """
        change event program on the track
        from MidiSequence object
        """

        track = self.get_track(tracknum)
        if track is None:
            return
        type = "set_tempo"
        ev = track.search_ev(type, time)
        if ev:
            ev.msg.tempo = int(val)
        else:
            # debug("event tempo not found")
            ev = MidiEvent(type=type, cat=1)
            ev.msg.tempo = int(val)
            ev.msg.time =0
            track.insert(0, ev)

    #-----------------------------------------

    def delete_event(self, evobj=None):
        """
        delete event in its track
        from MidiSequence object
        """
        
        res = None
        if evobj is None:
            evobj = self.playable_ev
        if evobj:
            tracknum = evobj.ev1.tracknum
            tracknum += 1
            track = self.get_track(tracknum)
            ev_lst = track.get_list()
            debug("len ev_lst: {}".format(len(ev_lst)))
            try:
                ev1 = ev_lst[evobj.index1]
                res = ev1
                if evobj.ev2: # note_off
                    debug("noteoff found at index: {}".format(evobj.index2))
                    del ev_lst[evobj.index2]
                del ev_lst[evobj.index1]
            except IndexError:
                debug("Error on deleting event, track: {}, index: {}, ev: {}".format(evobj.ev.tracknum, evobj.index, evobj.ev.msg))

            if res:
                pos = self.get_position()
                # self.gen_trackline()
                self.set_position(pos)
                
        return res

    #-----------------------------------------
    
    def insert_tempo_track(self):
        """
        insert a new track at the begining of track list
        from MidiSequence object
        """

        track = MidiTrack()
        self.track_lst.insert(0, track)
        self.gen_tracknum()
        # self.gen_trackline()
        self.update_sequencer()

    #-----------------------------------------

    def gen_tracknum(self):
        """
        generate track number in the event object
        from MidiSequence object
        """
        
        for (i, track) in enumerate(self.track_lst):
            ev_lst = track.get_list()
            for ev in ev_lst:
                ev.tracknum = i

    #-----------------------------------------
    
    def load_file(self, filename):
        """
        load file name
        from MidiSequence object
        """

        res =0
        ev_lst = []
        self.track_lst = []
        # from mido import MidiFile
        self.mid = mido.MidiFile(filename)
        # print(mid.ticks_per_beat)

        track_count =0
        track_name = ""
        instrument_name = ""
        self.track_names = [] # list containing track and instrument name
        tempo =0
        track_tempo = None
        bpm =0
        channel_num =0
        channeling =0
        patch_num =0

        # create tempo track 0 when  it missing
        if len(self.mid.tracks) == 1:
            # create track tempo
            track_tempo = MidiTrack()
            self.track_lst.append(track_tempo)
            track_count +=1
            names = ["", ""] # for name and instrument list of tracks
            self.track_names.append(names)

        self.format_type = self.mid.type
        self.base.ppq = self.mid.ticks_per_beat
        for (tracknum, trackobj) in enumerate(self.mid.tracks):
            abstick =0
            channel_num = -1
            bank_num =-1
            preset_num =-1
            patch_num =-1
            channeling =0
            track_name = ""
            instrument_name = ""
            names = ["", ""] # for name and instrument list of tracks
            ev_lst = []
            for msg in trackobj:
                evt = None
                evt0 = None
                if msg.type == 'set_tempo':
                    if track_tempo:
                        evt0 = MidiEvent()
                        evt0.msg = msg
                        track_tempo.append(evt0)
                    else:
                        evt = MidiEvent()
                        evt.msg = msg
                    # print("voici tempo: ",msg.tempo)
                    self.base.tempo = msg.tempo
                    # print("ticks_per_beat or ppq: {}".format(self.ppq))
                    # print("Tempo: {}".format(msg.tempo))
                elif msg.type == 'track_name':
                    evt = MidiEvent()
                    evt.msg = msg
                    track_name = msg.name
                    names[0] = track_name
                elif msg.type == 'instrument_name':
                    evt = MidiEvent()
                    evt.msg = msg
                    instrument_name = msg.name
                    names[1] = instrument_name
                elif msg.type == 'time_signature':
                    if track_tempo:
                        evt0 = MidiEvent()
                        evt0.msg = msg
                        track_tempo.append(evt0)
                    else:
                        evt = MidiEvent()
                        evt.msg = msg
                    self.numerator = msg.numerator
                    self.denominator = msg.denominator
                    # print(msg)
                elif msg.type in ('sequence_number', 'text', 'copyright', 'lyrics', 'key_signature',\
                    'marker', 'cue_marker', 'midi_port', 'smpte_offset', 'end_of_track'):
                    evt = MidiEvent()
                    evt.msg = msg
                elif msg.type == 'sysex':
                    evt = MidiEvent()
                    evt.msg = msg
                    pass
                elif not isinstance(msg, mido.MetaMessage):
                    channeling =1
                    evt = MidiEvent(type='note_on')
                    evt.msg = msg
                    if msg.type == 'note_on': 
                        if msg.velocity == 0:
                            evt = MidiEvent(type='note_off')
                            evt.msg.note = msg.note
                            evt.msg.velocity = msg.velocity
                            evt.msg.channel = msg.channel
                        
                        else: # velocity != 0
                            evt = MidiEvent(type='note_on')
                            evt.msg = msg
                    elif msg.type == 'control_change':
                        evt.msg = msg
                        if msg.control == 0 or msg.control == 32:
                            bank_num = msg.control
                            preset_num = msg.value
                        # print("control {}".format(msg.control))
                    elif msg.type == 'program_change': 
                        evt.msg = msg
                        patch_num = msg.program
                    elif msg.type == 'polytouch':
                        evt.msg = msg
                    elif msg.type == 'aftertouch':
                        evt.msg = msg
                    elif msg.type == 'pitchwheel':
                        evt.msg = msg

                if evt:
                    evt.tracknum = track_count + tracknum
                    # evt.msg is a mido message
                    # print("voici: ",msg.type)
                    if channeling:
                        evt.msg.channel = msg.channel
                        channel_num = evt.msg.channel
                        channeling =0

                    abstick  += msg.time
                    evt.msg.time = abstick
                    ev_lst.append(evt)
                    # print("type: {}, note: {}, vel: {}".format(msg.type, msg.note, msg.velocity))



            track = MidiTrack()
            track.midi_man = self.midi_man
            if channel_num != -1:
                track.channel_num = channel_num
            if bank_num != -1:
                track.select_bank(bank_num)
            if preset_num != -1:
                track.select_preset(preset_num)
            if patch_num != -1:
                track.select_patch(patch_num)
            track.track_name = track_name
            track.instrument_name = instrument_name
            # print(track_name, instrument_name)
            if ev_lst:
                track.add_evs(*ev_lst)
                res =1
            self.track_lst.append(track)
            self.track_names.append(names)
            
        if res:
            bpm = self.base.tempo2bpm(self.base.tempo)
            self.click_track = self.metronome.init_click(bpm)
            # self.set_bpm(bpm)
            # self.update_tempo_params()
            # self.gen_tempo_track()
            # dont loop
            self.set_looping(0)
            self.tools.adjust_tracks(self.track_lst)
 
        # debug(f"voici patch_num: {patch_num}, channel_num: {channel_num}")
        return res

    #-----------------------------------------
     
    def save_midi_file(self, filename, format_type=1):
        """
        save midi file
        from MidiSequence object
        """

        ev_lst = []
        res =0
        with mido.MidiFile() as mid:
            # debug("save file")
            # print(mid.ticks_per_beat)
            mid.type = format_type
            mid.ticks_per_beat = self.base.ppq

            for (i, trackobj) in enumerate(self.track_lst):
                # creating Mido track
                track = mido.MidiTrack()
                ev_lst = trackobj.get_list()
                for (j, ev) in enumerate(ev_lst):
                    msg = ev.msg.copy()
                    """
                    if msg.type == 'set_tempo':
                        debug("bingo, set_tempo")
                    """
                    if j >0:
                        evprec = ev_lst[j-1]
                        msg.time = msg.time - evprec.msg.time 
                    track.append(msg)
                mid.tracks.append(track)
            
            mid.save(filename)
            res =1

        return res

    #-----------------------------------------
    
    def new_sequence(self):
        """ 
        create new sequence
        from MidiSequence object
        """

        # player is ready too
        bpm = 120
        for track in self.track_lst:
            track.midi_man = self.midi_man
        self.click_track = self.metronome.init_click(bpm)
        self.tools.adjust_tracks(self.track_lst)
        self.midi_man.synth.play_notes() # demo test for the synth

        return

    #-----------------------------------------

    def gen_default_data(self):
        """
        temporary function
        generate midi data
        from MidiSequence object
        """
        
        track = None
        ev_lst = []
        val =0
        tempo_track = None
        self.click_track = None
        track_lst = self.get_tracks()
        numerator = self.base.numerator
        ppq = self.base.ppq

        # create tempo track
        tracknum =0
        note = 67 # G5, high Cowbell
        for _ in range(1):
            for j in range(numerator):
                if j == 0:
                    note = 67 # G5, high CowBell
                    vel =100
                else:
                    note =68 # G#5, low CowBell
                    vel = 80
                # Note On
                evt = MidiEvent(type='note_on')
                msg0 = evt.msg # mido.Message(type='note_on')
                msg0.channel =9 # drums
                msg0.note = note
                msg0.velocity = vel
                msg0.time = val
                evt.tracknum = tracknum
                ev_lst.append(evt)
                val += ppq # in absolute tick
                
                # Note Off
                evt = MidiEvent(type='note_off')
                msg1 = evt.msg # mido.Message(type='note_on')
                msg1.channel =9 # drums
                msg1.note = note
                msg1.time = val
                evt.tracknum = tracknum
                ev_lst.append(evt)


        self.click_track = MidiTrack()
        self.click_track.add_evs(*ev_lst)
        self.click_track.repeating =1
        self.click_track.channel_num =9 # drums
        track_lst.append(self.click_track)
        track = MidiTrack()
        track.add_evs(*ev_lst)
        track.channel_num =9 # drums
        track_lst.append(track)
       
        tempo = self.base.tempo
        bpm = self.base.tempo2bpm(tempo)
        self.set_bpm(bpm)

        return self.click_track

    #-----------------------------------------

    def get_bpm(self):
        """
        returns the bpm (beat per minute)
        from MidiSequence object
        """
        
        return self.base.bpm

    #-----------------------------------------

    def set_bpm(self, bpm):
        """
        set the bpm (beat per minute) and changing the tempo track
        from MidiSequence object
        """

        if bpm >0:
            res = self.metronome.change_bpm(bpm)
            self.base.bpm = bpm
           
            if res > 0:
                # changing tempo track
                tracknum =0
                timepos =0
                self.change_event_tempo(tracknum, timepos, self.base.tempo)
                # no necessary to regenerate the tempo track
                # self.gen_tempo_track()
                self.base.update_tempo_params()

    #-----------------------------------------

    def get_click_track(self):
        """
        returns the metronome click track
        from MidiSequence object
        """

        return self.metronome._click_track
      
    #-----------------------------------------

    def get_click_data(self):
        """
        returns click data
        from MidiSequence object
        """
       
        repeat_count =0
        click_pos =0
        ev_lst = []
        ev_group = []
        nb_beats = self.base.nb_beats
        
        tracknum =0
        ev = self.click_track.get_ev()
        if ev is None:
            ev = self.click_track.next_ev()
        if ev is not None and ev.msg.type in self.base.playable_lst:
            curmsg = ev.msg
            ev_group = self.click_track.search_ev_group(curmsg.time)
            # print("voici click_msg: ", msg)
            if self.click_track.repeating:
                repeat_count = self.click_track.repeat_count
            # calculate relative time click position
            click_pos = curmsg.time + (nb_beats * repeat_count)
            
            """
            # not necessary
            rest = msg.time % nb_beats
            if rest == 0:
                click_pos = msg.time + (nb_beats * repeat_count)
            else: # rest > 0
                click_pos = rest + (nb_beats * repeat_count)
            """

            # we need note_on and note_off click with the same time
            # debug("time: {}, repeat_count: {}, click_pos: {}".format(msg.time, repeat_count, click_pos))
            for ev in ev_group:
                # copy msg for not modifying the original
                # Todo: copy MidiEvent object
                msg = ev.msg
                newev = MidiEvent()
                newev.msg = msg.copy()
                newev.tracknum = tracknum
                newev.msg.time = self.base.tick2sec(click_pos)
                # debug("time: {}".format(msg.time))
                ev_lst.append(newev)

        return ev_lst

    #-----------------------------------------

    def get_midi_data(self, curtick):
        """
        returns midi data
        from MidiSequence object
        """

        msg_lst = []
        for (tracknum, track) in enumerate(self.track_lst):
            ev_lst = track.search_ev_group(curtick)
            for ev in ev_lst:
                if ev.msg.type in self.base.playable_lst:
                    newev = MidiEvent()
                    newev.msg = ev.msg.copy()
                    newev.tracknum = tracknum
                    msg = newev.msg
                    msg.time = self.base.tick2sec(msg.time)
                    # debug("voici: {}".format(msg))
                    msg_lst.append(newev)
             
        return msg_lst

    #-----------------------------------------

    def get_properties(self):
        """
        returns properties midi file
        from MidiPlayer object
        """
        
        nb_tracks = len(self.track_lst)
        msg = "Number tracks: {}, Format type: {}, ppq: {}, Bpm: {:.2f}, timesignature: {}/{},\nTempo: {}, Sec per beat: {:.3f}, Sec per tick: {:.3f}".format(nb_tracks, self.format_type, self.base.ppq, self.base.bpm, self.base.numerator, self.base.denominator, self.base.tempo, self.base.sec_per_beat, self.base.sec_per_tick)
        return msg

    #-----------------------------------------

#========================================

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

    def init_clock(self):
        """
        returns absolute time
        from SystemScheduler object
        """

        return time.time()

    #-----------------------------------------

    def get_relclock(self):
        """
        returns relatif timing since start_time
        from SystemScheduler object
        """

        return (time.time() - self.start_time) + self.last_time

    #-----------------------------------------

    def poll_out(self):
        """
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
            if not self._thread_running:
                break
           
            if not self._player.is_playing() and not self._player.is_paused():
                if finishing:
                    self._thread_running =0
                    break

            # get timing in msec                    
            self.curtime = self.get_relclock() # (time.time() - self.start_time) + self.last_time
            self.playpos = self._base.sec2tick(self.curtime)
            seq_pos = self._seq.get_position()
            seq_len = self._seq.get_length()
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
                    # if self.curtime >= msg_ev.msg.time:
                    # waiting time
                    while self.curtime < msg_ev.msg.time:
                        time.sleep(0.001)
                        msg_timing =1
                        # there is an ev in the list, cause not yet poped
                        msg_pending =1

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
   
    def start_play_thread(self):
        """
        start sending  midi data thread
        from SystemScheduler object
        """

        if self._thread_running:
            self.stop_play_thread()
            # self.init_click()
        if self._play_thread is None:
            self._thread_running =1
            self._playing =1
            self._play_thread = threading.Thread(target=self.poll_out, args=())
            self._play_thread.daemon = True
            self._play_thread.start()

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
        self.midi_sched = None # for midi scheduler
        self.trackedit = midto.MidiTrackEdit()
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
        self.curseq = MidiSequence()
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

        if self.curseq is None:
            return 0
        clicked =0
        if self.is_clicking():
            clicked =1
            self.stop_click()

        self.curseq.set_bpm(bpm)
        if clicked:
            self.start_click()
    
    #-----------------------------------------

    def update_bpm(self, bpm):
        """
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
            self.start_engine()

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
        self.stop_engine()
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
            self.stop_engine()
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
        
        if self.curseq is None:
            return 0
        return self.curseq.get_position()

    #-----------------------------------------

    def set_position(self, pos):
        """
        set player position
        from MidiPlayer object
        """

        state = self._playing
        if self.curseq is None: return
        if state:
            self.stop_engine()
            self.midi_man.panic()
        
        self.init_pos()
        self.init_click()
        self.curseq.set_position(pos)
        
        if state:
            self._playing =1
            self.start_engine()
            
    #-----------------------------------------

    def get_length(self):
        """
        returns length player
        from MidiPlayer
        """
        
        if self.curseq is None:
            return 0
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

        if self.curseq is None:
            return
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

    def start_engine(self):
        """
        start the midi engine
        from MidiPlayer object
        """

        self.midi_sched.start_play_thread()
        self.init_click()
            
    #-----------------------------------------

    def stop_engine(self):
        """
        stop the midi engine
        from MidiPlayer object
        """

        self.midi_sched.stop_play_thread()
            
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
            self.start_engine()
        
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
            self.stop_engine()
        
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

