#!/usr/bin/python3
"""
    File: midimanager.py:
    Module midi device and FluidSynth manager 
    Date: Mon, 04/07/2022
    Author: Coolbrother
"""

import time
import fluidsynth
import mido
from constants import * # for patch_lst


class MidiFluid(object):
    """ fluidsynth manager """
    def __init__(self):
        self.fs = None
        self.sfid = None

    #-----------------------------------------
    
    def init_synth(self, filename, audio_device=""):
        """
        init Fluidsynth
        from MidiFluid object
        """

        if not audio_device:
            audio_device = "hw:0" # for default audio device
        # increasing gain for more audio output volume
        # default: 0.2
        audio_driver = "alsa"
        
        # audio_device = "sysdefault"
        # audio_device = "hw:0"
        # audio_device = "hw:1"
        gain =3
        gain=1
        self.fs = fluidsynth.Synth(gain=gain)
        self.fs.start(driver=audio_driver, device=audio_device)
        # print(f"voici filename: {filename}")
        filename = "/home/com/banks/sf2/fluidr3_gm.sf2"
        self.sfid = self.fs.sfload(filename, update_midi_preset=0)
        # chan, sfid, bank, preset
        # bank select 128 for percussion
        self.fs.program_select(0, self.sfid, 0, 0)
        # self.fs.bank_select(0, 128)

    #-----------------------------------------

    def close_synth(self):
        """ 
        close fluidsynth 
        """
        if self.fs:
            self.fs.delete()

    #-----------------------------------------

    def play_notes(self):
        """
        test for fluidsynth
        from MidiFluid object
        """

        """
        # self.fs.bank_select(0, 0)
        self.fs.noteon(9, 60, 100)
        time.sleep(0.5)
        self.fs.noteon(9, 62, 100)
        time.sleep(0.5)
        self.fs.noteon(9, 64, 100)
        time.sleep(0.5)
        """

   
        if self.fs is None: 
            print("Error: No Synth Engine")
            return
        
        self.fs.program_change(0, 16)
        self.fs.noteon(0, 60, 100)
        time.sleep(1.0)
        self.fs.noteon(0, 67, 100)
        time.sleep(1.0)
        self.fs.noteon(0, 76, 100)

        time.sleep(1.0)

        self.fs.noteoff(0, 60)
        self.fs.noteoff(0, 67)
        self.fs.noteoff(0, 76)

        time.sleep(1.0)

    #-----------------------------------------

#========================================

