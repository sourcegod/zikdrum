#python3
"""
    File: miditools.py
    Module for midi tools objects.
    Last update: Tue, 04/07/2023
    Date: Mon, 04/07/2022
    Author: Coolbrother
"""
import copy
import midiplayer as midplay
import midisequence as midseq

def merge_dict(dic1, dic2):
    """
    merge two dictionnaries for python 3
    """
    dic = dic1.copy() # make a shallow copy
    # add new dict
    dic.update(dic2)
    
    return dic

#------------------------------------------------------------------------------



class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        
        return cls._instance

    #-------------------------------------------

#========================================

class UndoManager(object):
    """ undo manager """
    def __init__(self):
        """
        Undo manager object
        """

        self.items = []
        self.index =0
        self.level =0 # undo level
        self.title = "" # current title

    #-----------------------------------------

    def init(self):
        """
        init item list
        from UndoManager object
        """
    
        self.items = []
        self.level =0
        self.index =0
        self.title = ""
    
    #-----------------------------------------

    def get_count(self):
        """
        returns items count
        from UndoManager object
        """
        
        return len(self.items)
    
    #-----------------------------------------

    def set_prev(self):
        """
        set previous item in the list
        returns a tuple of item
        from UndoManager object
        """

        title = ""        
        player = None
        if self.index > 0:
            try:
                self.index -= 1
                (title, player) = self.items[self.index]
            except IndexError:
                pass

        return (title, player)

    #-----------------------------------------

    def set_next(self):
        """
        set next item in the list
        returns a tuple of item
        from UndoManager object
        """

        title = ""        
        player = None
        if self.index < len(self.items) -1:
            try:
                self.index += 1
                (title, player) = self.items[self.index]
            except IndexError:
                pass

        return (title, player)

    #-----------------------------------------

    def add_undo(self, title, item):
        """ 
        add a tuple item to the list
        from UndoManager object
        """
        
        count = self.get_count()
        if self.index < count -1:
            self.items = self.items[:self.index+1]
            # debug("voici len list: %d" %(len(lst)))
        
        self.items.append((title, item))
        self.index = self.get_count() -1
        self.level = self.get_count() # length of the object list
        self.title = title
        # debug("voici undo_count: %d, index: %d" %(self.level, self.index))

    #-----------------------------------------

    def prev_undo(self):
        """ 
        undo the current player in the list
        and move to previous player in the list
        returns a tuple of item object
        from UndoManager object
        """

        title = ""        
        player = None
        if self.level >= 1:
            (title, player) = self.set_prev()
            if player:
                self.level -=1
                self.title = title
        # debug("voici undo_count: %d, index: %d" %(self._level, self.item_index))

        return (title, player)
    
    #-----------------------------------------

    def next_undo(self):
        """ 
        move to next player in the list
        and redo the next player
        returns a tuple of item object
        from UndoManager object
        """

        title = ""        
        player = None
        if self.level < self.get_count():
            (title, player) = self.set_next()
            if player:
                self.level += 1
                self.title = title
        # debug("voici undo_count: %d, index: %d" %(self._level, self.item_index))

        return (title, player)

    #-----------------------------------------

#========================================

