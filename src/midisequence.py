#!/usr/bin/python3
"""
    File: midisequence.py:
    Module for manage midi events and tracks
    Last update: Tue, 04/07/2023

    Date: Mon, 04/07/2022
    Author: Coolbrother
"""
import time
import itertools as itt
import mido
import miditools as midto
import constants as cst
import logger as log
import eventqueue as evq

log.set_level(log._DEBUG)
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
    """ 
    Deprecated Object
    midi file information 
    """
    
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
        self.group_time_lst = [] # list of tuple of uniq index and time for the event
        self.group_time_index =0
        self.time_grouping =0

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

    def clear(self):
        """
        Clear events list
        from Miditrack object
        """
        
        self.ev_lst[:] = []

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

    def get_prev_ev(self):
        """
        Returns prev event without changing position in the ev list
        from MTrack object
        """

        ret = None
        pos = self.pos
        if pos >0:
            pos -=1
            try:
                ret = self.ev_lst[pos]
            except IndexError:
                pass

        return ret

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

    def get_next_ev(self):
        """
        Returns next event without changing position in ev list
        from MTrack object
        """

        ret = None
        pos = self.pos
        if pos < len(self.ev_lst):
            pos +=1
            try:
                ret = self.ev_lst[pos]
            except IndexError:
                pass
        elif pos >= len(self.ev_lst):
            if self.repeating:
                pos =0
                try:
                    ret = self.ev_lst[pos]
                    # debug("repeat count: {}".format(self.repeat_count))
                except IndexError:
                    pass
            else: # no repeating
                pass
        
        return ret

    #-----------------------------------------

    def next_ev(self):
        """
        set next event
        from MidiTrack object
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
    
    def prev_ev_time(self):
        """
        returns previous event time in the event list
        from MidiTrack object
        """
        
        ev = self.prev_ev()
        if ev is None: return -1
        
        return ev.msg.time

    #-----------------------------------------

    def next_ev_time(self):
        """
        returns next event time in the event list
        from MidiTrack object
        """
        
        ev = self.next_ev()
        if ev is None: return -1
        
        return ev.msg.time

    #-----------------------------------------

    def search_ev_group(self, time):
        """
        Deprecated function, can be replaced by search_ev_group_time 
        returns event list between last_pos, and <= time
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
                    elif msg.time > time:
                        break
                else: # ev is None
                    self.ev_grouping =0
                    break
        
        # print(f"voici len lst: {len(lst)}")
        # debug(f"voici len lst: {len(lst)}")
        return lst

    #-----------------------------------------


    def gen_group_pos(self):
        """
        generate a list of unique index of each group event
        from MidiTrack object
        """

        self.group_lst = []
        
        """
        # Note: cannot use the fastest way:
        # lst = sorted(set(ev_lst), key=lambda x: x.msg.time)
        # Cause set do not accept complex object,
        # But only simple object as: integer, string ...
        """

        
        curtime =-1
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
        

        ret =-1
        try:
            ret = self.group_lst[self.group_index]
        except IndexError:
            pass

        return ret
    
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
    
    def get_next_group_pos(self):
        """
        returns next ev group index from ev group list
        from MidiTrack object
        """

        ret =-1
        index = self.group_index
        index +=1
        if index < len(self.group_lst):
            try:
                pos = self.group_lst[index]
                ret = self.ev_lst[pos].msg.time
            except IndexError:
                pass

        return ret
    
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

    def gen_group_time(self):
        """
        Note: Not used yet
        Generate a list of unique index and time of each group event
        from MidiTrack object
        """

        # Note: dont forget to reinitialize the group list
        self.group_time_lst = []
        self.group_time_index =0
        curtime =-1
        for (pos, ev) in enumerate(self.ev_lst):
            evtime = ev.msg.time
            if evtime != curtime:
                self.group_time_lst.append((pos, evtime))
                curtime = evtime
 
      
        return self.group_time_lst
    
    #-----------------------------------------

    def get_group_time(self):
        """
        returns current group_time from group_time_index
        from MidiTrack object
        """
        
        ret =-1
        try:
            ret = self.group_time_lst[self.group_time_index]
        except IndexError:
            pass

        return ret
    
    #-----------------------------------------

    def set_group_time(self, pos):
        """
        sets the index in the group_time list position
        from MidiTrack object
        """

        index =-1
        curpos =-1
        # group_time_lst contain a tuple index and time of each group event
        if not self.group_time_lst: return
        last_pos = self.group_time_lst[-1][0]
        if pos >= last_pos:
            index = last_pos
        else:
            for (ind, group_pos) in enumerate(self.group_time_lst):
                if group_pos[pos] == pos:
                    index = ind
                    break
                elif group_pos[0] > pos:
                    index = ind -1
                    break

        if index >= 0:
            try:
                curpos = self.group_time_lst[index][0]
                self.group_time_index = index
            except IndexError:
                pass

        return curpos
    
    #-----------------------------------------
 
    def get_prev_group_time(self):
        """
        Returns prev pos and time  without changing position in the group_time list
        from MidiTrack object
        """

        ret = None
        pos = self.group_time_index
        if pos >0:
            pos -=1
            try:
                ret = self.group_time_lst[pos]
            except IndexError:
                pass

        return ret

    #-----------------------------------------

    def prev_group_time(self):
        """
        set prev event
        from MTrack object
        """

        ret = None
        if self.group_time_index >0:
            self.group_time_index -=1
            try:
                ret = self.group_time_lst[self.group_time_index]
            except IndexError:
                pass

        return ret

    #-----------------------------------------

    def get_next_group_time(self):
        """
        Returns next pgroup pos and time without changing position in group_time  list
        from MidiTrack object
        """

        ret = None
        pos = self.group_time_index
        if pos < len(self.group_time_lst):
            pos +=1
            try:
                ret = self.group_time_lst[pos]
            except IndexError:
                pass
        elif pos >= len(self.group_time_lst):
            if self.repeating:
                pos =0
                try:
                    ret = self.group_time_lst[pos]
                    # debug("repeat count: {}".format(self.repeat_count))
                except IndexError:
                    pass
            else: # no repeating
                pass
        
        return ret

    #-----------------------------------------

    def next_group_time(self):
        """
        Sets next group pos and time 
        from MidiTrack object
        """

        ret = None
        if self.group_time_index < len(self.group_time_lst):
            self.group_time_index +=1
            try:
                ret = self.group_time_lst[self.group_time_index]
            except IndexError:
                pass
        elif self.group_time_index >= len(self.group_time_lst):
            if self.repeating:
                self.group_time_index =0
                self.repeat_count +=1
                try:
                    ret = self.group_time_lst[self.group_time_index]
                    # debug("repeat count: {}".format(self.repeat_count))
                except IndexError:
                    pass
            else:
                self.group_time_index = len(self.group_time_lst)

        return ret

    #-----------------------------------------
    
    def search_ev_group_time(self, time):
        """
        returns event list between last_pos, and exact time, 
        used when we have allready a list of group time
        from MidiTrack object
        """

        lst = []
        
        if self.pos >= len(self.ev_lst): return lst
        while 1:
            ev = self.get_ev()
            if ev is None: break
            msg = ev.msg
            if msg.time >= self.lastpos and msg.time == time:
                # debug(f"[DEBUG], search_group_time: track: {ev.tracknum}, pos: {self.pos}, msg time: {msg.time}, on time: {time}")
                lst.append(ev)
                self.next_ev()
            elif msg.time > time: 
                # debug(f"[DEBUG], search_group_time, Break Out, track: {ev.tracknum}, pos: {self.pos}, msg time: {msg.time}, on time: {time}")
                break

        # debug(f"voici len lst: {len(lst)}")
        return lst

    #-----------------------------------------

    def sort(self):
        """
        sort events list
        from MidiTrack object
        """

        self.ev_lst.sort(key=lambda x: x.msg.time)

    #-----------------------------------------

    def sort_uniq_evs(self):
        """
        Note: Not ideal but ...
        Sorting event list and uniq it by time
        from MidiTrack object
        """

        lst = []
        curtime =-1
        self.ev_lst.sort(key=lambda x: x.msg.time)
        # Note: FIXME, Deleting the doublon by time, not ideal but...
        for ev in self.ev_lst:
            evtime = ev.msg.time
            if evtime != curtime:
                lst.append(ev)
                curtime = evtime
        self.ev_lst = lst

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
        Sets the track position in event list
        from MidiTrack object
        """
        
        ev_len = len(self.ev_lst)
        if pos == -1: pos = ev_len -1
        elif pos >=0 and pos < ev_len:
            self.pos = pos
            # update event group position
            if self.ev_grouping:
                self.update_group_pos(0)
            if self.time_grouping:
                self.update_group_time(0)
    
 
    #-----------------------------------------

    def update_track_pos(self, pos=-1):
        """
        Updating the track position by searching the right time
        from MidiTrack object
        """

        if pos == -1: pos = self.pos
        self.lastpos =-1
        index = self.search_pos(pos)
        self.set_pos(index)

    #-----------------------------------------

    def update_group_pos(self, grouping=0):
        """
        update ev group position
        from MidiTrack object
        """

        self.set_group_pos(self.pos)    
        self.ev_grouping = grouping
    
    #-----------------------------------------

    def update_group_time(self, grouping=0):
        """
        update time group index
        from MidiTrack object
        """

        self.set_group_time(self.group_time_index)    
        self.time_grouping = grouping
    
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
        self.file_name = ""
        self.notes_name = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
        self.notes_lst = []
        self._tempo_ref = 60_000_000 # in microsec
        self.tempo = 500000 # in microseconds
        self.micro_sec = 1e6
        self.format_type =0
        self.numerator =4 # time signature
        self.denominator =4 # time signature
        self.ppq = 120 # pulse per quarter, or ticks per beat
        self.bar = self.numerator * self.ppq # in ticks
        self.nb_beats = self.ppq * self.numerator # in ticks
        self.sec_per_beat = self.tempo / self.micro_sec # in sec
        self.sec_per_tick = self.sec_per_beat / float(self.ppq)
        self.bpm = self._tempo_ref / self.tempo
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

    def bar2tick(self, num):
        """
        Convert bar to tick
        from MidiSequence object
        """
        
        if num <=0: num =0
        # else: num -=1 # temporary, before calculate tick to bar
        # position is in ticks
        pos = self.bar * num

        return pos

    #-----------------------------------------


    def tick2beat(self, pos):
        """
        convert pos in tick to beat
        from MidiBase object
        """
 
        if self.ppq <=0: return 0
        nb_beats = (pos // self.ppq)
        # nb_beats +=1
        
        return nb_beats
    
    #-----------------------------------------

    def beat2tick(self, pos):
        """
        convert beats values to tick
        from MidiBase object
        """
 
        if self.ppq <=0: return 0
        nb_ticks = (pos * self.ppq)
        
        return nb_ticks
    
    #-----------------------------------------


    def tick2sec(self, nb_tick):
        """
        convert ticks to seconds
        from MidiBase object
        """

        # debug("sec_per_tick: {}".format(self.sec_per_tick))
        return float(nb_tick * self.sec_per_tick)

    #-----------------------------------------

    def sec2tick(self, nb_sec):
        """
        convert seconds to ticks
        from MidiBase object
        """

        # We need rounding when passing from sec to ticks, for better playback accuracy
        return round(nb_sec / self.sec_per_tick)

    #-----------------------------------------

    def tempo2bpm(self, tempo):
        """
        convert tempo to bpm
        from MidiBase object
        """
        
        if tempo <= 0: return 0
        return float(self._tempo_ref / tempo)
        
    #-----------------------------------------

    def bpm2tempo(self, bpm):
        """
        convert bpm to tempo
        from MidiBase object
        """
        
        if bpm <= 0: return 0
        return int(self._tempo_ref / bpm) # in microsec

    #-----------------------------------------

    def update_tempo_params(self):
        """
        Updating the tempo parameters to change the bpm
        from MidiBase object
        """
        
        # self.numerator =4 # time signature
        # self.denominator =4 # time signature
        # self.ppq = 120 # pulse per quarter, tick per beat
        self.bar = self.numerator * self.ppq # in ticks, cause ppq is also number of ticks_per_beat
        self.nb_beats = self.ppq * self.numerator # in ticks, cause ppq is also ticks_per_beat
        self.sec_per_beat = float(self.tempo / self.micro_sec) # 
        self.sec_per_tick = float(self.sec_per_beat) / float(self.ppq)
        self.tick_per_sec = round((1 / self.sec_per_beat) * self.ppq) # in tick
        # debug(self.tempo)
        # self.bpm = (self._tempo_ref / self.tempo)

    #-----------------------------------------

    def set_bpm(self, bpm):
        """
        sets the bpm bellong the tempo
        from MidiBase object
        """
        if bpm <= 0: return
        self.tempo = int(self._tempo_ref / bpm)
        self.bpm = bpm
        self.update_tempo_params()

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
        from MidiMetronome object
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

        if bpm <= 0: return 0
        self._base.set_bpm(bpm)

        return bpm
            
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
    def __init__(self, parent=None, *args, **kwargs):
        # super().__init__()
        self.parent = parent
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
        self.old_tempo =120
        self._next_pos =0
        self._last_pos =0
        self._timeline = None # A MidiTrack object
        self._bpm_changed =0

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

    def init_sequencer(self, midi_driver=None):
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
            track.gen_group_pos()
        # Generate timeline track
        self._timeline = MidiTrack()
        self._timeline.init()
        self.gen_timeline()

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

    def gen_timeline(self):
        """
        Generate timeline midi track
        from MidiSequence object
        """
        
        global _DEBUG
        debugging =0
        if _DEBUG: debugging =1
        _DEBUG =0
        tim = self._timeline
        # filtering events with uniq time
        debug("\nFunc: gen_timeline, Initializing Timeline", "\nMidiSequence Info", writing_file=True)
        tim.clear()
        file_name = self.base.file_name
        debug(f"File_name: {file_name}", writing_file=True)
        total_count =0

        for track in self.track_lst:
            
            # """
            curtime =-1
            for ev in track.ev_lst:
                evtime = ev.msg.time
                if evtime != curtime:
                    tim.ev_lst.append(ev)
                    curtime = evtime
                    total_count +=1
            # """
 
  
            """
            tim.add_evs(*track.ev_lst)
            total_count += track.count()
            """
        # sorting the timeline in place
        # tim.sort()
        tim.sort_uniq_evs()
        
        # Cannot make uniq item in the event list, cause groupby function not work with complex object for consecutive item
        # tim.ev_lst = list(k for k, _ in itt.groupby(sorted(tim.ev_lst, key=lambda x: x.msg.time)))
        tim.set_pos(0)

        # Keeping index of grouping event
        # generate group position for the timeline
        tim.gen_group_pos()
        # Or generate tuple of uniq index and time for group event
        tim.gen_group_time()
        count = tim.count()
        if count:
            first_tick = tim.ev_lst[0].msg.time
            last_tick = tim.ev_lst[-1].msg.time
            debug(f"Timeline count: {count}, / total_count: {total_count}, first_tick: {first_tick}, last_tick: {last_tick}", writing_file=True)
        # Show the results
        nb_ev = 100
        debug(f"First {nb_ev} items in timeline in ev_lst", writing_file=True)
        ev_lst = tim.get_list()
        for i, ev in enumerate(ev_lst[:nb_ev]): debug(f"{i}, tick: {ev.msg.time}, tracknum: {ev.tracknum}", writing_file=True)
        debug(f"\nGroup Event Position time count: {len(tim.group_time_lst)}", writing_file=True)
        for (i, item) in enumerate(tim.group_time_lst[:nb_ev]): debug(f"index Group: {i}, Pos: {item[0]}, Tick: {item[1]}", writing_file=True)
        if debugging: _DEBUG =1

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
        set the Sequence position
        from MidiSequence object
        """

        if self.parent is None: return
        state = self.parent._playing
        if state:
            # self.parent.stop_engine()
            pass
        
        if pos == -1: pos = self.curpos
        seq_len = self.get_length()
        pos = limit_value(pos, 0, seq_len)
        self.update_tracks_position(pos) 
        # Sets the timeline position
        tim = self._timeline
        tim.update_track_pos(pos)
        self.curpos = pos
        if state:
            # self.parent.start_midi_engine()
            pass
           
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
        self.curpos =pos
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
                # debug(msg_str, title, writing_file=True)
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
                            # debug(msg_str, title, writing_file=True)
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
        debug("Liste complete", writing_file=True)
        for msg in msg_lst:
            debug("Type: {}, Note: {}, Time: {}".format(msg.type, msg.note, msg.time), writing_file=True)
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
        TODO: this function can be replaced by tick2bar in MidiBase object
        convert pos in tick to bar
        from MidiSequence
        """
 
        if pos == -1: pos = self.get_position()
        
        bar = self.base.bar
        (nb_bars, nb_ticks) = divmod(pos, bar)
        ppq = self.base.ppq
        (nb_beats, nb_ticks) = divmod(nb_ticks, ppq)

        nb_bars +=1 # for user friendly
        nb_beats +=1
        # nb_ticks +=1
        
        return (nb_bars, nb_beats, nb_ticks)
    
    #-----------------------------------------

    def get_ppq(self):
        """
        Returns the PPQ or number of Ticks per beat
        from MidiSequence object
        """
 
        return self.base.ppq
   
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
        if track is None: return
        type = "set_tempo"
        ev = track.search_ev(type, time)
        if ev:
            ev.msg.tempo = int(val)
            pass
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

        self.format_type = int(self.mid.type)
        self.base.ppq = int(self.mid.ticks_per_beat)
        self.base.file_name = filename
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
                    if msg.time == 0:
                        self.base.tempo = int(msg.tempo)
                    # print(f"voici tempo: {msg.tempo}, time: {msg.time}")
                    # print("ticks_per_beat or ppq: {}".format(self.ppq))
                    # print(f"track: {tracknum}, Tempo: {msg.tempo}")
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
                    if msg.time == 0:
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
                track.gen_group_pos()
                res =1
            self.track_lst.append(track)
            self.track_names.append(names)
            
        if res:
            bpm = self.base.tempo2bpm(self.base.tempo)
            self.click_track = self.metronome.init_click(bpm)
            self.gen_timeline()
            # self.set_bpm(bpm)
            # self.base.update_tempo_params()
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

        ret = self.metronome.change_bpm(bpm)
        if ret > 0:
            # print("je passe ici")
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

    def get_next_ev_list(self):
        """
        Note: Deprecated function
        returns next event sorted list of all tracks
        from MidiSequence object
        """

        ev_lst = []
        for track in self.track_lst:
            ev = track.get_next_ev()
            if ev: ev_lst.append(ev)
        # sorting the event list
        if ev_lst:
            ev_lst.sort(key=lambda x: x.msg.time)

        return ev_lst

    #-----------------------------------------

    def get_next_ev_pos(self):
        """
        Note: Deprecated function
        returns the minimum next event time from the sorting ev list on all tracks
        from MidiSequence object
        """

        if self._next_pos >=0: return self._next_pos
        ev_lst = self.get_next_ev_list()
        if not ev_lst: return -1
        self._next_pos = ev_lst[0].msg.time
        
        return self._next_pos

    #-----------------------------------------

    def get_next_group_pos_list(self):
        """
        Note: Deprecated function
        returns next group ev position  sorted list of all tracks
        from MidiSequence object
        """

        ev_lst = []
        for track in self.track_lst:
            pos = track.get_next_group_pos()
            if pos >=0: ev_lst.append(pos)
        # sorting the event list
        if ev_lst:
            ev_lst.sort()

        return ev_lst

    #-----------------------------------------

    def get_next_group_pos(self):
        """
        Note: Deprecated function
        returns the minimum next group position from the sorting group list position
        from MidiSequence object
        """

        if self._next_pos >=0: return self._next_pos
        group_lst = self.get_next_group_pos_list()
        print(f"voici group_lst: {group_lst}")
        if not group_lst: return -1
        self._next_pos = group_lst[0]
        
        return self._next_pos

    #-----------------------------------------


    def get_playable_data(self, curtick):
        """
        returns playable midi event list
        from MidiSequence object
        """

        msg_lst = []
        log.debug(f"\nFunc: get_playable_data, at curtick: {curtick}", bell=0)
        
        """
        if not self._bpm_changed and curtick >= 1024 * 4:
            # log.debug(f"[bpm_change], at turtick: {curtick}")
            type = evq.EVENT_BPM_CHANGED
            value = 60
            _evq_instance.push_event(type, value)
            self._bpm_changed =1
        """

        for (tracknum, track) in enumerate(self.track_lst):
            # Note: Used, when we have a list of group time, for playing in realtime
            ev_lst = track.search_ev_group_time(curtick)
            # ev_lst = track.search_ev_group(curtick)
            
            """
            if not ev_lst: 
                log.debug(f"No ev_lst at curtick: {curtick}, on tracknum {tracknum}", writing_file=True)
            else: 
                log.debug(f"Len ev_lst: {len(ev_lst)},  at curtick: {curtick}, on tracknum {tracknum}", writing_file=True)
            """

            for (index, ev) in enumerate(ev_lst):
                # log.debug(f"msg: {ev.msg}", writing_file=True)
                
                """
                if ev.msg.type == "set_tempo":
                    self.old_tempo = self.base.tempo
                    new_tempo = ev.msg.tempo
                    if abs(self.old_tempo - new_tempo) >= 1000:
                    # if (curtick - self._last_pos) >= 256:
                        self._last_pos = curtick
                        self.old_tempo = new_tempo
                        self.base.tempo = new_tempo

                        self.base.update_tempo_params()
                        # msec = self.base.tick2sec(ev.msg.time)
                        bpm = self.base.tempo2bpm(self.old_tempo)
                        # debug(f"[tempo_change]: {new_tempo}, bpm: {bpm:.3f}, at tick: {ev.msg.time}")
                        type = evq.EVENT_BPM_CHANGED
                        value = bpm
                        # _evq_instance.push_event(type, value)
                """

                # print(f"Type Set_tempo, tempo: {ev.msg.tempo}, bpm: {bpm:.3f}, msec: {msec:.3f}")
                if ev.msg.type in self.base.playable_lst:
                    """
                    # not work
                    if self.base.tempo != self.old_tempo:
                        self.base.tempo = self.old_tempo
                        # self.base.update_tempo_params()
                        # self.set_position(-1)
                        pass
                    """

                    newev = MidiEvent()
                    newev.msg = ev.msg.copy()
                    newev.tracknum = tracknum
                    msg = newev.msg
                    # TODO: We rolling the timeline in time so, we need to convert tick to sec???
                    # Not necessary
                    # msg.time = self.base.tick2sec(msg.time)
                    # log.debug("voici msg: {}".format(msg))
                    msg_lst.append(newev)
             
        if not msg_lst:
            log.debug(f"No msg_lst, at curtick: {curtick}\n", bell=0)
        else:
            log.debug(f"msg_lst len: {len(msg_lst)}, at curtick: {curtick}\n", bell=0)
       
        return msg_lst

    #-----------------------------------------

    def get_properties(self):
        """
        returns properties midi file
        from MidiSequence object
        """
        
        nb_tracks = len(self.track_lst)
        msg = f"File name: {self.base.file_name}, Format type: {self.base.format_type},\n"\
                f"Number of tracks: {nb_tracks}, PPQ or Ticks Per Beat: {self.base.ppq},\n"\
                f"Bpm: {self.base.bpm:.2f}, Tempo: {self.base.tempo}, timesignature: {self.base.numerator}/{self.base.denominator},\n"\
                f"Sec per beat: {self.base.sec_per_beat:.3f}, Sec per tick: {self.base.sec_per_tick:.3f}, Tick per sec: {self.base.tick_per_sec}"
        return msg

    #-----------------------------------------

#========================================

if __name__ == "__main__":
    seq = MidiSequence()
    seq.init_sequencer()
    input("It's OK")
#-----------------------------------------