class MidiManager(object):
    """ Midi manager from mido module """
    def __init__(self, parent=None):
        self.parent = parent
        self.synth_type =0
        self.synth = None
        self.chan =0
        self.midi_in = None
        self.midi_out = None

    #-----------------------------------------

    def init_midi(self, synth_type=0, bank_filename="", audio_device=""):
        """
        init synth 
        from MidiManager object
        """

        self.synth_type = synth_type
        if self.synth_type == 0:
            self.open_output(2)
        else:
            self.synth = MidiFluid()
            self.synth.init_synth(bank_filename, audio_device)
            # set channel 9 for drum percussion

    #-----------------------------------------

    def close_midi(self):
        if self.synth_type == 1:
            self.synth.close_synth()

    #-----------------------------------------

    def print_ports(self):
        """
        print input and output ports through mido driver
        from MidiManager object
        """

        print("Input Midi Ports:")
        names = mido.get_input_names()
        for (i, item) in enumerate(names): print(f"{i}: {item}")
        
        print("Output Midi Ports:")
        names = mido.get_output_names()
        for (i, item) in enumerate(names): print(f"{i}: {item}")

    #-----------------------------------------
    def get_in_ports(self):
        return mido.get_input_names()

    #-----------------------------------------

    def get_out_ports(self):
        return mido.get_output_names()

    #-----------------------------------------

    def send_to(self, msg, port=0):
        output_names = mido.get_output_names()
        port_name = output_names[port]
        out_port = mido.open_output(port_name)
        out_port.send(msg)

    #-----------------------------------------

    def open_input(self, port=0):
        """
        open midi input port
        from MidiManager object
        """

        input_names = mido.get_input_names()
        try:
            port_name = input_names[port]
            self.midi_in = mido.open_input(port_name)
        except IndexError:
            print("Error opening midi input Port {}".format(port))
        
        return self.midi_in

    #-----------------------------------------

    def open_output(self, port=0):
        """
        open midi output port
        from MidiManager object
        """

        output_names = mido.get_output_names()
        try:
            port_name = output_names[port]
            self.midi_out = mido.open_output(port_name)
        except IndexError:
            print("Error opening midi output Port {}".format(port))
        
        return self.midi_out

    #-----------------------------------------


    def get_message_blocking(self, port=0):
        # Get incoming messages - blocking interface
        input_names = mido.get_input_names()
        port_name = input_names[port]
        in_port = mido.open_input(port_name)
        for msg in in_port: 
            print("\a") 
            print(msg)

    #-----------------------------------------

    def send_message(self, msg):
        """
        send incomming message to fluidsynth
        from MidiManager object
        """
        
        # print("Message in:", msg)
        type = msg.type
        bank =0
        if self.synth_type == 0:
            if self.midi_out:
                self.midi_out.send(msg)
        else:
            fs = self.synth.fs
            if type in ['note_on', 'note_off']:
                chan = msg.channel
                
                note = msg.note
                msg.velocity =100
                vel = msg.velocity
                args = [chan, note, vel]
            if type == "note_on":
                fs.noteon(self.chan, msg.note, msg.velocity)
            elif type == "note_off":
                fs.noteoff(self.chan, msg.note)
            elif type == "program_change":
                fs.program_change(self.chan, msg.program)
            elif type == "control_change":
                fs.cc(self.chan, msg.control, msg.value)
            elif type == "pitchwheel":
                fs.pitch_bend(self.chan, msg.pitch)

        # notify toplevel application
        """
        if self.parent:
            self.parent.notify(msg)
        """

    #-----------------------------------------

    def output_message(self, msg):
        """
        output playback message to fluidsynth 
        distinguishing message channel
        from MidiManager object
        """
        
        # print("Message in:", msg)
        type = msg.type
        bank =0
        if self.synth_type == 0:
            if self.midi_out:
                self.midi_out.send(msg)
        else:
            fs = self.synth.fs
            chan = msg.channel
            if type in ['note_on', 'note_off']:
                chan = msg.channel
                
                note = msg.note
                msg.velocity =100
                vel = msg.velocity
                args = [chan, note, vel]
            if type == "note_on":
                fs.noteon(chan, msg.note, msg.velocity)
            elif type == "note_off":
                fs.noteoff(chan, msg.note)
            elif type == "program_change":
                fs.program_change(chan, msg.program)
            elif type == "control_change":
                fs.cc(self.chan, msg.control, msg.value)
            elif type == "pitchwheel":
                fs.pitch_bend(self.chan, msg.pitch)

        # notify toplevel application
        """
        if self.parent:
            self.parent.notify(msg)
        """

    #-----------------------------------------

    def input_callback(self, msg):
        """
        incomming messages callback
        from MidiManager object
        """

        self.send_message(msg)

    #-----------------------------------------

    def receive_from(self, port=0, callback=None):
        """
        Get incoming messages - nonblocking interface
        with cb_func as callback
        """
        portname = ""

        inputnames = mido.get_input_names()
        try:
            portname = inputnames[port]
        except IndexError:
            print("Error: Midi input Port {} is not available".format(port))
        
        if portname:
            inport = mido.open_input(portname)
            # or we can pass the callback function at the opening port:
            # in_port = mido.open_input(port_name, callback=cb_func)
            if callback:
                inport.callback = callback
        
    #-----------------------------------------

    def program_change(self, chan, program):
        """
        set program change
        from MidiManager object
        """
        
        if self.synth_type == 0 and self.midi_out:
            msg = mido.Message(type='program_change')
            msg.channel = chan
            msg.program = program
            self.midi_out.send(msg)
        else:
           if self.synth.fs:
               self.synth.fs.program_change(chan, program)
               # input callback function
        self.chan = chan

    #-----------------------------------------

    def bank_change(self, chan, bank):
        """
        change bank
        from MidiManager object
        """
        
        if self.synth_type == 0 and self.midi_out:
            msg = mido.Message(type='control_change')
            msg.channel = chan
            msg.value = bank
            self.midi_out.send(msg)
        else:
            if self.synth.fs:
                self.synth.fs.bank_select(chan, bank)

    #-----------------------------------------
        
    def panic(self, chan=-1):
        """
        set all notes off controller on al channels
        from MidiManager object
        """

        control = 123 # all notes off
        if self.synth_type == 0 and self.midi_out:
            msg = mido.Message(type='control_change')
            msg.channel =0
            msg.control = control
            msg.value =0
            if chan == -1: # all channels
                for chan in range(16):
                    msg.channel = chan
                    self.midi_out.send(msg)
            else:
                msg.channel = chan
                self.midi_out.send(msg)

        else: # synth_type = 0
            if self.synth.fs:
                if chan == -1:
                    for chan in range(16):
                        self.synth.fs.cc(chan, control, 0)
                else:
                    self.synth.fs.cc(chan, control, 0)

    #-----------------------------------------

    def note_on(self, chan, note, vel):
        """
        set Note On
        from MidiManager object
        """
        
        if self.synth_type == 0 and self.midi_out:
            msg = mido.Message(type='note_on')
            msg.channel = chan
            msg.note = note
            msg.velocity = vel
            self.midi_out.send(msg)
        else:
           if self.synth.fs:
               self.synth.fs.noteon(chan, note, vel)
               # input callback function
        self.chan = chan

    #-----------------------------------------

    def note_off(self, chan, note):
        """
        set Note Off
        from MidiManager object
        """
        
        if self.synth_type == 0 and self.midi_out:
            msg = mido.Message(type='note_off')
            msg.channel = chan
            msg.note = note
            self.midi_out.send(msg)
        else:
           if self.synth.fs:
               self.synth.fs.noteoff(chan, note)
               # input callback function
        self.chan = chan

    #-----------------------------------------


    def play_notes(self):
        """
        Test notes
        from MidiManager object
        """

        if self.synth_type == 0:
            self.program_change(0, 16)
            self.note_on(0, 60, 100)
            time.sleep(1.0)
            self.note_off(0, 60)
            self.note_on(0, 67, 100)
            time.sleep(1.0)
            self.note_on(0, 76, 100)

            time.sleep(1.0)

            self.note_off(0, 60)
            self.note_off(0, 67)
            self.note_off(0, 76)
            time.sleep(1.0)


        elif self.synth_type == 1:
            if self.synth: self.synth.play_notes()


    #-----------------------------------------

#========================================

if __name__ == "__main__":
    mid = MidiManager()
    mid.init_midi("")