class MidiTools(Singleton):
    """ Tools midi manager """
    def __init__(self):
        pass

    #-----------------------------------------

    def duplicate_evs_obj(self, ev_lst):
        """
        copy event list
        returns new_evs list
        from tools object
        """
        if not ev_lst:
            return
        
        new_evs = []
        for ev in ev_lst:
            evt = midseq.MidiEvent()
            evt.__dict__ = merge_dict(evt.__dict__, ev.__dict__)
            evt.msg = ev.msg.copy()
            
            # adding event
            new_evs.append(evt)

        return new_evs
    
    #-------------------------------------------
    
    def duplicate_tracks_obj(self, track_lst):
        """
        duplicate track object list
        returns new_tracks object
        from Tools object
        """
        
        if not track_lst:
            return
        
        new_tracks = []
        for track in track_lst:
            trk = midseq.MidiTrack()
            trk.__dict__ = merge_dict(trk.__dict__, track.__dict__)
            # init track parts
            trk.ev_lst = []
            ev_lst = track.ev_lst
            new_evs = self.duplicate_evs_obj(ev_lst)
            if new_evs:
                trk.add_evs(*new_evs)
            # debug("voici new_track: %s" %(new_track))
            new_tracks.append(trk)

        return new_tracks

    #-------------------------------------------

    def duplicate_seq_obj(self, seq):
        """ 
        copy sequence
        from MidiTools object
        """

        if seq:
            new_seq = midseq.MidiSequence()
            new_seq.__dict__ = merge_dict(new_seq.__dict__, seq.__dict__)
            
            track_lst = seq.track_lst
            new_tracks = self.duplicate_tracks_obj(track_lst)
            new_seq.track_lst = new_tracks
            new_seq.base = copy.deepcopy(seq.base)

        return new_seq

    #-----------------------------------------

    def duplicate_player_obj(self, player):
        """ 
        copy player
        from MidiTools object
        """

        if player:
            new_player = midplay.MidiPlayer()
            new_player.__dict__ = merge_dict(new_player.__dict__, player.__dict__)
            
            curseq = player.curseq
            new_seq = self.duplicate_seq_obj(curseq)
            new_player.curseq = new_seq
            

            # debug("voici len track_lst: {}".format(len(new_player.track_lst)))    
        return new_player

    #-----------------------------------------

    def get_track_range(self, track, start_pos, end_pos):
        """
        return track range index event between start_pos and end_pos
        from MidiTools object
        """
        
        val1 = track.search_pos(start_pos)
        val2 = track.search_lastpos(end_pos)
        
        # debug("first_pos: {}, last_pos: {}".format(val1, val2))

        return (val1, val2)

    #-------------------------------------------

    def get_evs_range(self, track, start_pos=0, end_pos=-1):
        """
        returns events list from start_pos and end_pos
        from MidiTools object
        """

        res =0
        new_evs = []
        if track:
            ev_lst = track.get_list()
            if start_pos == 0 and end_pos == 0:
                return new_evs
            elif start_pos >= end_pos and end_pos != -1:
                return new_evs
            
            if end_pos == -1:
                end_pos = len(ev_lst) -1
            (start_ind, end_ind) = self.get_track_range(track, start_pos, end_pos)
            if start_ind and end_ind != -1:
                try:
                    new_evs = ev_lst[start_ind:end_ind]
                except IndexErro:
                    pass
            
        return new_evs

    #-----------------------------------------

    def get_max_track(self, track_lst):
        """ 
        returns index and length of the  maximum track for the track list
        from MidiTools object
        """

        idx =-1
        ilen =0
        lst = []
        for (i, track) in enumerate(track_lst):
            track_len = track.get_length()
            lst.append((i, track_len))
        if lst:
            res  = max(lst, key=lambda x: x[1])
            # we starting at index =1
            (idx, ilen) = res
        
        return (idx, ilen)
    
    #-----------------------------------------

    def is_max_track(self, track_lst):
        """ 
        whether there is a maximum length track in the track list
        from MidiTools object
        """

        res =0
        if len(track_lst) <= 1:
            return res
        
        track_ref = track_lst[0]
        ref_len = track_ref.get_length()
        for (i, track) in enumerate(track_lst):
            track_len = track.get_length()
            if ref_len != track_len:
                res =1
                break
       
        return res
    
    #-----------------------------------------

    def clean_tracks(self, track_lst):
        """
        clean the end_of_track and markers MARK_ZZZ event on the tracks
        from MidiTools object
        """

        res =0
        for track in track_lst:
            ev_lst = track.get_list()
            if ev_lst:
                last_ev = ev_lst[-1]
                type1 = "end_of_track"
                type2 = "marker"
                msg = last_ev.msg
                if msg.type != type1:
                    new_ev = midplay.MidiEvent(type=type1, cat=1)
                    new_ev.msg.time = msg.time
                    ev_lst.append(new_ev)
                    last_ev = new_ev
                    res =1
                i=0
                while i < len(ev_lst):
                    ev = ev_lst[i]
                    msg = ev.msg
                    if (msg.type == type1 and i < len(ev_lst) -1) or\
                    (msg.type == type2 and i<len(ev_lst)):
                        del ev_lst[i]
                        res =1
                        i -=1
                    i +=1

        return res

    #-----------------------------------------

    def adjust_tracks(self, track_lst):
        """
        adjust tracks length for a track list 
        to get all tracks same length
        from MidiTools object
        """
        
        res =0
        self.clean_tracks(track_lst)
        if not self.is_max_track(track_lst):
            return
        
        (id_max, max_len) = self.get_max_track(track_lst)
        max_track = track_lst[id_max]
        # debug("voici curpos: %.2f, et id_max: %d" %(curpos, id_max))
        for (i, track) in enumerate(track_lst):
            if track != max_track:
                track_len = track.get_length()
                if track_len < max_len:
                    # calculate the delta time for the new track
                    time_dur = max_len - track_len
                    # debug("voici time_dur: %d" % time_dur)
                    # changing the time of EndOfTrack event
                    ev_lst = track.get_list()
                    if ev_lst:
                        last_ev = ev_lst[-1]
                        msg = last_ev.msg
                        if msg.type == "end_of_track":
                            msg.time += time_dur
                            res =1
        return res

    #-----------------------------------------

    def reduce_tracks(self, track_lst):
        """
        reduce tracks length for a track list 
        to reduce all tracks when deleting
        from MidiTools object
        """
        
        res =0
        type1 = "end_of_track"
        # self.clean_tracks(track_lst)
        for (i, track) in enumerate(track_lst):
            # changing the time of EndOfTrack event
            ev_lst = track.get_list()
            if len(ev_lst) == 1:
                ev1 = ev_lst[-1]
                msg1 = ev1.msg
                if msg1.type == type1 and msg1.time !=0:
                    msg1.time =0
                    res =1
            # not necessary
            """
            elif len(ev_lst) > 1:
                ev1 = ev_lst[-1]
                ev2 = ev_lst[-2]
                msg1 = ev1.msg
                msg2 = ev2.msg
                if msg1.type == type1 and msg1.time != msg2.time:
                    msg1.time = msg2.time
                    res =1
            """

        return res

    #-----------------------------------------

  #========================================

