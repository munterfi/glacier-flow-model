###############################################################################
# Glacier Flow Model - GUI
# Authors:          Merlin Unterfinger
# Date:             11.07.2017
###############################################################################

from Tkinter import *
import tkFileDialog, tkMessageBox
import ttk
from GlacierFlowModel import *


class App():
    def __init__(self, master):
        # Initalize
        self.master = master
        # Call start to initialize to create the UI elements
        self.start()
        self.GFM = None

    def start(self):
        self.master.title('Glacier Flow Model')

        # CREATE A TEXT/LABEL
        # Create a variable with text
        label01 = "Choose a digital elevation model (GeoTiff) to process:"
        label02 = "Set the change in temperature for the simulation:"
        label03 = "Save plots"
        label04 = "Choose folder to save the plots:"
        label_fill = ""

        # Put "label01" in "self.master" which is the window/frame
        # Then, put in the first row (row=0) and in the 2nd column (column=1), align it to "West"/"W"
        Label(self.master, text=label01).grid(row=0, column=0, sticky=W)
        Label(self.master, text=label02).grid(row=6, column=0, sticky=W)
        Label(self.master, text=label03).grid(row=10, column=0, sticky=W)
        Label(self.master, text=label04).grid(row=11, column=0, sticky=W)
        Label(self.master, text=label_fill).grid(row=2, column=0, sticky=W)
        Label(self.master, text=label_fill).grid(row=5, column=0, sticky=W)
        # Label(self.master, text=label_fill).grid(row=8, column=0, sticky=W)


        # CREATE A TEXTBOX
        self.filelocation = Entry(self.master)
        self.filelocation["width"] = 60
        self.filelocation.focus_set()
        self.filelocation.grid(row=1, column=0)

        # CREATE A BUTTON WITH "ASK TO OPEN A FILE"
        self.open_file = Button(self.master, text="Browse...",
                                command=self.browse_file)  # see: def browse_file(self)
        self.open_file.grid(row=1,
                            column=1)  # put it beside the filelocation textbox

        # CREATE A TEXTBOX2
        self.filelocation2 = Entry(self.master)
        self.filelocation2["width"] = 60
        self.filelocation2.focus_set()
        self.filelocation2.grid(row=13, column=0)

        # CREATE A BUTTON WITH "ASK TO SAVE A FILE"
        self.save_file = Button(self.master, text="Browse...",
                                command=self.browse_file_save)  # see: def browse_file(self)
        self.save_file.grid(row=13,
                            column=1)  # put it beside the filelocation textbox

        # CREATE RADIO BUTTONS
        RADIO_BUTTON1 = [
            ("Yes", True),
            ("No", False),
        ]

        # Initialize a variable to store the selected value of the radio buttons
        # Set it to A by default
        self.radio_var1 = StringVar()
        self.radio_var1.set(False)

        # Create a loop to display the RADIO_BUTTON
        i = 0
        for text, item in RADIO_BUTTON1:
            # setup each radio button. variable is set to the self.radio_var
            # and the value is set to the "item" in the for loop
            self.radio1 = Radiobutton(self.master, text=text,
                                      variable=self.radio_var1, value=item)
            self.radio1.grid(row=10, column=i + 1)
            i += 1

        self.w = Scale(self.master, from_=-15, to=15, length=480,
                       resolution=0.5, orient=HORIZONTAL)
        # self.w["width"] = 60
        self.w.focus_set()
        self.w.grid(row=7, column=0)

        # BUTTONS
        # Load dem button
        self.submit_load = Button(self.master, text="Load DEM",
                                  command=self.load_dem, fg="red", width=10)
        self.submit_load.grid(row=3, column=0, sticky=W)
        # Steady state button
        self.submit_steady = Button(self.master, text="Steady state",
                                    command=self.steady_state, fg="red",
                                    width=10)
        self.submit_steady.grid(row=4, column=0, sticky=W)
        # Steady state button
        self.submit_simulate = Button(self.master, text="Simulation",
                                      command=self.simulate, fg="red",
                                      width=10)
        self.submit_simulate.grid(row=8, column=0, sticky=W)

    def browse_file(self):
        # put the result in self.filename
        self.filename = tkFileDialog.askopenfilename(title="Open a file...")

        # this will set the text of the self.filelocation
        self.filelocation.insert(0, self.filename)

    def browse_file_save(self):
        # put the result in self.filename
        self.filename2 = tkFileDialog.askdirectory(title="Save as...")

        # this will set the text of the self.filelocation
        self.filelocation2.insert(0, self.filename2)

    def load_dem(self):
        # Close eventually excising plots
        plt.close()

        # Create new instance of GlacierFlowModel
        self.GFM = GlacierFlowModel(self.filename)
        Label(self.master, text='DEM loaded.').grid(row=3,
                                                    column=0,
                                                    sticky=W,
                                                    padx=120)

    def steady_state(self):
        # Reach steady state and print message
        message = self.GFM.reach_steady_state()
        Label(self.master, text=message).grid(row=4,
                                              column=0,
                                              sticky=W,
                                              padx=120)

    def simulate(self):
        # Simulate and print message
        message = self.GFM.simulate(temp_change=self.w.get())
        Label(self.master, text=message).grid(row=8,
                                              column=0,
                                              sticky=W,
                                              padx=120)

root = Tk()
root.lift()

# Separators
ttk.Separator(root, orient=HORIZONTAL).grid(row=2, columnspan=3, sticky="ew")
ttk.Separator(root, orient=HORIZONTAL).grid(row=5, columnspan=3, sticky="ew")
ttk.Separator(root, orient=HORIZONTAL).grid(row=9, columnspan=3, sticky="ew")

# Start app mainloop
app = App(root)
root.mainloop()
