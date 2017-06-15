from Tkinter import * 
from ScrolledText import ScrolledText

#custom Imports 
import utils as u 

class EventLogger:
	'''
	Class to handle event logging within event viewer and log file. 
	'''
	def __init__(self, app, logFileName): 
		'''
		Set up Event Logger Object. 
		@app: calling application object.  Needed to update event viewer window. 
		@logFileName: Name of the log file to log actions. 
		'''
		self.logfile = open(logFileName, 'a')

		app.logViewText.insert(END, "Welcome to the Pokemon Go Mobile Analysis Application \n\n")
		self.logfile.write("\nWelcome to the Pokemon Go Mobile Analysis Application \n\n")
		self.logEvent(app, "Event Log: "+logFileName)

		#create "alert" tag for errors 
		app.logViewText.tag_config("alert", foreground="red")

	def logEvent(self, app, event, alert=False): 
		'''
		Function to handle logging of events to log viewer and log file. 
		@app: Calling application object. 
		@event: Event text to record in logs 
		@alert: General information (False), Critical Alert (True)
		'''
		app.logViewText.config(state=NORMAL)

		#Build Log Entry
		if alert:
			entry = r" [!] "+u.timestamp()+" "+event+"\n"
			app.logViewText.insert(END, entry, "alert")
		else: 
			entry = r" [*] "+u.timestamp()+" "+event+"\n"
			app.logViewText.insert(END, entry)

		app.logViewText.see(END)
		app.logViewText.config(state=DISABLED)

		#log to eventLog file 
		self.logfile.write(entry)
		self.logfile.flush()