class MidiTrackEdit(object):
    """ Midi Editor manager """
    def __init__(self):
        self.tools = MidiTools()

    #-------------------------------------------

    def shift_one_ev_to_left(self, ev_lst, ev_ind, step):
        """
        move just one event start of a track
        from MidiTrackEdit object
        """

        if ev_lst:
            ev_lst[ev_ind].msg.time -= step
        
    #-------------------------------------------

    def shift_one_ev_to_right(self, ev_lst, ev_ind, step):
        """
        move just one event to end of a track
        from MidiTrackEdit object
        """

        if ev_lst:
            ev_lst[ev_ind].msg.time += step
        
    #-------------------------------------------

    def shift_evs_to_left(self, ev_lst, ev_ind, step):
        """
        move all evs ofset of a ev list from ev index ev_ind to left to step in time
        from MidiTrackEdit object
        """

        if ev_lst:
            for i in range(ev_ind, len(ev_lst)):
                ev_lst[i].msg.time -= step

    #-------------------------------------------

    def shift_evs_to_right(self, ev_lst, ev_ind, step):
        """
        move all evs ofset of a ev list from ev index ev_ind to right to step in time
        from MidiTrackEdit object
        """

        if ev_lst:
            for i in range(ev_ind, len(ev_lst)):
                ev_lst[i].msg.time  += step

    #-------------------------------------------
          
    def shift_track_to_left(self, track, ev_ind, step):
        """
        move all evs ofset of a track from ev index ev_ind to left to step in time
        We can pass any track, not only track in the track list of midi player
        from MidiTrackEdit object
        """

        if track:
            ev_lst = track.get_list()
            for i in range(ev_ind, len(ev_lst)):
                ev_lst[i].msg.time  -= step
        
    #-------------------------------------------
     
    def shift_track_to_right(self, track, ev_ind, step):
        """
        move all evs ofset of a track from ev index ev_ind to right to step in time
        We can pass any track, not only track in the track list of midi player
        from MidiTrackEdit object
        """

        if track:
            ev_lst = track.get_list()
            for i in range(ev_ind, len(ev_lst)):
                ev_lst[i].msg.time  += step
        
    #-------------------------------------------
    
    def shift_track_to_zero(self, track):
        """
        move the first ev to zero and move all next evs ofset belong the first ev in time
        We can pass any track, not only track in the track list of midi player
        from MidiTrackEdit object
        """

        if track:
            ev_lst = track.get_list()
            step = ev_lst[0].msg.time
            if step > 0:
                for i in range(len(ev_lst)):
                    ev_lst[i].msg.time  -= step
    
    #-------------------------------------------

    def delete_events(self, ev_lst, start_ind, end_ind):
        """
        delete events except end_of_track events
        from MidiTrackEdit object
        """

        res =0
        if ev_lst:
            type = "end_of_track"
            # note: faster way to remove items in a list while iterating
            ev_lst[start_ind:end_ind] = [ev for (i, ev) in enumerate(ev_lst[start_ind:end_ind], start_ind) if ev.msg.type == type]
            
        return res

    #-------------------------------------------


    def add_copy_marks(self, track, start_pos, end_pos):
        """
        add copy markers to the copy track to keep the right length time selection 
        from MidiTrackEdit object
        """
        
        if track:
            ev_lst = track.get_list()
            # if ev_lst:
            type = "marker"
            # debug("event tempo not found")
            # start marker
            ev1 = midplay.MidiEvent(type=type, cat=1)
            ev1.msg.text = "MARK_ZZZ"
            ev1.msg.time = start_pos
            # end marker
            ev2 = midplay.MidiEvent(type=type, cat=1)
            ev2.msg.text = "MARK_ZZZ"
            ev2.msg.time = end_pos
            ev_lst.insert(0, ev1)
            ev_lst.append(ev2)

    #-------------------------------------------

    def copy_track(self, track, start_pos, end_pos):
        """
        copy track from start_pos to end_pos
        returns miditrack
        from MidiTrackEdit object
        """

        ev_lst = []
        new_track = None
        # track = self.get_track(tracknum)
        ev_lst = self.tools.get_evs_range(track, start_pos, end_pos)
        if ev_lst:
            ev_lst = self.tools.duplicate_evs_obj(ev_lst)
        new_track = MidiTrack()
        if ev_lst:
            new_track.add_evs(*ev_lst)
        # add markers to the copy to keep the right length selection
        self.add_copy_marks(new_track, start_pos, end_pos)
        self.shift_track_to_zero(new_track)
    
        return new_track

    #-----------------------------------------

    def arrange_events(self, track, start_pos, end_pos):
        """
        arrange midi events from start_pos to end_pos
        make place in event list,
        return: 
        ins_ind: the insert index point, 
        and ev_lst: the modified events
        from MidiTrackEdit object
        """
        
        ins_ind =-1 # for insert index
        start_ind =-1
        end_ind =-1
        # get_evs_range function returns only exact index at its time, not index for time between. Due to the midi event time
        ev_lst = track.get_list()
        (start_ind, end_ind) = self.tools.get_track_range(track, start_pos, end_pos)
        # debug("arrange_parts: start_pos: %d, end_pos: %d" %(start_pos, end_pos))
        # debug("arrange_parts: start_ind: %d, end_ind: %d" %(start_ind, end_ind))

        # whether there is no event
        if start_ind == -1 and end_ind == -1:
            return (-1, ev_lst)
        # whether end_pos is longer than events
        elif start_ind >= 0 and end_ind == -1:
            # getting event count from start_ind
            ev_count = len(ev_lst[start_ind:])
            if ev_count >0:
                end_ind = ev_count -1

        # whether there is one event
        if start_ind == end_ind:
            # ev = ev_lst[start_ind]
            # delete event except end_of_track event
            self.delete_events(ev_lst, start_ind, end_ind+1)
            # del ev_lst[start_ind]
            ins_ind = start_ind

        # whether there is multiple events
        elif start_ind != end_ind:
            ins_ind = start_ind
            # delete events except end_of_track event
            self.delete_events(ev_lst, start_ind, end_ind+1)
            
            """
            try:
                del ev_lst[start_ind:end_ind+1]
            except IndexError:
                debug("Index Error: deleting parts")
                pass
            """

       
        return (ins_ind, ev_lst)

    #-------------------------------------------

    def arrange_track(self, track, start_pos, end_pos):
        """
        arrange events in track from start_pos to end_pos
        make place in the track, then, insert events
        return: 
        ins_ind: the insert index point, 
        and ev_lst: the modified events
        from MidiTrackEdit object
        """
        
        ins_ind =-1 # for insert index
        ev_lst = None
        new_evs = None

        # track = self.get_track(tracknum)
        ev_lst = track.get_list()
        if ev_lst:
            # new_evs is events's track modified
            (ins_ind, new_evs) = self.arrange_events(track, start_pos, end_pos)

        return (ins_ind, track)

    #-------------------------------------------

    def cut_events_to_track(self, track_obj, start_pos, end_pos):
        """
        delete events in track, to shifting to left, from start_pos to end_pos
        from SequencePlayer object
        """

        (ins_ind, track) = self.arrange_track(track_obj, start_pos, end_pos)
        if ins_ind >=0:
            step = (end_pos - start_pos)
            # shift left events to
            self.shift_track_to_left(track, ins_ind, step)

    #-------------------------------------------
        
    def erase_events_to_track(self, track_obj, start_pos, end_pos):
        """
        replace  events in track from start_pos to end_pos
        from SequencePlayer object
        """

        (ins_ind, track) = self.arrange_track(track_obj, start_pos, end_pos)
        # no need to insert silence at ins_ind for midi events
        step = (end_pos - start_pos)

    #-------------------------------------------

    def replace_events_to_track(self, track_obj, curtrack, ins_pos, copy_mode=0):
        """
        replace eventss from clipboard to track, 
        from MidiTrackEdit object
        """

        new_evs = []
        adding_mode =0 # for adding events or insert
        # if track_obj is None:
        #    return
        ev_lst = track_obj.get_list()
        if ev_lst:
            # hard copy the clipboard content to not modify the original
            new_evs = self.tools.duplicate_evs_obj(ev_lst)
        if new_evs:
            last_pos = ev_lst[-1].msg.time
            if ins_pos >= last_pos:
                adding_mode =1
            start_pos = ins_pos
            end_pos = ins_pos + last_pos
            # delete events to be replaced
            (ins_ind, track) = self.arrange_track(curtrack, start_pos, end_pos)
            if ins_ind == -1:
                return
            self.shift_evs_to_right(new_evs, 0, ins_pos)
            if adding_mode:
                # adding events at the end of track
                track.add_evs(*new_evs)
            else:
                # insert events at ins_pos index
                track.insert_evs(ins_pos, new_evs)
            # sorting events by time
            track.sort()

    #-------------------------------------------

    def merge_events_to_track(self, track_obj, curtrack, ins_pos, copy_mode=0):
        """
        merge eventss from clipboard to track, 
        from MidiTrackEdit object
        """

        new_evs = []
        if track_obj is None:
            return
        ev_lst = track_obj.get_list()
        if ev_lst:
            # hard copy the clipboard content to not modify the original
            new_evs = self.tools.duplicate_evs_obj(ev_lst)
        if new_evs:
            self.shift_evs_to_right(new_evs, 0, ins_pos)
            # track = self.get_track(tracknum)
            if curtrack:
                curtrack.insert_evs(ins_pos, new_evs)
                # sorting events by time
                curtrack.sort()

    #-------------------------------------------

