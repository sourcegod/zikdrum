#! /usr/bin/python3
"""
    dialog.py:
    Version 0.2
    Update: dimanche, 14/05/17
    See changelog

    
    Rapid dialog boxes
    Date: mardi, 13/12/16
    Author: Coolbrother
"""

import sys, os, time
import curses
import readline, glob
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8') # for french
code = locale.getpreferredencoding()
# ids for dialog box
ID_OK =100
ID_CANCEL =102
ID_YES =106
ID_NO =108
DEBUG =1

def debug(msg="", title="", bell=True, write_file=False):
    if DEBUG:
        if msg and title:
            print("{}: {}".format(title, msg))
        elif msg:
            print("{}".format(msg))

        if bell:
            curses.beep()
#------------------------------------------------------------------------------

def beep():
    curses.beep()

#-------------------------------------------

class EditBox():
    """ test edibox with curses and unicode """
    def __init__(self):
        self.stdscr = curses.initscr()
        curses.noecho() # don't repeat key hit at the screen
        curses.cbreak()
        # curses.raw() # for no interrupt mode like suspend, quit
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        self.ypos =0; self.xpos =0
        self.height, self.width = self.stdscr.getmaxyx()
        self.maxX = self.width -1
        self.win = curses.newwin(self.height, self.width, self.ypos, self.xpos)
        self.win.refresh()
        self.win.keypad(1) # allow to catch code of arrow keys and functions keys
        self.buf = ""
        self.edl =0 # end of line
        self.completing =0
        self.index =0
        self.txt = ""

    #-------------------------------------------

    def print_info(self, msg="", title=""):
        # print message
        self.win.erase()
        self.win.addstr(0, 0, "%s %s" %(title, msg))
        # self.win.getch()

    #-------------------------------------------

    def close_win(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    #-------------------------------------------

    def beep(self):
        curses.beep()

    #-------------------------------------------
    
    def set_text(self, msg, mode=0):
        # mode 0 add text and 1 insert text
        size = len(self.buf) + len(msg)
        if (len(msg) > 0 and size <= self.maxX):
            self.edl = size
            if (self.edl >= self.maxX): 
                self.edl = self.maxX
            if not mode:
                self.win.addstr(self.ypos, self.xpos, msg)
                self.buf += msg
                self.xpos = self.edl
            else:
                self.win.insstr(self.ypos, self.xpos, msg)
                self.buf = self.buf[:self.xpos] +msg + self.buf[self.xpos:]
                self.xpos +=1
            try:
                self.win.move(self.ypos, self.xpos)
                self.win.refresh()
            except curses.error:
                self.xpos =0
                self.win.move(self.ypos, self.xpos)
                self.win.refresh()
                self.beep()
        
    #-------------------------------------------
    
    def set_complete(self, text, state=0):
        # return (glob.glob(text+'*')+[None])[state]
        lst = []
        l_dir = [] 
        l_file = []
        name = ""
        for name in glob.glob(text+'*'):
            if os.path.isdir(name):
                name = name+'/'
                l_dir.append(name)
            else:
                l_file.append(name)
            l_dir.sort()
            l_file.sort()


        l_dir.extend(l_file)
        
        return l_dir

    #-------------------------------------------

    def print_complete(self, msg):
        size = len(msg)
        self.win.erase()
        self.xpos =0
        self.win.addstr(self.ypos, self.xpos, msg)
        self.buf = msg
        self.edl = size
        self.xpos = self.edl
        try:
            self.win.move(self.ypos, self.xpos)
            self.win.refresh()
        except curses.error:
            self.xpos =0
            self.win.move(self.ypos, self.xpos)
            self.win.refresh()
            self.beep()
    
    #-------------------------------------------
        
    def update(self):
        # pdate cursor 
        try:
            self.win.move(self.ypos, self.xpos)
            self.win.refresh()
        except curses.Error:
            self.xpos =0
            self.win.move(self.ypos, self.xpos)
            self.win.refresh()
            self.beep()

    #-------------------------------------------

    def reset_complete(self):
        # init completion variables
        self.completing =0
        self.state =0
        self.txt = ""

    #-------------------------------------------

    def edit_text(self, msg=""):
        # msg = "coucou la planete"
        # msg = unicode(msg, 'utf-8').encode('utf-8')
        old_msg = msg
        state =0
        txt = ""
        self.set_text(msg, 0) # add text
        while (1):
            ch = self.win.getch()
            if ch == curses.KEY_ENTER or ch == 10 : 
                self.beep()
                self.win.erase()
                break
            elif ch >= 32 and ch < 256:
                key = chr(ch)
                self.set_text(str(key), 1) # insert text
                self.reset_complete()
            elif ch == curses.KEY_LEFT : 
                if self.xpos > 0: 
                    self.xpos -= 1
                    self.update()
                else: self.beep()
            elif ch == curses.KEY_RIGHT : 
                if self.xpos < self.edl and self.edl <= self.maxX: 
                    self.xpos += 1
                    self.update()
                else: self.beep()
            elif ch == curses.KEY_UP or ch == curses.KEY_DOWN : 
                old_x = self.xpos; old_y = self.ypos
                self.win.erase()
                self.ypos = 0; self.xpos=0
                self.set_text(self.buf, 0)
                self.ypos = old_y; self.xpos = old_x
                self.update()
                self.beep()
            elif ch == curses.KEY_BACKSPACE: 
                if self.xpos > 0 and self.edl > 0:
                    if self.xpos == 1:
                        msg = self.buf[0]
                        self.buf = self.buf[1:]
                    else: 
                        self.buf = self.buf[:self.xpos-1] + self.buf[self.xpos:]
                    self.edl -=1
                    self.xpos -=1
                    self.win.delch(self.ypos, self.xpos)
                    self.reset_complete()
                else: self.beep()
            elif ch == 4 or ch == curses.KEY_DC: # ctrl-D or DEL for delete character
                try:
                    self.buf = self.buf[:self.xpos] + self.buf[self.xpos+1:]
                except IndexError:
                    pass
                if (self.xpos < self.edl):
                    self.win.delch(self.ypos, self.xpos)
                    self.edl -=1
                else: self.beep()
            elif ch == curses.KEY_HOME or ch == 1: # cltr-A
                self.xpos=0
                self.win.move(self.ypos, self.xpos)
            elif ch == curses.KEY_END or ch == 5: # ctrl-E
                self.xpos = self.edl
                self.win.move(self.ypos, self.xpos)
                self.reset_complete()
            elif ch == 11: # ctrl-K
                if self.xpos < self.edl:
                    self.buf = self.buf[:self.xpos]
                    self.win.clrtoeol()
                    self.edl = self.xpos
                else: self.beep()
            elif ch == 21: # ctrl-U
                if self.xpos > 0 :
                    self.buf = self.buf[self.xpos:]
                    self.xpos -=1
                    for i in range(self.xpos, -1, -1):
                        self.win.delch(self.ypos, self.xpos)
                        if self.edl > 0:
                            self.edl -=1
                        self.xpos -=1
                    self.xpos=0
                else: self.beep()
            elif ch == 27: # escape
                self.beep()
                self.win.erase()
                return ""
                break
            elif ch == 9: # tab
                if not self.completing:
                    self.txt = self.buf
                    old_txt = self.txt
                    lst = []
                    self.state =0
                    lst = self.set_complete(self.txt)
                    if (len(lst) > 1):
                        self.beep()
                    self.completing =1
                if (len(lst) == 0):
                    self.beep()
                elif (len(lst) == 1):
                    st = (lst[self.state])
                    if (st == self.txt):
                        self.beep()
                    else:
                        self.print_complete(st) # insert mode
                        self.reset_complete()
                else: # for len lst > 1
                    lst.append(old_txt)
                    if (self.state < len(lst)):
                        st = (lst[self.state])
                        self.print_complete(st)
                        self.state +=1
                    if (self.state >= len(lst)):
                        self.state =0
                        self.beep()
            elif ch == 20: # ctrl-T
                # to debug
                msg = "voici : %s, %s" %(self.buf, self.txt)
                self.print_info(msg)
            
            else: pass

        return self.buf

    #-------------------------------------------

#========================================

class ItemBase(object):
    """ Item base manager """
    def __init__(self):
        self.items = [None]
        self.index =0

    #-----------------------------------------

    def items(self):
        """
        returns items
        from ItemType object
        """

        return self.items
    
    #-----------------------------------------

    def set_items(self, items):
        """
        set item list
        from ItemBase object
        """

        self.items = items
    
    #-----------------------------------------

    def get_item(self):
        """
        returns current item
        from ItemType object
        """
        
        try:
            res = self.items[self.index]
        except IndexError:
            res = None

        return res
    
    #-----------------------------------------

    def search_index(self, val):
        """
        returns index of val in the list of tuple
        from ItemBase object
        """

        res =0
        for (ind, item) in enumerate(self.items):
            if item[0] == val:
                res = ind
                break
        
        return res

    #-----------------------------------------
 
    def check_value(self, val, left_lim=0, right_lim=100):
        """
        returns value between left_lim and right_lim range
        from ItemType object
        """

        if val <= left_lim: val = left_lim
        elif val >= right_lim: val = right_lim

        return val

    #-----------------------------------------
    
    def set_index(self, val):
        """
        change index
        from ItemBase object
        """
        
        if self.items:
            len1 = len(self.items) -1
            self.index = self.check_value(val, 0, len1)
    
    #-----------------------------------------

    def change_item(self, step=0, adding=0, min_val=0, max_val=-1):
        """
        changing item generic
        from ItemBase object
        """

        changing =0
        val =0
        if max_val == -1: # last  value
            max_val = len(self.items) -1
        if adding == 0:
            if step == -1:
                step = max_val
        else: # adding value
            val = self.index + step
            changing =1
        if changing:
            step = self.check_value(val, min_val, max_val)
        if self.index != step:
            self.index = step
        else: # no change for item num
            pass
        
        return self.items[self.index]

    #-------------------------------------------
  
#========================================

class ItemType(ItemBase):
    """ Item box manager """
    def __init__(self):
        super().__init__()
        self.id =0
        self.type =0
        self.title = ""
        self.items = [None]
        self.index =0

    #-----------------------------------------

    def id(self):
        """
        returns id
        from ItemType object
        """

        return self.id
    
    #-----------------------------------------

    def type(self):
        """
        returns type
        from ItemType object
        """

        return self.type
    
    #-----------------------------------------

    def title(self):
        """
        returns title
        from ItemType object
        """

        return self.title
    
    #-----------------------------------------

#========================================

class DialogBox(ItemBase):
    """ Dialog Box manager """
    def __init__(self):
        super().__init__()
        self.stdscr = curses.initscr()
        curses.noecho() # don't repeat key hit at the screen
        self.ypos =0; self.xpos =0
        self.height, self.width = self.stdscr.getmaxyx()
        self.win = curses.newwin(self.height, self.width, self.ypos, self.xpos)
        self.win.refresh()
        self.win.keypad(1) # allow to catch code of arrow keys and functions keys

        self.items = []
        self.index =0
        self.result =0
        self.style = [] # for style buttons like: Ok, Cancel
        self.wintitle = "Dialog Box"

        
        # listbox 1
        lb1 = ItemType()
        lb1.id =0
        lb1.type =0 # type list box
        lb1.title = "Listbox1"
        lb1.items = range(10)

        
        # Listbox 2
        lb2 = ItemType()
        lb2.id =1
        lb2.type =0 # type list box
        lb2.title = "Listbox2"
        lb2.items = range(10, 20)

        # Ok button
        bt1 = ItemType()
        bt1.id =ID_OK
        bt1.type =1 # type button
        bt1.title = "Button"
        bt1.items = ["Ok"]

        # Cancel button
        bt2 = ItemType()
        bt2.id =ID_CANCEL
        bt2.type =1 # type button
        bt2.title = "Button"
        bt2.items = ["Cancel"]
        # create style box
        self.style = [bt1, bt2]
        
        # add items 
        self.items.append(lb1)
        self.items.append(lb2)

    #-------------------------------------------
    
    def init(self):
        """
        init dialog box
        from DialogBox object
        """
        
        if self.style:
            self.items.extend(self.style)

    #-------------------------------------------

    def set_style(self, style):
        """
        set style list
        from DialogBox object
        """

        self.style = style
    
    #-----------------------------------------

    
    def display(self, msg=""):
        """
        display message 
        from DialogBox object
        """

        self.win.move(0, 0)
        self.win.clrtobot()
        self.win.addstr(3, 0, "                                                           ")
        self.win.addstr(3, 0, str(msg))
        self.win.move(3, 0)
        self.win.refresh()

    #-------------------------------------------

    def tabkey(self, step=0, adding=0):
        """
        manage tabkey
        from DialogBox
        """
        
        # debug("voici index: {}".format(self.index))
        if step == 1 and self.index == len(self.items) -1:
            # pass to first item
            item = self.change_item(step=0, adding=0)
            # self.index =0
        elif step == -1 and self.index == 0:
            # pass to last item
            item = self.change_item(step=step, adding=0)
            # self.index = len(self.items) -1
        else:
            item = self.change_item(step=step, adding=adding)

        val = item.get_item()
        msg = "{}: {}".format(item.title, val)
        self.display(msg)

    #-------------------------------------------

    def cursorkey(self, step=0, adding=0):
        """
        manage cursor keys like arrow keys
        from DialogBox
        """
        
        item = self.get_item()
        val = item.change_item(step=step, adding=adding)
        self.display(val)

    #-------------------------------------------

    def update(self):
        """
        update dialog box
        from DialogBox object
        """

        item = self.get_item()
        # if not isinstance(item, int):
        val = item.get_item()
        msg = "{}: {}".format(item.title, val)
        self.display(msg)

    #-------------------------------------------

    def show(self):
        """
        show dialog 
        from DialogBox object
        """
        
        # self.wintitle = "Dialog Box"
        self.display(self.wintitle)
        self.update()
        self.key_handler()
        
        return self.result
    
    #-------------------------------------------

    def close(self):
        """
        close dialog
        from DialogBox object
        """
        
        msg = "Closing Dialog"
        self.display(msg)

    #-------------------------------------------

    def key_handler(self):
        """
        manage keystroke
        from DialogBox object
        """

        while 1:
            key = self.win.getch()
            if key >= 32 and key < 128:
                key = chr(key)
            if key == 'Q': # 'Q' or escape
                # self.beep()
                self.result = ID_CANCEL
                self.close()
                break
            elif key == 9: # Tab key
                self.tabkey(step=1, adding=1)
            elif key == 10: # Enter key
                item = self.get_item()
                self.result = item.id
                self.close()
                break
            elif key == 27: # Escape for key
                key = self.win.getch()
                if key >= 32 and key < 128:
                    key = chr(key)
                if key == 9: # Alt+Tab
                    msg = "Alt+Tab"
                    self.tabkey(step=-1, adding=1)
                elif key == 27: # Alt+Escape
                    self.close()
                    break
            elif key == curses.KEY_UP:
                self.cursorkey(step=-1, adding=1)
            elif key == curses.KEY_DOWN:
                self.cursorkey(step=1, adding=1)

    #-------------------------------------------
         
#========================================

if __name__ == "__main__":
    ed = EditBox()
    text = ed.edit_text("Tapez votre texte")
    print("voici text: {}".format(text))
    dlg = DialogBox()
    dlg.init()
    dlg.show()
