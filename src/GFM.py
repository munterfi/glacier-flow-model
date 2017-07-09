from Tkinter import *
import tkFileDialog, tkMessageBox
#import datetime
from Slac4M_Class import Slac4M as Slac4M

 
class App():
    '''
    sadsad
    '''
    def __init__(self, master):
        self.master = master
 
        #call start to initialize to create the UI elemets
        self.start()

    def start(self):
        self.master.title('Slac4M')
 
        #self.now = datetime.datetime.now()
 
        #CREATE A TEXT/LABEL
        #create a variable with text
        label01 = "Choose Shapefile ('.shp') to process:"
        label02 = "Choose folder for the outputfiles:"
        label_fill = ""
        label03 = "Keep original attribute data?"
        label04 = "Extract crossings and save as additional Shapefile?"
        label05 = "Save results also as CSV-files?"
        label_fill2 = ""
        label_fill3 = ""
        #put "label01" in "self.master" which is the window/frame
        #then, put in the first row (row=0) and in the 2nd column (column=1), align it to "West"/"W"
        Label(self.master, text=label01).grid(row=0, column=0, sticky=W)
        Label(self.master, text=label02).grid(row=2, column=0, sticky=W)
        Label(self.master, text=label_fill).grid(row=4, column=0, sticky=W)
        Label(self.master, text=label03).grid(row=5, column=0, sticky=W)
        Label(self.master, text=label04).grid(row=6, column=0, sticky=W)
        Label(self.master, text=label05).grid(row=7, column=0, sticky=W)
        Label(self.master, text=label_fill2).grid(row=8, column=0, sticky=W)
        Label(self.master, text=label_fill2).grid(row=10, column=0, sticky=W)
 
        #CREATE A TEXTBOX
        self.filelocation = Entry(self.master)
        self.filelocation["width"] = 60
        self.filelocation.focus_set()
        self.filelocation.grid(row=1,column=0)
 
        #CREATE A BUTTON WITH "ASK TO OPEN A FILE"
        self.open_file = Button(self.master, text="Browse...", command=self.browse_file) #see: def browse_file(self)
        self.open_file.grid(row=1, column=1) #put it beside the filelocation textbox

        #CREATE A TEXTBOX2
        self.filelocation2 = Entry(self.master)
        self.filelocation2["width"] = 60
        self.filelocation2.focus_set()
        self.filelocation2.grid(row=3,column=0)
        
        #CREATE A BUTTON WITH "ASK TO SAVE A FILE"
        self.save_file = Button(self.master, text="Browse...", command=self.browse_file_save) #see: def browse_file(self)
        self.save_file.grid(row=3, column=1) #put it beside the filelocation textbox
 
        #CREATE RADIO BUTTONS
        RADIO_BUTTON1 = [
            ("Yes", True),
            ("No",False),
        ]
 
        #initialize a variable to store the selected value of the radio buttons
        #set it to A by default
        self.radio_var1 = StringVar()
        self.radio_var1.set(False)
        self.radio_var2 = StringVar()
        self.radio_var2.set(False)
        self.radio_var3 = StringVar()
        self.radio_var3.set(False)
 
        #create a loop to display the RADIO_BUTTON
        i=0
        for text, item in RADIO_BUTTON1:
            #setup each radio button. variable is set to the self.radio_var
            #and the value is set to the "item" in the for loop
            self.radio1 = Radiobutton(self.master, text=text, variable=self.radio_var1, value=item)
            self.radio1.grid(row=5, column=i+1)
            self.radio2 = Radiobutton(self.master, text=text, variable=self.radio_var2, value=item)
            self.radio2.grid(row=6, column=i+1)
            self.radio3 = Radiobutton(self.master, text=text, variable=self.radio_var3, value=item)
            self.radio3.grid(row=7, column=i+1)
            i += 1
 
        #now for a button
        self.submit = Button(self.master, text="Process!", command=self.start_processing, fg="red")
        self.submit.grid(row=9, column=0)

    def browse_file(self):
        #put the result in self.filename
        self.filename = tkFileDialog.askopenfilename(title="Open a file...")

        #this will set the text of the self.filelocation
        self.filelocation.insert(0,self.filename)

    def browse_file_save(self):
        #put the result in self.filename
        self.filename2 = tkFileDialog.askdirectory(title="Save as...")

        #this will set the text of the self.filelocation
        self.filelocation2.insert(0,self.filename2)

    def start_processing(self):
        # Process file with Slac4M, setting up Variables
        print bool(int(self.radio_var1.get())), self.radio_var2.get(), self.radio_var3.get()
        orig_attr = bool(int(self.radio_var1.get()))
        crossings = bool(int(self.radio_var2.get()))
        csvfile = bool(int(self.radio_var3.get()))

        # Satrting the Process
        adjacency = Slac4M(self.filename, self.filename2+'/',
                 csvfile, orig_attr, crossings)
        adjacency.initiate()
        adjacency.calculate()
        adjacency.save()


root = Tk()
app = App(root)
root.mainloop()