#========================================

class MidiSelector(object):
    """ selections manager """
    def __init__(self, player=None):
        self.player = None
        self.curseq = None
        self._tracks_sel = []
        if player:
            self.set_player(player)

    #-------------------------------------------

    def set_player(self, player):
        """
        set the player manager 
        from MidiSelector object
        """
    
        if player:
            self.player = player
            self.curseq = self.player.curseq

    #-------------------------------------------

    def get_tracks_selection(self):
        """
        return tracks selection
        from MidiSelector object
        """

        return self._tracks_sel

    #-------------------------------------------

    def set_tracks_selection(self, *tracks_sel):
        """
        set tracks selection
        from MidiSelector object
        """

        res =0
        if tracks_sel:
            self._tracks_sel = []
            self._tracks_sel.extend(tracks_sel)
            for track_ind in self._tracks_sel:
                track = self.curseq.get_track(track_ind)
                track.set_selected(1)
            res =1
        
        return res

    #-------------------------------------------

    def add_track_selection(self, tracknum):
        """
        adding track index to the tracks selection
        from MidiSelector object
        """

        res =0
        if tracknum == -1:
            tracknum = self.curseq.get_tracknum()
        if not tracknum in self._tracks_sel:
            self._tracks_sel.append(tracknum)
            track = self.curseq.get_track(tracknum)
            track.set_selected(1)
            self._tracks_sel.sort()
            res =1

        return (res, tracknum)

    #-------------------------------------------

    def del_track_selection(self, tracknum):
        """
        delete track number to the tracks selection
        from MidiSelector object
        """

        res =0
        if tracknum == -1:
            tracknum = self.curseq.get_tracknum()
        if tracknum in self._tracks_sel:
            self._tracks_sel.remove(tracknum)
            track = self.curseq.get_track(tracknum)
            track.set_selected(0)
            res =1

        return (res, tracknum)

    #-------------------------------------------

    def select_cur_track(self):
        """
        select current track
        from MidiSelector object
        """
        
        res =0
        tracknum = self.curseq.get_tracknum()
        if self.set_tracks_selection(tracknum):
            res =1

        return res

    #-------------------------------------------

    def unselect_cur_track(self):
        """
        unselect current track
        from MidiSelector object
        """
        
        res =0
        tracknum = self.curseq.get_tracknum()
        if self.del_track_selection(tracknum):
            res =1

        return res

    #-------------------------------------------

    def select_all_tracks(self):
        """
        select all tracks
        from MidiSelector object
        """
        
        res =0
        nb_tracks = self.curseq.get_nb_tracks()
        lst = [i for i in range(0, nb_tracks)]
        if self.set_tracks_selection(*lst):
            res =1

        return res

    #-------------------------------------------

    def unselect_all_tracks(self):
        """
        unselect all tracks
        from MidiSelector object
        """

        res =0
        nb_tracks = self.curseq.get_nb_tracks()
        for tracknum in range(0, nb_tracks):
            if self.del_track_selection(tracknum):
                res =1
        self._tracks_sel = []

        return res

    #-------------------------------------------

    def is_all_tracks_selected(self):
        """
        returns 1 whether all tracks are selected
        from MidiSelector object
        """
        
        res =0
        nb_tracks = self.curseq.get_nb_tracks()
        nb_sels = self.curseq.get_track_selections()
        if nb_tracks == nb_sels:
            res =1

        return res

    #-------------------------------------------

    def select_time(self, start_pos, end_pos=-1):
        """
        select time from start_pos to end_pos, 
        from MidiSelector object 
        """
        
        if end_pos == -1:
            track = self.curseq.get_track(-1) # current track
            end_pos = track.get_length()
        
        self.curseq.set_locators(start_pos, end_pos)

    #-------------------------------------------

    def select_all_time(self):
        """
        select all time 
        from MidiSelector object 
        """
        
        start_pos =0
        track = self.curseq.get_track(-1) # current track
        end_pos = track.get_length()
        self.select_time(start_pos, end_pos)

    #-------------------------------------------

