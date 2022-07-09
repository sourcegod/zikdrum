#! /usr/bin/env python3
"""
    File: zikdrum.py
    See changelog

    Version 0.9
    Last update: Wed, 06/07/2022

    Update: samedi, 19/08/17
    See changelog

    Date: jeudi, 25/08/16    
    Author:
    Coolbrother

"""

import sys
import time
import curses
import dialog as dlg
import interfaceapp as intapp
import utils as uti
import constants as cst

help = """
       Menu : Octave    Channel    Patch
        Use Key Left/Right to change menu, Key Up/Down to change menu item,
        Ctrl+F Filter On,
        Shift+F Filter Off,
        Escape to quit.
        """

#-------------------------------------------

class Empty(object):
    """ """
    def __init(self):
        pass
    
    #-------------------------------------------

    def empty(self):
        """
        """

    #-------------------------------------------

#========================================
   
class MainApp(object):
    def __init__(self):
        self.stdscr = curses.initscr()
        curses.noecho() # don't repeat key hit at the screen
        # curses.cbreak()
        # curses.raw() # for no interrupt mode like suspend, quit
        curses.start_color()
        curses.use_default_colors()
        self.ypos =0; self.xpos =0
        self.height, self.width = self.stdscr.getmaxyx()
        self.win = curses.newwin(self.height, self.width, self.ypos, self.xpos)
        self.win.refresh()
        self.win.keypad(1) # allow to catch code of arrow keys and functions keys
        # self.win.nodelay(1)

        self.octave_num =4
        self.octave_lst = range(-4, 8)
        self.nbnote =12 # notes per octave
        self.channel_num =0 # for channel 1
        self.channel_lst = [] # containing channel object
        self.patch_num =0
        self.volume =0

        self.menu_names = [
                    # 'Octave', 
                    'Track',
                    'Channel',
                    'Bank', 'Preset',
                    'Patch',
                    ]
        self.menu_num =0
        self.menuitem =0
        self.menu_lst = [
                    # self.octave_menu,
                    self.track_menu,
                    self.channel_menu,
                    self.bank_menu, self.preset_menu,
                    self.patch_menu,
                    ]

        self.curmenu = self.menu_lst[self.menu_num]
        self.midi_man = None
        self.player = None
        self.iap = None
        self.notifying =0
        self.bank_lst = ["0 (MSB)", "32 (LSB)"]
        self.bank_num =0
        self.preset_lst = range(128)
        self.msb_preset_num =0
        self.lsb_preset_num =0
        self.bank_select_num =0 # result of: (msb_preset_num + msb_preset_num*128)
        self.bank_select_lst = [0, 128] # bank select allowed
        self.preset_modified =0
        self.new_patch_lst = range(128) # empty patch
        self.filename = "/home/com/banks/sf2/FluidR3_GM.sf2"
        # self.filename = "/home/banks/sf2/Yamaha_XG_Sound_Set.sf2"
        # not work with fluidsynth 1.1.6
        # self.filename = "/home/banks/sf2/OmegaGMGS.sf2"
        self.msg_home = "Grovit Synth..."
        self.window_num =0

    #-------------------------------------------
    
    def display(self, msg=""):
        self.win.clrtobot()
        self.win.addstr(3, 0, "                                                           ")
        self.win.addstr(3, 0, str(msg))
        self.win.move(3, 0)
        self.win.refresh()
        # self.beep()

    #-------------------------------------------

    def display_status(self, msg=""):
        self.win.clrtobot()
        self.win.move(22, 0) # bottom of screen
        self.win.addstr(22, 0, str(msg))
        self.win.move(22, 0) # bottom of screen

    #-------------------------------------------

    def display_menu(self):
        self.win.addstr(0, 0, str(help))
        self.win.move(0, 0)
        self.win.refresh()

    #-------------------------------------------

    def beep(self):
        curses.beep()

    #-------------------------------------------

    def notify(self, msg):
        """
        receive notification
        from MainApp object
        """

        if self.notifying:
            self.display(msg)

    #-------------------------------------------

    def switch_notifier(self):
        """
        active or not notification
        from MainApp object
        """

        self.notifying = not self.notifying
        if self.notifying:
            msg = "Notification enabled"
        else:
            msg = "Notification disabled"
        self.display(msg)

    #-------------------------------------------

    def print_ports(self):
        """
        print midi driver ports
        from MainApp object
        """
        inports = self.midi_man.get_in_ports()
        outports = self.midi_man.get_out_ports()
        msg = "Input ports: {} \nOutports: {}".format(inports, outports)
        self.display(msg)

    #-------------------------------------------

    def get_menu_num(self):
        """ 
        returns menu number
        """
        
        return self.menu_num

    #-------------------------------------------

    def select_menu(self, step=0, adding=0):
        """
        select menu by index
        """
        
        self.menu_num = self.change_menu(self.menu_num, self.menu_names, 
                step, adding)
        menu_name = self.menu_names[self.menu_num]
        bank_name = self.bank_lst[self.bank_num]
        if self.bank_num == 0:
            preset_num = self.msb_preset_num
        else:
            preset_num = self.lsb_preset_num
        patch_name = cst._gm_patch_lst[self.patch_num]
        self.curmenu = self.menu_lst[self.menu_num]
        if menu_name == "Channel":
            msg = "Menu {}: {}".format(menu_name, self.channel_num+1)
        elif menu_name == "Bank":
            msg = "Menu {}: {}".format(menu_name, bank_name)
        elif menu_name == "Preset":
            msg = "Menu {}: {}".format(menu_name, preset_num)
        elif menu_name == "Patch":
            msg = "Menu {}: {} - {}".format(menu_name, self.patch_num, patch_name)
        else:
            msg = "Menu {}".format(menu_name)
        self.display(msg)

    #-------------------------------------------

    def change_menu(self, menu_num, menu_lst, step=0, adding=0):
        """
        changing menu generic
        """

        changing =0
        val =0
        max_val = len(menu_lst) -1
        if adding == 0:
            if step == -1:
                step = max_val
        else: # adding value
            val = menu_num + step
            changing =1
        if changing:
            step = uti.limit_value(val, 0, max_val)
        if menu_num != step:
            menu_num = step
        else: # no change for menu num
            self.beep()
        
        return menu_num

    #-------------------------------------------

    def octave_menu(self, step=0, adding=0):
        """
        select octave menu by index
        """
        
        self.octave_num = self.change_menu(self.octave_num, self.octave_lst, step, adding)
        msg = "Octave : {}".format(self.octave_lst[self.octave_num])
        self.display(msg)

    #-------------------------------------------

    def track_menu(self, step=0, adding=0):
        """
        select track menu by index
        from MainApp object
        """
        
        self.iap.change_tracknum(step, adding)    

    #-------------------------------------------

    def channel_menu(self, step=0, adding=0):
        """
        select channel menu by index
        from MainApp object
        """
        
        # the result is displays by the app interface
        self.iap.change_channel(step, adding)
        # getting the message information from InterfaceApp object
        
    #-------------------------------------------
    
    def bank_menu(self, step=0, adding=0):
        """
        change bank type
        from MainApp object
        """

        self.iap.change_bank(step, adding)

    #-------------------------------------------

    def preset_menu(self, step=0, adding=0):
        """
        change bank preset
        from MainApp object
        """
     
        self.iap.change_preset(step, adding)

    #-------------------------------------------

    def patch_menu(self, step=0, adding=0):
        """
        select patch menu by index
        """
        
        self.iap.change_patch(step, adding)


    #-------------------------------------------

    def close_win(self):
        curses.nocbreak()
        self.win.keypad(0)
        curses.echo()

    #-------------------------------------------

    def test(self):
        """
        test function
        from MainApp object
        """
        # testing track 1
        tracknum =1
        # track = self.player.get_track(tracknum)
        # count = track.count()
      
    #------------------------------------------------------------------------------
   
    def on_open_file(self):
        """
        open midi file
        from MainApp object
        """

        msg = "Open file - Dialog"
        self.display(msg)
        filedialog = dlg.EditBox()
        filename = filedialog.edit_text()
        # filename containing the input text
        # test filename
        self.iap.open_file(filename)
           
    #-------------------------------------------

    def on_change_bpm(self):
        """
        change bpm dialog
        from MainApp object
        """

        bpm = self.iap.curseq.get_bpm()
        ed = dlg.EditBox()
        msg = "Tapez un nombre"
        self.display(msg)
        bpm = ed.edit_text(str(bpm))
        self.iap.change_bpm(bpm)
        self.update()

    #-------------------------------------------
    
    def on_goto_bar(self):
        """
        goto bar dialog
        from MainApp object
        """

        (bar, beat, tick)  = self.iap.curseq.get_bar()
        ed = dlg.EditBox()
        msg = "Tapez un nombre"
        self.display(msg)
        bar = ed.edit_text(str(bar))
       
        self.iap.goto_bar(bar)
        self.update()

    #-------------------------------------------


    def on_save_dialog(self):
        """
        save midi file dialog
        from MainApp object
        """

        msg = "Save file - Dialog"
        self.display(msg)
        filedialog = dlg.EditBox()
        filename = filedialog.edit_text()
        # filename containing the input text
        # test filename
        self.iap.save_file(filename)
        self.update()


    #-------------------------------------------

    def on_quantize_dialog(self):
        """
        quantize dialog
        from MainApp object
        """
       
        reso = self.player.quan_res
        # input list
        lb1 = dlg.ItemType()
        lb1.id =0
        lb1.type =0 # type list box
        lb1.title = "Quantize Listt"
        lb1.items = [1,2,4,6,8,12,16,24,32,48,64]
        ind = lb1.items.index(reso)
        lb1.set_index(ind) # index list
        items = [lb1] # must be list of list 
        # get_item returns a tuple with input_device_index and name of device 
        item = lb1.get_item()
        box = dlg.DialogBox()
        box.set_items(items)
        box.init()
        res = box.show()
        if res != dlg.ID_CANCEL:
            # inputnum is the input device index by Portaudio, and inputind is the index in the input list
            item = lb1.get_item()
            ind = lb1.index
            type=0; tracknum=-1; reso = item
            self.iap.quantize_track(type, tracknum, reso)
        self.update()

    #-------------------------------------------

    def update(self):
        """
        update the interface
        from MainApp object
        """
        msg = self.msg_home
        time.sleep(0.5)
        self.display(msg)

    #-------------------------------------------

    def key_handler(self):
        msg = self.msg_home
        self.display(msg)
        # curses.beep() # to test the nodelay function
        while 1:
            key = self.win.getch()
            if key == 27: # escape
                key = self.win.getch()
                if key >= 32 and key < 128:
                    key = chr(key)
                if self.iap.window_num == 1: # event window
                    if key == ' ': # alt+space
                        self.iap.play_ev()
                    elif key == 'n': # alt+n
                        # change note group
                        self.iap.change_note_group(1)
                    elif key == 'p': # alt+p
                        # change note group
                        self.iap.change_note_group(-1)
                    elif key == 'P': # alt+P
                        # playing notes group with timing
                        self.iap.curseq.play_note_group(timing=1)
                if key == 'I': # Alt+I
                    # insert tempo track
                    self.iap.curseq.insert_tempo_track()
                    msg = "Insert Tempo Track"
                elif key == '0': # alt+0
                    self.iap.change_window(0)
                elif key == '1': # alt+2
                    self.iap.change_window(1)
                    # self.player.set_track_events()
                elif key == 'D': # alt+D
                    # debug
                    self.iap.player.print_ev()
                elif key == 'f': # alt+f
                    # filter notes
                    self.iap.filter_notes(-1, "C1", "C8")
                elif key == 'F': # alt+F
                    # move notes
                    tracknum =-1; start_note = "C5"; end_note = "C8"
                    self.iap.curseq.move_notes(tracknum, start_note, end_note)
                elif key == 'z': # alt+z
                    # quantize dialog
                    self.on_quantize_dialog()
                continue                
            elif key >= 32 and key < 128:
                key = chr(key)
            if key == 'Q': 
                self.beep()
                self.iap.close_app()
                self.close_win()
                break
            elif  key == 'b':
                # forward to next bar
                self.iap.forward()
            elif  key == 'B':
                # forward to 10 next bar
                self.iap.forward(10)
            elif key == 'D':
                # erase track whole track
                self.iap.erase_track(tracknum=-1, startpos=0, endpos=-1)
            elif key == 'e': 
                # add current track to the selection
                self.iap.add_track_selection(-1)
            elif key == 'E': 
                # delete current track to the selection
                self.iap.del_track_selection(-1)
            elif  key == 'i':
                # set left locator
                self.iap.set_left_locator()
            elif  key == 'I':
                # set start loop
                self.iap.set_start_loop()
            elif  key == 'k':
                # toggle clicking
                self.iap.toggle_click()
            elif  key == 'l':
                # toggle loop
                self.iap.toggle_loop()
            elif  key == 'o':
                # set right locator
                self.iap.set_right_locator()
            elif  key == 'O':
                # set end loop
                self.iap.set_end_loop()
            elif  key == ' ' or key == '0': # space
                # play pause
                self.iap.play_pause()
                # msg = self.iap.get_message()
            elif  key == 'r': 
                # toggle record
                self.iap.toggle_record()
            elif key == 's':
                # toggle solo
                self.iap.toggle_solo()
            elif  key == 'T':
                # change the bpm
                self.on_change_bpm()
            elif key == 'T':
                # Todo: change the shortcut key
                # desarm track
                self.iap.arm_track(tracknum=-1, armed=0)
            elif  key == 'u':
                # display status
                self.iap.print_status()
            elif  key == 'U':
                # Redo
                self.iap.redo()
            elif  key == 'v':
                # stop
                self.iap.stop()
            elif  key == 'V':
                # paste merge
                self.iap.paste_merge()
            elif  key == 'w':
                # rewind to prev bar
                self.iap.rewind()
            elif  key == 'W':
                # rewind to 10 prev bar
                self.iap.rewind(10)
            elif  key == 'x':
                # toggle mute
                self.iap.toggle_mute()
            elif  key == 'z':
                # toggle autoquantize
                self.iap.toggle_quantize()
            elif  key == 'Z':
                # quantize
                self.iap.quantize()
            elif key == '<':
                # goto start
                self.iap.goto_start()
            elif key == '>':
                # goto end
                self.iap.goto_end()
            elif key == ',': 
                # select current track
                self.iap.change_cur_track()
            elif key == '?': # 
                # unselect current track
                self.iap.unselect_cur_track()
            elif key == 1: # ctrl +A
                # select all tracks
                self.iap.change_all_tracks()
            elif key == 4: # Ctrl+D
                # cut track to the clipboard
                self.iap.cut_to_clip()
            elif key == 5: # Ctrl+E
                # arm track
                self.iap.arm_track(tracknum=-1, armed=1)
            elif key == 7: # Ctrl+G
                # goto bar
                self.on_goto_bar()
            elif key == 11: # ctrl+K
                # delete whole track
                self.iap.delete_track(tracknum=-1)
            elif key == 15: # ctrl+O
                # open midi file
                self.on_open_file()
                self.update()
            elif key == 16: # ctrl+P
                # get midi file properties
                self.iap.print_info()
            elif key == 20: # ctrl+T
                self.iap.test()
                # self.test()
            elif key == 21: # Ctrl+U
                # Undo
                self.iap.undo()
            elif key == 22: # Ctrl+v
                # paste replace
                self.iap.paste_replace()
            elif key == 23: # ctrl+W
                # save midi file
                self.on_save_dialog()
            elif key == 24: # ctrl+X
                # erase to clipboard
                self.iap.erase_to_clip()
            elif key == 25: # ctrl+Y
                # copy to clipboard
                self.iap.copy_to_clip()
            elif key == curses.KEY_LEFT:
                if self.window_num == 0:
                    self.select_menu(step=-1, adding=1)

            elif key == curses.KEY_RIGHT:
                if self.window_num == 0:
                    self.select_menu(step=1, adding=1)
            elif key == curses.KEY_UP:
                if self.iap.window_num == 0:
                    self.curmenu(step=-1, adding=1)
                else: 
                    self.iap.change_one_ev(step=-1, adding=1)
            elif key == curses.KEY_DOWN:
                if self.iap.window_num == 0:
                    self.curmenu(step=1, adding=1)
                else: 
                    self.iap.change_one_ev(step=1, adding=1)
            elif key == curses.KEY_DC: # Delete
                # delete event
                self.iap.delete_event()
            elif key == '.' or key == curses.KEY_F12: # dot, F12
                # panic
                self.iap.panic()
            elif key == curses.KEY_HOME:
                # goto left locator
                self.iap.goto_left_locator()
            elif key == curses.KEY_END:
                # goto right locator
                self.iap.goto_right_locator()
            elif key == curses.KEY_PPAGE:
                if self.iap.window_num == 1:
                    # change note group
                    self.iap.change_note_group(-1)
                else:
                    self.curmenu(step=-25, adding=1)
            elif key == curses.KEY_NPAGE:
                if self.iap.window_num == 1:
                    # change note group
                    self.iap.change_note_group(1)
                else:
                    self.curmenu(step=25, adding=1)
            
            elif key == '1':
                if self.iap.window_num == 1:
                    self.iap.change_one_ev(step=-1, adding=1)
            elif key == '2':
                if self.iap.window_num == 1:
                    self.iap.play_one_ev()
            elif key == '3':
                if self.iap.window_num == 1:
                    self.iap.change_one_ev(step=1, adding=1)
            elif key == '4':
                if self.iap.window_num == 1:
                    self.iap.change_note_group(-1, timing=0)
            elif key == '5':
                if self.iap.window_num == 1:
                    # playing notes group with no timing
                    self.iap.play_note_group(timing=0)
            elif key == '6':
                if self.iap.window_num == 1:
                    self.iap.change_note_group(1, timing=0)
            elif key == '7':
                if self.iap.window_num == 1:
                    self.iap.change_note_group(-1, timing=1)
            elif key == '8':
                if self.iap.window_num == 1:
                    # playing notes group with timing
                    self.iap.play_note_group(timing=1)
            elif key == '9':
                if self.iap.window_num == 1:
                    self.iap.change_note_group(1, timing=1)



            elif key == curses.KEY_F2:
                if self.iap.window_num == 1:
                    self.iap.play_ev()
            elif key == curses.KEY_F3:
                if self.iap.window_num == 1:
                    # playing notes group with no timing
                    self.iap.curseq.play_note_group(timing=0)
            elif key == curses.KEY_F4:
                if self.iap.window_num == 1:
                    # playing notes group with timing
                    self.iap.curseq.play_note_group(timing=1)


            elif key == curses.KEY_F7:
                self.iap.change_window(0)
            elif key == curses.KEY_F8:
                self.iap.change_window(1)
            elif key == curses.KEY_F9:
                self.iap.test_synth_engine()
                """
                # log info 
                self.iap.log_info(type=0)
                self.iap.log_info(type=1)
                """

            elif key == curses.KEY_F11: # not working
                self.iap.test_synth_engine()


            # self.update()
            # msg = self.iap.get_message()
            # self.display(msg)

    #-------------------------------------------
    
    def main(self, midi_filename="", audio_device=""):
        """ 
        main function 
        from MainApp object
        """
        
        self.iap = intapp.InterfaceApp(self)
        self.notifying =1
        self.iap.init_app(midi_filename, audio_device)
        self.key_handler()

    #-------------------------------------------

#========================================

if __name__ == "__main__":
    midi_filename = ""
    audio_device = "" # hw:0 by default
    app = MainApp()
    if len(sys.argv) >= 2:
        midi_filename = sys.argv[1]
    if len(sys.argv) >= 3:
        audio_device = sys.argv[2]
        # print("voici filename", filename)
    app.main(midi_filename, audio_device)
    

#------------------------------------------------------------------------------