#========================================

class MidiClipboard(object):
    """ clipboard manager """
    def __init__(self, player=None):
        self.player = None
        self.curseq = None
        self._clipboard = []
        self.trackedit = None
        self.tools = None
        if player:
            self.set_player(player)

    #-------------------------------------------

    def set_player(self, player):
        """
        set the player manager 
        from MidiClipboard object
        """
    
        if player:
            self.player = player
            self.curseq = self.player.curseq
            self.trackedit = self.player.trackedit
            self.tools = self.curseq.tools

    #-------------------------------------------

    def get_clipboard(self):
        """
        return the clipboard list 
        from MidiClipboard object
        """

        return self._clipboard

    #-------------------------------------------

    def set_clipboard(self, clip_lst):
        """
        set the clipboard list 
        from MidiClipboard object
        """

        if clip_lst:
            self._clipboard = clip_lst

    #-------------------------------------------
     
    def copy_to_clip(self, tracks_sel, start_pos, end_pos):
        """
        copy tracks to the clipboard 
        from MidiClipboard object
        """
        
        clip_lst = []
       
        if self.curseq:
            # tracks_sel = self.get_tracks_selection()
            # tracks_sel = [self.curseq.get_tracknum()]
            if not tracks_sel:
                return
            
            start_ind = tracks_sel[0]
            # hard copy tracks
            for (ind, tracknum) in enumerate(tracks_sel):
                curtrack = self.curseq.get_track(tracknum)
                track = self.trackedit.copy_track(curtrack, start_pos, end_pos)
                if track:
                    # re-ordering tracks from zero 
                    val = tracknum - start_ind
                    clip_lst.append((val, track))

            
            self.set_clipboard(clip_lst)
            
    #-------------------------------------------

    def erase_to_clip(self, tracks_sel, start_pos, end_pos):
        """
        erase tracks with blank and copy to the clipboard 
        from MidiClipboard object
        """
        
        if self.curseq:
            # tracks_sel = self.get_tracks_selection()
            # tracks_sel = [self.curseq.get_tracknum()]
            if not tracks_sel:
                return
            
            self.copy_to_clip(tracks_sel, start_pos, end_pos)
            for (ind, tracknum) in enumerate(tracks_sel):
                track = self.curseq.get_track(tracknum)
                self.trackedit.erase_events_to_track(track, start_pos, end_pos)
            track_lst = self.curseq.get_tracks()
            self.tools.adjust_tracks(track_lst)
            self.curseq.update_length()

    #-------------------------------------------

    def cut_to_clip(self, tracks_sel, start_pos, end_pos):
        """
        delete tracks and copy to the clipboard 
        from MidiClipboard object
        """
        
        all_selected =0
        if self.curseq:
            # tracks_sel = self.get_tracks_selection()
            # tracks_sel = [self.curseq.get_tracknum()]
            if not tracks_sel:
                return
            nb_tracks = self.curseq.get_nb_tracks()
            if nb_tracks == len(tracks_sel):
                all_selected =1
            self.copy_to_clip(tracks_sel, start_pos, end_pos)
            for (ind, tracknum) in enumerate(tracks_sel):
                track = self.curseq.get_track(tracknum)
                self.trackedit.cut_events_to_track(track, start_pos, end_pos)
            track_lst = self.curseq.get_tracks()
            if all_selected:
                self.tools.reduce_tracks(track_lst)
            self.tools.adjust_tracks(track_lst)
            self.curseq.update_length()

    #-------------------------------------------

    def paste_replace(self, ins_pos):
        """
        paste replace tracks from the clipboard from sequence player object
        """
        
        clip_lst = self.get_clipboard()
        if not clip_lst:
            return

        if self.curseq:
            # calculate the new track index bellong the clip track index
            nb_tracks = self.curseq.get_nb_tracks()
            tracknum = self.curseq.get_tracknum()
            for clip in clip_lst:
                clip_ind = clip[0]
                track_obj = clip[1]
                tracknum = tracknum + clip_ind
                if tracknum < nb_tracks:
                    # hard copy the clipboard
                    curtrack = self.curseq.get_track(tracknum)
                    self.trackedit.replace_events_to_track(track_obj, curtrack, ins_pos, copy_mode=1)
                else:
                    
                    """
                    # create new track ans paste on the new
                    self.curseq.new_tracks(1)
                    nb_tracks = self.curseq.get_nb_tracks()
                    tracknum = nb_tracks - 1
                    # debug("voici tracknum: %d, et nb_tracks: %d" %(tracknum, nb_tracks))
                    # return
                    # hard copy the clipboard
                    self.curseq.replace_parts_to_track(track_obj, tracknum, ins_pos, copy_mode=1)
                    """
            track_lst = self.curseq.get_tracks()
            self.tools.adjust_tracks(track_lst)
            self.curseq.update_length()


    #-------------------------------------------

    def paste_merge(self, ins_pos):
        """
        paste merge tracks from the clipboard 
        from SequencePlayer object
        """
        
        clip_lst = self.get_clipboard()
        if not clip_lst:
            return

        if self.curseq:
            # calculate the new track index bellong the clip track index
            nb_tracks = self.curseq.get_nb_tracks()
            tracknum = self.curseq.get_tracknum()
            for clip in clip_lst:
                clip_ind = clip[0]
                # track_obj is a track list
                track_obj = clip[1]
                tracknum = tracknum + clip_ind
                if tracknum < nb_tracks:
                    # hard copy the clipboard
                    curtrack = self.curseq.get_track(tracknum)
                    self.trackedit.merge_events_to_track(track_obj, curtrack, ins_pos, copy_mode=1)
                else:
                    
                    """
                    # create new track ans paste on the new
                    self.curseq.new_tracks(1)
                    nb_tracks = self.curseq.get_nb_tracks()
                    tracknum = nb_tracks - 1
                    # hard copy the clipboard
                    self.trackedit.merge_events_to_track(track_obj, tracknum, ins_pos, copy_mode=1)
                    """
                    
            track_lst = self.curseq.get_tracks()
            self.tools.adjust_tracks(track_lst)
            self.curseq.update_length()

    #-------------------------------------------

    def empty(self):
        """
        """

    #-------------------------------------------

#========================================

if __name__ == "__main__":
    tol = MidiTools()
    input("It's OK")
#-----------------------------------------
