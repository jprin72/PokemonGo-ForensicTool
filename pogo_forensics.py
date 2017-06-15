from Tkinter import * 
from ScrolledText import ScrolledText
import ttk, tkFileDialog, os, time, sqlite3, json, subprocess
import xml.etree.ElementTree as ET 

#Custom Imports
import utils as u 
import CustomNotebook as cnb
import EventLogger as el
import StaticMaps as sm

try: 
	import s2 #this must be custom compiled. 
	s2Lib = True
except: 
	s2Lib = False

class App: 
	'''
	Class that defines the PokemonGo Forensics Application. 
	'''

	def __init__(self):
		'''
		Initalize the Application GUI. 
		''' 

		self.root = Tk()
		self.root.title("Pokemon GO: Forensic Analysis Tool")
		self.root.minsize(width=1500, height=900)
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

		#Menu Bar
		self.menubar = Menu(self.root)
		self.filemenu = Menu(self.menubar, tearoff=0)
		self.filemenu.add_command(label="Capture PokemonGo Backup", command=self.capture_backup)
		self.filemenu.add_command(label="Capture Full Backup", command= lambda: self.capture_backup(True))
		self.filemenu.add_command(label="Create New Analysis from Backup", command=self.create_case_backup)
		self.filemenu.add_command(label="Open Case Folder", command=self.open_case_folder)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Exit", command=self.on_closing) 
		self.menubar.add_cascade(label="File", menu=self.filemenu)
		#add menu bar to root window
		self.root.config(menu=self.menubar)

		#Create Main Paned Window
		self.m1 = PanedWindow(self.root) 
		self.m1.pack(fill=BOTH, expand=1, padx=2, pady=3)

		#Create Left Pane For Treeview
		self.fileTree = ttk.Treeview(self.m1)
		self.fileTree["columns"]=("date_modified", "size")
		self.fileTree.column("#0", width=300)
		self.fileTree.column("date_modified", width=150)
		self.fileTree.column("size", width=150)
		self.fileTree.heading("#0", text="Name")
		self.fileTree.heading("date_modified", text="Date Modified")
		self.fileTree.heading("size", text="Size")
		#Bind double click option 
		self.fileTree.bind("<Double-1>", self.FileTreeDoubleClick)
		#add file tree to paned window
		self.m1.add(self.fileTree)

		#Create Right Pane Window - Split 
		self.m2 = PanedWindow(self.m1, orient=VERTICAL)
		self.m1.add(self.m2)

		#Create Notebook view for file information 
		self.nb = cnb.CustomNotebook(self.m2, name="nb_View")
		self.nb.enable_traversal() 

		#Frame for Welcome Tab 
		self.welcomeFrame = Frame(self.nb, name="welcome")
		self.welcomeFrame.grid(row=0, column=0, columnspan=2, sticky='new')
		self.welcomeFrame.rowconfigure(1, weight=1)
		self.welcomeFrame.columnconfigure(1, weight=1)

		#Welcome Tab Text
		self.WelcomeMsgLbl = Label(self.welcomeFrame, text='Welcome!', font='TkDefaultFont 12 bold')
		self.WelcomeMsgLbl.grid(row=0, column=0, columnspan=2, sticky='new', pady=5, padx=5)

		self.OverviewMsgLbl = Label(self.welcomeFrame, text='Overview: ', font='TkDefaultFont 10 bold')
		self.OverviewMsgLbl.grid(row=1, column=0, sticky='nw', padx=2, pady=2)

		self.ExplainMsgLbl = Label(self.welcomeFrame, text='This application parses the session information from the Upsight Logs of the PokemonGo Application from an Android Backup File. Using this information an investigator is '+
															'able to determine the start and end time of the last time the game was actively played. Active game play is determined by when the game is '+
															'run in the foreground of the mobile device. Therefore, the session end time will reflect the time at which the application was terminated, '+
															'or backgrounded. If a backgrounded application is later terminated, the session end time will not be affected provided the application was ' +
															'not brought to the forground before being terminated. The use of a PokemonGo Plus device with the mobile application will not affect this ' +
															'session information. Gameplay can also be inferred by examining the timestamps of certian files within the mobile application. In particular ' +
															'the files contained within the "ef/bundles" directory which contain Unity 3D models for different assets within the game, and are dynmically downloaded '+
															'during gameplay. \n\n'+
															'The application is capable retrieving and mapping the relative geolocation information of the user at the end of the last active session. These location cordinates are '+
															'rounded to two decimal places when stored by the application.  Therefore, the cordinates can be two to three blocks off from the user\'s true position. '+
															'Applications installed before July 31, 2017 may contain crittercism log files. These log files may contain additional geolocation information.', font='TkDefaultFont 10', justify='left', wraplength=1000)
		self.ExplainMsgLbl.grid(row=2, column=0, columnspan=2, sticky='new', pady=2, padx=2)

		self.GettingStartedMsgLbl = Label(self.welcomeFrame, text='Getting Started:', font='TkDefaultFont 10 bold')
		self.GettingStartedMsgLbl.grid(row=3, column=0, sticky='nw', padx=2, pady=2)

		self.GSTxtLbl = Label(self.welcomeFrame, text='File>Capture PokemonGo Backup:  Captures a backup of the PokemonGo Application from the target device.\n' +
													  'File>Capture Full Backup:  Captures a full backup of the target device.\n'+
													  'File>Create New Analysis from Backup:  Creates a new case folder in the current working directory named after the selected Android backup file. \n' +
													  '                                       The selected Android backup file is extracted to this directory, and the Upsight logs are parsed.\n'+
													  'File>Open Case Folder:  Opens a case folder containing an extracted Android backup file, and parses the Upsight logs.\n'+
													  '\nAfter a case has been opened, an Overview Tab will be created that contains all of the information contained within the Upsight logs. The application will '+
													  'also generate a file tree of all the files contained within the mobile application, and their last modified timestamps.  Double-Clicking on a file will '+
													  'open the file in a hex viewer. The application will also provide an investigator the option to map the GPS cordinates found within the Upsight database. '+
													  'If the application detects the presence of the Crittercism Log files, an option to parse, and map this location information will also be provided. ', font='TkDefaultFont 10', justify='left', wraplength=1000)
		self.GSTxtLbl.grid(row=4, column=0, sticky='nw', padx=2, pady=2)

		self.CrittercismMsgLbl = Label(self.welcomeFrame, text='Crittercism Logs:', font='TkDefaultFont 10 bold')
		self.CrittercismMsgLbl.grid(row=5, column=0, sticky='nw', padx=2, pady=2)

		self.CrittercismTxtLbl = Label(self.welcomeFrame, text='In order to parse the Crittercism log files, the Google S2 Geometry Library must be installed. This library is available at the following link: '+
																'https://github.com/micolous/s2-geometry-library\n\n' +
																'The most accurate location information derived from these logs comes from enteries where an Cell ID encounter identifier was updated. These entries are represented by a blue marker on the map. '+
																'Log entries that indicate that a Cell ID was removed are shown in red. These appear to occur at the edges of the user\'s location. \n\n\n\n\n\n', font='TkDefaultFont 10', justify='left', wraplength=1000)
		self.CrittercismTxtLbl.grid(row=6, column=0, sticky='nw', padx=2, pady=2)

		self.nb.add(self.welcomeFrame, text="Welcome")
		self.m2.add(self.nb)

		#Create Event Viewer Window
		self.logViewText = ScrolledText(self.m2, height=10)
		self.logViewText.grid(row=0, column=0, sticky='nsew')
		self.m2.add(self.logViewText)

		#Create Event Viewer Object
		self.evtLogger = el.EventLogger(self, logfile)

		#Check if S2 Library Exists
		if not s2Lib:
			#if no record it in the log
			self.evtLogger.logEvent(self, "S2 Library Not Found!!", True)

		#Set default zoom levels
		self.zoomLvl = 15 
		self.cbcsZoomLvl = 15
		self.pbcsZoomLvl = 15

		#Successfully Initialized the application
		self.evtLogger.logEvent(self, "Application Initialized!")

		#Enter the mainloop
		self.root.mainloop()

	def capture_backup(self, full=False):
		'''
		Capture a backup of the target (attached) device using Andriod Debug Bridge. 
		@full: Capture Full backup of device (True), or Capture only PokemonGo (False)
		'''
		#Get path to save capture as
		saveas = tkFileDialog.asksaveasfilename(defaultextension='.ab')
		try: 
			#run adb devices command to check if device is recognized and adb is installed
			self.evtLogger.logEvent(self, "\n"+subprocess.check_output(['adb', 'devices']))
			try: 
				self.evtLogger.logEvent(self, 'Started Backup Process')
				#Determine if taking a full or partial back up
				if not full: 
					output = subprocess.check_output(['adb', 'backup', 'com.nianticlabs.pokemongo', '-f', saveas], stderr=subprocess.STDOUT)
				else: 
					output = subprocess.check_output(['adb', 'backup', '-all', '-f', saveas], stderr=subprocess.STDOUT)

				self.evtLogger.logEvent(self, output)
				self.evtLogger.logEvent(self, 'Completed Capture: '+saveas)
			except: 
				#Problem Creating back up
				self.evtLogger.logEvent(self, 'An error occurred!!', True)
		except: 
			#ADB Not found!! 
			self.evtLogger.logEvent(self, 'Android Debug Bridge Not Found!', True)

	def on_closing(self): 
		'''
		Perform these actions when the application is closed. 
		'''
		#Log application termination 
		self.evtLogger.logEvent(self, "Terminating Application!")
		#close the application
		self.root.destroy()

	def FileTreeDoubleClick(self, event): 
		'''
		Event Listener for Double Click on a File Tree Item.  This method will display the hexdump of the clicked item in a new notebook tab. 
		'''
		item = self.fileTree.selection()[0]

		#check that clicked item is a file
		if os.path.isfile(item): 
			self.evtLogger.logEvent(self, "Open Hexview of file: "+item)

			#create new frame
			self.fileViewFrame = Frame(self.nb)
			self.fileViewFrame.grid(row=0, column=0, columnspan=2, sticky='new')

			#create scrolled text box to display hex dump
			self.fileViewText = ScrolledText(self.fileViewFrame, height=40)
			self.fileViewText.grid(row=0, column=0, sticky='nsew', pady=5, padx=5)

			#read in contents of selected item
			with open(item, 'rb') as f: 
				content = f.read() 
				text = u.hexdump(content)

				#display contents in new scrolled text box
				self.fileViewText.insert(END, text)
				self.fileViewText.config(state=DISABLED)

			#add Frame to notebook
			self.nb.add(self.fileViewFrame, text=self.fileTree.item(item, "text"))
			#select newly added tab
			self.selectCurrentTab()

	def add_item(self, dirname, parentName=None, top=True): 
		'''
		Recursive function to add items to the File Tree Viewer. 
		@dirname: current directory being parsed 
		@parentName: Name of the parent item in tree
		@top: Specifies if a top level directory 
		'''
		dirs = os.listdir(dirname)

		if top is True: 
			for name in dirs: 
				path = os.path.join(dirname, name)

				#get metadata information 
				timestamp = u.get_timestamp(path)
				fs = u.get_fileSize(path)
				
				self.fileTree.insert("", 0, path, text=name, values=(timestamp, fs))

				if os.path.isdir(path) is True: 
					self.add_item(path, path, False)
		else: 
			for name in dirs: 
				path = os.path.join(dirname, name)

				#get metadata information 
				timestamp = u.get_timestamp(path)
				fs = u.get_fileSize(path)

				self.fileTree.insert(parentName, 0, path, text=name, values=(timestamp, fs))
				if os.path.isdir(path) is True: 
					self.add_item(path, path, False)

	def selectCurrentTab(self): 
		'''
		Function to select the top most tab in the notebook view. 
		'''
		self.nb.select(len(self.nb.tabs())-1)

	def parseCrittercismLogs(self, path, name): 
		'''
		Function to parse all files within the crittercism logs.  This function searches for log entries that contain Cell ID information.
		The function converts Cell ID information into GPS Cordinates, and passes this information to the StaticMaps function to generate a map. 
		The function will also return a list containing the raw text of each log entry that contains Cell ID information. 
		@path: The path to the log files. 
		@name: The name of the logs being searched (current_bcs|previous_bcs). This is passed to the StaticMaps function to name the map. 
		'''
		#obtain list of files in directory 
		files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
		
		#compile regular expression -> THis is more effecient 
		cellRE = re.compile('(.*[C|c][e][l]{2}\s)([0-9]{19})(.*)')
		cordsRE= re.compile('[\[]([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)[\,][\s]([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?).*')

		cords = []
		logText = []

		for log in files: 
			with open(os.path.join(path, log)) as f: 
				content = f.read() 
				result = cellRE.match(content)
				#check if log contains Cell ID information 
				if result is not None: 
					#append contents of log to list
					logText.append(result.group(0))
					
					#Convert to GPS location information 
					hexv = str(hex(int(result.group(2))))
					cord = str(s2.S2CellId_FromToken(hexv[2:-1]).ToLatLng())
					
					cre = cordsRE.findall(cord)

					#determine if Updating Cell Encounter or Removing Cell ID
					for x in cre: 
						if result.group(1)[2:6] == 'Cell':
							cords.append((str(x[0]), str(x[4]), True))
						else: 
							cords.append((str(x[0]), str(x[4]), False))

		if name == 'current_bcs':
			#Get Map of Current_BCS
			self.sm.getMap(str(self.cbcsZoomLvl), cords, name+str(self.cbcsZoomLvl)+'.gif' )
		else:
			#Get Map of Previous_BCS
			self.sm.getMap(str(self.pbcsZoomLvl), cords, name+str(self.pbcsZoomLvl)+'.gif')

		#return raw text of each entry
		return logText

	def cbcsZoomIn(self): 
		'''
		Function to increase the zoom level of the current_bcs map. 
		'''
		#check zoom level
		if self.cbcsZoomLvl < 20:
			#increase zoom level
			self.cbcsZoomLvl = self.cbcsZoomLvl+1
			#check if already downloaded 
			if os.path.isfile(os.path.join(self.caseDir, 'maps', 'current_bcs'+str(self.cbcsZoomLvl)+'.gif')):
				self.evtLogger.logEvent(self, 'Increase Current_BCS Map Zoom Level: '+str(self.cbcsZoomLvl))
			else: 
				self.evtLogger.logEvent(self, "Download New Current_BCS Map Zoom Level: "+str(self.cbcsZoomLvl))
				self.parseCrittercismLogs(os.path.join(self.caseDir, 'apps', 'com.nianticlabs.pokemongo', 'f', 'com.crittercism', 'current_bcs'), 'current_bcs')

			#add image to frame
			self.current_bcsLogMapImage = PhotoImage(file=os.path.join(self.caseDir, 'maps', 'current_bcs'+str(self.cbcsZoomLvl)+".gif"))
			self.current_bcsLogMapImageLbl = Label(self.current_bcsLogMapFrame, image=self.current_bcsLogMapImage)
			self.current_bcsLogMapImageLbl.grid(row=0, column=0, rowspan=4, columnspan=2, sticky='nsew')
		else: 
			self.evtLogger.logEvent(self, "Already at Max Zoom!", True)

	def cbcsZoomOut(self):
		'''
		Function to decrease the zoom level of the current_bcs map. 
		'''
		#check zoom level
		if self.cbcsZoomLvl > 1:
			#decrease zoom level
			self.cbcsZoomLvl = self.cbcsZoomLvl-1
			#check if already downloaded 
			if os.path.isfile(os.path.join(self.caseDir, 'maps', 'current_bcs'+str(self.cbcsZoomLvl)+'.gif')):
				self.evtLogger.logEvent(self, 'Decrease Current_BCS Map Zoom Level: '+str(self.cbcsZoomLvl))
			else: 
				self.evtLogger.logEvent(self, "Download New Current_BCS Map Zoom Level: "+str(self.cbcsZoomLvl))
				self.parseCrittercismLogs(os.path.join(self.caseDir, 'apps', 'com.nianticlabs.pokemongo', 'f', 'com.crittercism', 'current_bcs'), 'current_bcs')

			#add image to frame
			self.current_bcsLogMapImage = PhotoImage(file=os.path.join(self.caseDir, 'maps', 'current_bcs'+str(self.cbcsZoomLvl)+".gif"))
			self.current_bcsLogMapImageLbl = Label(self.current_bcsLogMapFrame, image=self.current_bcsLogMapImage)
			self.current_bcsLogMapImageLbl.grid(row=0, column=0, rowspan=4, columnspan=2, sticky='nsew')
		else: 
			self.evtLogger.logEvent(self, "Already at Min Zoom!", True)

	def pbcsZoomIn(self): 
		'''
		Function to increase the zoom level of the previous_bcs map. 
		'''
		#check zoom level
		if self.pbcsZoomLvl < 20:
			#increase zoom level
			self.pbcsZoomLvl = self.pbcsZoomLvl+1
			#check if already downloaded 
			if os.path.isfile(os.path.join(self.caseDir, 'maps', 'previous_bcs'+str(self.pbcsZoomLvl)+'.gif')):
				self.evtLogger.logEvent(self, 'Increase Previous_BCS Map Zoom Level: '+str(self.pbcsZoomLvl))
			else: 
				self.evtLogger.logEvent(self, "Download New Previous_BCS Map Zoom Level: "+str(self.pbcsZoomLvl))
				self.parseCrittercismLogs(os.path.join(self.caseDir, 'apps', 'com.nianticlabs.pokemongo', 'f', 'com.crittercism', 'previous_bcs'), 'previous_bcs')

			#add image to frame
			self.previous_bcsLogMapImage = PhotoImage(file=os.path.join(self.caseDir, 'maps', 'previous_bcs'+str(self.pbcsZoomLvl)+".gif"))
			self.previous_bcsLogMapImageLbl = Label(self.previous_bcsLogMapFrame, image=self.previous_bcsLogMapImage)
			self.previous_bcsLogMapImageLbl.grid(row=0, column=0, rowspan=4, columnspan=2, sticky='nsew')
		else: 
			self.evtLogger.logEvent(self, "Already at Max Zoom!", True)

	def pbcsZoomOut(self): 
		'''
		Function to decrease the zoom level of the previous_bcs map. 
		'''
		#check zoom level
		if self.pbcsZoomLvl > 1:
			#decrease zoom level
			self.pbcsZoomLvl = self.pbcsZoomLvl-1
			#check if already downloaded 
			if os.path.isfile(os.path.join(self.caseDir, 'maps', 'previous_bcs'+str(self.pbcsZoomLvl)+'.gif')):
				self.evtLogger.logEvent(self, 'Decrease Previous_BCS Map Zoom Level: '+str(self.pbcsZoomLvl))
			else: 
				self.evtLogger.logEvent(self, "Download New Previous_BCS Map Zoom Level: "+str(self.pbcsZoomLvl))
				self.parseCrittercismLogs(os.path.join(self.caseDir, 'apps', 'com.nianticlabs.pokemongo', 'f', 'com.crittercism', 'previous_bcs'), 'previous_bcs')

			#add image to frame
			self.previous_bcsLogMapImage = PhotoImage(file=os.path.join(self.caseDir, 'maps', 'previous_bcs'+str(self.pbcsZoomLvl)+".gif"))
			self.previous_bcsLogMapImageLbl = Label(self.previous_bcsLogMapFrame, image=self.previous_bcsLogMapImage)
			self.previous_bcsLogMapImageLbl.grid(row=0, column=0, rowspan=4, columnspan=2, sticky='nsew')
		else: 
			self.evtLogger.logEvent(self, "Already at Min Zoom!", True)

	def mapCrittercismLogs(self): 
		'''
		Function that generates the frames to display the current_bcs and previous_bcs maps.  This function calls parseCrittercismLogs to parse 
		the log files.  
		'''
		#check if S2 library is present
		if s2Lib: 
			#parse files in current_bcs
			current_bcs = os.path.join(self.caseDir, 'apps', 'com.nianticlabs.pokemongo', 'f', 'com.crittercism', 'current_bcs')
			if os.path.exists(current_bcs):
				#parse current_bcs log files 
				logText = self.parseCrittercismLogs(current_bcs, 'current_bcs')
				
				#create frame to hold map 
				self.current_bcsLogMapFrame = Frame(self.nb)
				self.current_bcsLogMapFrame.grid(row=0, column=0, sticky='nsew')

				#add image to frame
				self.current_bcsLogMapImage = PhotoImage(file=os.path.join(self.caseDir, 'maps', 'current_bcs'+str(self.cbcsZoomLvl)+'.gif'))
				self.current_bcsLogMapImageLbl = Label(self.current_bcsLogMapFrame, image=self.current_bcsLogMapImage)
				self.current_bcsLogMapImageLbl.grid(row=0, column=0, rowspan=4, columnspan=2, sticky='nsew')

				#add Raw log file text to frame
				self.mapCurrent_BCSLogText = ScrolledText(self.current_bcsLogMapFrame, height=15, width=32)
				self.mapCurrent_BCSLogText.grid(row=0, column=2, columnspan=2, sticky='nsew')

				text = ''
				label = 'A'

				for x in logText: 
					text = text + label+': '+x+'\n\n'
					label = chr(ord(label)+1)

				self.mapCurrent_BCSLogText.insert(END, text)
				self.mapCurrent_BCSLogText.config(state=DISABLED)

				#add zoom controls to frame
				self.mapCurrent_BCSZoomInBtn = Button(self.current_bcsLogMapFrame, text='Zoom In', command=self.cbcsZoomIn)
				self.mapCurrent_BCSZoomInBtn.grid(row=1, column=2, sticky='sew')

				self.mapCurrent_BCSZoomOutBtn = Button(self.current_bcsLogMapFrame, text='Zoom Out', command=self.cbcsZoomOut) 
				self.mapCurrent_BCSZoomOutBtn.grid(row=2, column=2, sticky='new')

				#add frame to notebook view
				self.nb.add(self.current_bcsLogMapFrame, text='Current_BCS Map')
				#select recently added frame
				self.selectCurrentTab()
			else: 
				#could not find current_bcs logs
				self.evtLogger.logEvent(self, 'Current_bcs logs not found!', True)
			
			#parse files in previous_bcs
			previous_bcs = os.path.join(self.caseDir, 'apps', 'com.nianticlabs.pokemongo', 'f', 'com.crittercism', 'previous_bcs')
			if os.path.exists(current_bcs): 
				#parse previous_bcs log files
				logText = self.parseCrittercismLogs(previous_bcs, 'previous_bcs')

				#create frame to hold map
				self.previous_bcsLogMapFrame = Frame(self.nb)
				self.previous_bcsLogMapFrame.grid(row=0, column=0, sticky='nsew')

				#add image to frame
				self.previous_bcsLogMapImage = PhotoImage(file=os.path.join(self.caseDir, 'maps', 'previous_bcs'+str(self.pbcsZoomLvl)+'.gif'))
				self.previous_bcsLogMapImageLbl = Label(self.previous_bcsLogMapFrame, image=self.previous_bcsLogMapImage)
				self.previous_bcsLogMapImageLbl.grid(row=0, column=0, rowspan=4, columnspan=2, sticky='nsew')

				#add raw log file text to frame
				self.mapPrevious_BCSLogText = ScrolledText(self.previous_bcsLogMapFrame, height=15, width=32)
				self.mapPrevious_BCSLogText.grid(row=0, column=2, columnspan=2, sticky='nsew')

				text = ''
				label = 'A'

				for x in logText: 
					text = text + label+': '+x+'\n\n'
					label = chr(ord(label)+1)

				self.mapPrevious_BCSLogText.insert(END, text)
				self.mapPrevious_BCSLogText.config(state=DISABLED)

				#add zoom controls to frame
				self.mapPrevious_BCSZoomInBtn = Button(self.previous_bcsLogMapFrame, text='Zoom In', command=self.pbcsZoomIn)
				self.mapPrevious_BCSZoomInBtn.grid(row=1, column=2, sticky='sew')

				self.mapPrevious_BCSZoomOutBtn = Button(self.previous_bcsLogMapFrame, text='Zoom Out', command=self.pbcsZoomOut)
				self.mapPrevious_BCSZoomOutBtn.grid(row=2, column=2, sticky='new')

				#add frame to notebook view
				self.nb.add(self.previous_bcsLogMapFrame, text='Previous_BCS Map')
				#select recently added frame 
				self.selectCurrentTab()
			else: 
				#could not find previous_bcs
				self.evtLogger.logEvent(self, 'Previous_bcs logs not found!', True)

		else: 
			#S2 Library not found
			self.evtLogger.logEvent(self, 'S2 Library not found!', True)

	def onClickMapCords(self, latitude, longitude):
		'''
		Event Listener for displaying upsight map cordinates.
		@latitude: Latitude of marker. 
		@longitude: Longitude of marker. 
		'''
		cords = [(str(latitude), str(longitude), False)]

		#check if map already exists
		if not os.path.isfile(os.path.join(self.caseDir, 'maps', 'upsightMap'+str(self.zoomLvl)+'.gif')):
			self.sm.getMap(str(self.zoomLvl), cords, "upsightMap"+str(self.zoomLvl)+".gif")

		#Create Frame to hold map 
		self.upsightMapFrame = Frame(self.nb)
		self.upsightMapFrame.grid(row=0, column=0, sticky='nsew')

		#add image to frame
		self.upsightMapImage = PhotoImage(file=os.path.join(self.caseDir, 'maps', "upsightMap"+str(self.zoomLvl)+".gif"))
		self.upsightMapImageLbl = Label(self.upsightMapFrame, image=self.upsightMapImage)
		self.upsightMapImageLbl.grid(row=0, column=0, rowspan=2, columnspan=2, sticky='nsew')

		self.evtLogger.logEvent(self, "Download New Upsight Map Zoom Level: "+str(self.zoomLvl))

		#add zoom buttons to frame
		self.upsightMapZoomIn = Button(self.upsightMapFrame, text="Zoom In ", command= lambda: self.MapZoomIn('upsightMap', cords))
		self.upsightMapZoomIn.grid(row=0, column=3, sticky='sew')

		self.upsightMapZoomOut = Button(self.upsightMapFrame, text='Zoom Out', command= lambda: self.MapZoomOut('upsightMap', cords))
		self.upsightMapZoomOut.grid(row=1, column=3, sticky='new')

		self.upsightZoomSpacer = Label(self.upsightMapFrame)
		self.upsightZoomSpacer.grid(row=0, column=2)

		#add frame to notebook 
		self.nb.add(self.upsightMapFrame, text="Upsight Cords")
		#select current frame 
		self.selectCurrentTab()

	def MapZoomIn(self, name, cords): 
		'''
		Function to increase zoom level of upsight map. 
		@name: name of the map image
		@cords: cordinates of map image marker
		'''
		#check zoom level 
		if self.zoomLvl < 20:
			#increase zoom level
			self.zoomLvl = self.zoomLvl + 1
			#check if already downloaded
			if os.path.isfile(os.path.join(self.caseDir, 'maps', name+str(self.zoomLvl)+'.gif')):
				self.evtLogger.logEvent(self, "Increase Upsight Map Zoom Level: "+str(self.zoomLvl))
			else: 
				self.evtLogger.logEvent(self, "Download New Upsight Map Zoom Level: "+str(self.zoomLvl))
				self.sm.getMap(str(self.zoomLvl), cords, "upsightMap"+str(self.zoomLvl)+".gif")

			#add image to frame
			self.upsightMapImage = PhotoImage(file=os.path.join(self.caseDir, 'maps', "upsightMap"+str(self.zoomLvl)+".gif"))
			self.upsightMapImageLbl = Label(self.upsightMapFrame, image=self.upsightMapImage)
			self.upsightMapImageLbl.grid(row=0, column=0, rowspan=2, columnspan=2, sticky='nsew')
		else: 
			self.evtLogger.logEvent(self, "Already at Max Zoom!", True)

	def MapZoomOut(self, name, cords): 
		'''
		Function to decrease zoom level of upsight map. 
		@name: name of the map image
		@cords: cordinates of the map image marker
		'''
		#check zoom level 
		if self.zoomLvl > 1:
			#decrease zoom level
			self.zoomLvl = self.zoomLvl - 1
			#check if already downloaded
			if os.path.isfile(os.path.join(self.caseDir, 'maps', name+str(self.zoomLvl)+'.gif')):
				self.evtLogger.logEvent(self, "Decrease Upsight Map Zoom Level: "+str(self.zoomLvl))
			else: 
				self.evtLogger.logEvent(self, "Download New Upsight Map Zoom Level: "+str(self.zoomLvl))
				self.sm.getMap(str(self.zoomLvl), cords, "upsightMap"+str(self.zoomLvl)+".gif")

			#add image to frame
			self.upsightMapImage = PhotoImage(file=os.path.join(self.caseDir, 'maps', "upsightMap"+str(self.zoomLvl)+".gif"))
			self.upsightMapImageLbl = Label(self.upsightMapFrame, image=self.upsightMapImage)
			self.upsightMapImageLbl.grid(row=0, column=0, rowspan=2, columnspan=2, sticky='nsew')
		else: 
			self.evtLogger.logEvent(self, "Already at Min Zoom!", True)

	def create_case_backup(self): 
		'''
		Function to create a new case folder from an Android backup. 
		'''
		#get path to Andriod Backup file
		filename = tkFileDialog.askopenfilename(title='Create Case from Android Backup')

		#check that file was selected
		if filename != '': 
			self.evtLogger.logEvent(self, "Creating A New Case from Backup: "+filename)

			#Get backup filename and current working directory 
			name = u.getFileNameFromPath(filename)
			cwd =  os.getcwd()

			#path to case directory 
			caseDir = os.path.join(cwd, name[:-3])
			#check if case directory exists
			if not os.path.exists(caseDir):
				#if not create directory and extract backup 
				os.makedirs(caseDir)
				self.evtLogger.logEvent(self, "Creating New Case Folder: "+caseDir)
				
				#Path of extracted backup
				exBackup = os.path.join(caseDir, name[:-3]+'.tar')

				#extract the backup 
				abePath =  os.path.join(cwd, 'tools', 'abe', 'abe.jar')
				subprocess.call(['java', '-jar', abePath, 'unpack', filename, exBackup])
				self.evtLogger.logEvent(self, "Extracting Andriod Backup: "+exBackup)

				#extract the tar file
				u.extractTarFile(exBackup, caseDir) 
				self.evtLogger.logEvent(self, 'Extracting Archive... ')

				#Generate Case Information
				self.create_case(caseDir)
				self.evtLogger.logEvent(self, 'Successfully Created New Case')
			else: 
				#Case exists.  Use Open Case Folder instead... 
				self.evtLogger.logEvent(self, 'Case Already Exists!! Open Case Folder Instead!', True)

	def open_case_folder(self): 
		'''
		Function to open case from an already extracted Andriod backup. User must point application to Case Directory. 
		'''
		#get the directory path to the case directory 
		dirname = tkFileDialog.askdirectory(initialdir=os.getcwd(), title="Select the Case Folder you wish to open.")
		#check that directory was specified 
		if dirname != '':
			self.evtLogger.logEvent(self, "Opening Case Folder: "+dirname)
			#Generate Case Information 
			self.create_case(dirname)
			self.evtLogger.logEvent(self, 'Successfully Opened Case')

	def create_case(self, dirname):
		'''
		Function to parse the upsight information from an extracted Andriod backup. 
		@dirname: Path to the case directory. 
		'''
		#Initalize the StaticMaps Object 
		self.caseDir = dirname
		self.sm = sm.StaticMaps(googleAPI, os.path.join(self.caseDir, 'maps'), '1200x1000', '1', 'gif')

		dirname = os.path.join(dirname, 'apps', 'com.nianticlabs.pokemongo')

		#check if PokemonGo exists 
		if os.path.isdir(dirname) is not True: 
			self.evtLogger.logEvent(self, "PokemonGo Application not detected!", True)
		else: 
			#Build File Tree View
			self.add_item(dirname)
		
			#Basic Processing -> need to parse information from upsight.xml and update overview tab 
			upsight = os.path.join(dirname, 'sp', 'upsight.xml')
			if os.path.isfile(upsight):
				tree = ET.parse(upsight)
				root = tree.getroot() 

				sessInfo = {} 
				for child in root:
					if child.tag != 'string':
						sessInfo[child.attrib['name']] = child.attrib['value']

				#collect information from sqlite database
				upsightDB = os.path.join(dirname, 'db', 'upsight.db')
				if  os.path.isfile(upsightDB):
					conn = sqlite3.connect(upsightDB)
					c = conn.cursor() 
					c.execute("SELECT data FROM models WHERE type = 'upsight.model.location'")

					data = c.fetchone()
					if data != None: 
						j = json.loads(data[0])
						sessInfo['latitude'] = j['latitude'] 
						sessInfo['longitude'] = j['longitude'] 
					else: 
						self.evtLogger.logEvent(self, "No GPS information within Upsight Database Found!", True)
						sessInfo['latitude'] = None
					conn.close()
				else: 
					sessInfo['latitude'] = None
					self.evtLogger.logEvent(self, "com.nianticlabs.pokemongo\\db\\upsight.db Not Found!", True)
			else: 
				self.evtLogger.logEvent(self, "com.nianticlabs.pokemongo\\sp\\upsight.xml Not Found!", True)


			self.ovrViewFrame = Frame(self.nb, name="overview")

			##########################################
			# Display Last Known Session Information #
			##########################################

			self.LastKnownSessionLbl = Label(self.ovrViewFrame, text="Last Known Session Information", font="TkDefaultFont 12 bold")
			self.LastKnownSessionLbl.grid(row=0, column=0, columnspan=3, sticky='nw', pady=2, padx=2)

			#Session Number
			self.SessionNumLbl = Label(self.ovrViewFrame, text="Session Number: ", font="TkDefaultFont 10 bold")
			self.SessionNumLbl.grid(row=1, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.SessionNumVal = Label(self.ovrViewFrame, text=sessInfo['session_num'], font="TkDefaultFont 10")
			self.SessionNumVal.grid(row=1, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Current Session Duration 
			self.SessionDurLbl = Label(self.ovrViewFrame, text="Session Duration: ", font="TkDefaultFont 10 bold")
			self.SessionDurLbl.grid(row=2, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.SessionDurVal = Label(self.ovrViewFrame, text=sessInfo['current_session_duration'], font="TkDefaultFont 10")
			self.SessionDurVal.grid(row=2, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Session Start Time 
			self.SessionStartLbl = Label(self.ovrViewFrame, text="Session Start Time: ", font="TkDefaultFont 10 bold")
			self.SessionStartLbl.grid(row=3, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.SessionStartVal = Label(self.ovrViewFrame, text=time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(float(sessInfo['session_start_ts']))), font="TkDefaultFont 10" )
			self.SessionStartVal.grid(row=3, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Session End Time
			self.SessionEndLbl = Label(self.ovrViewFrame, text="Session End Time: ", font="TkDefaultFont 10 bold")
			self.SessionEndLbl.grid(row=4, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.SessionEndVal = Label(self.ovrViewFrame, text=time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(float(sessInfo['last_known_session_time']))), font="TkDefaultFont 10")
			self.SessionEndVal.grid(row=4, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Past Session Time 
			self.PastSessTimeLbl = Label(self.ovrViewFrame, text="Past Session Time: ", font="TkDefaultFont 10 bold")
			self.PastSessTimeLbl.grid(row=5, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.PastSessTimeVal = Label(self.ovrViewFrame, text=sessInfo['past_session_time'], font="TkDefaultFont 10")
			self.PastSessTimeVal.grid(row=5, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Sequence ID
			self.SeqIDLbl = Label(self.ovrViewFrame, text="Sequence ID: ", font="TkDefaultFont 10 bold")
			self.SeqIDLbl.grid(row=6, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.SeqIDVal = Label(self.ovrViewFrame, text=sessInfo['seq_id'], font="TkDefaultFont 10")
			self.SeqIDVal.grid(row=6, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Install Timestampe
			self.InstallTSLbl = Label(self.ovrViewFrame, text="Install Time: ", font="TkDefaultFont 10 bold")
			self.InstallTSLbl.grid(row=7, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.InstallTSVal = Label(self.ovrViewFrame, text=time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(float(sessInfo['install_ts']))), font="TkDefaultFont 10" )
			self.InstallTSVal.grid(row=7, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Player XP
			self.PlayerXPLbl = Label(self.ovrViewFrame, text="Player XP: ", font='TkDefaultFont 10 bold')
			self.PlayerXPLbl.grid(row=8, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.PlayerXPVal = Label(self.ovrViewFrame, text=sessInfo['com.upsight.user_attribute.player_xp'], font='TkDefaultFont 10')
			self.PlayerXPVal.grid(row=8, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Player Avatar
			self.PlayerAvatarLbl = Label(self.ovrViewFrame, text="Player Avatar: ", font='TkDefaultFont 10 bold')
			self.PlayerAvatarLbl.grid(row=9, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.PlayerAvatarVal = Label(self.ovrViewFrame, text=sessInfo['com.upsight.user_attribute.player_avatar'], font='TkDefaultFont 10')
			self.PlayerAvatarVal.grid(row=9, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Item count 
			self.ItemCntLbl = Label(self.ovrViewFrame, text="Item Count: ", font='TkDefaultFont 10 bold')
			self.ItemCntLbl.grid(row=10, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.ItemCntVal = Label(self.ovrViewFrame, text=sessInfo['com.upsight.user_attribute.item_count'], font='TkDefaultFont 10')
			self.ItemCntVal.grid(row=10, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Pokemon Count 
			self.PokemonCntLbl = Label(self.ovrViewFrame, text="Pokemon Count: ", font='TkDefaultFont 10 bold')
			self.PokemonCntLbl.grid(row=11, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.PokemonCntVal = Label(self.ovrViewFrame, text=sessInfo['com.upsight.user_attribute.pokemon_count'], font='TkDefaultFont 10')
			self.PokemonCntVal.grid(row=11, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#Player Level 
			self.PlayerLevelLbl = Label(self.ovrViewFrame, text="Player Level: ", font='TkDefaultFont 10 bold')
			self.PlayerLevelLbl.grid(row=12, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			self.PlayerLevelVal = Label(self.ovrViewFrame, text=sessInfo['com.upsight.user_attribute.player_level'], font='TkDefaultFont 10')
			self.PlayerLevelVal.grid(row=12, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#lastPushTokenRegistrationTime
			#check to see if file exists 
			registration = os.path.join(dirname, 'sp', 'com.upsight.android.googleadvertisingid.internal.registration.xml')
			if os.path.isfile(registration):
				tree = ET.parse(registration)
				root = tree.getroot()
				for child in root: 
					if child.tag != 'string': 
						sessInfo[child.attrib['name']] = child.attrib['value']
				self.evtLogger.logEvent(self, 'Found lastPushTokenRegistrationTime.')

				#Display results 
				self.LastPushLbl = Label(self.ovrViewFrame, text="lastPushTokenRegistrationTime: ", font='TkDefaultFont 10 bold')
				self.LastPushLbl.grid(row=13, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

				self.LastPushVal = Label(self.ovrViewFrame, text=time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(float(sessInfo['lastPushTokenRegistrationTime']))), font="TkDefaultFont 10" )
				self.LastPushVal.grid(row=13, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			else: 
				self.evtLogger.logEvent(self, registration+' not found!', True)

			#Upsight.db Cords
			self.GPSCordsLbl = Label(self.ovrViewFrame, text="Relative GPS Cords: ", font='TkDefaultFont 10 bold')
			self.GPSCordsLbl.grid(row=14, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

			#check if upsight cords were found
			if sessInfo['latitude'] == None: 
				self.GPSCordsVal = Label(self.ovrViewFrame, text='')
			else: 	
				self.GPSCordsVal = Label(self.ovrViewFrame, text="("+str(sessInfo['latitude'])+", "+str(sessInfo['longitude'])+")", font='TkDefaultFont 10')
				
				#Create Button to display cords on a map. 
				self.DisplayCordsBtn = Button(self.ovrViewFrame, text="Map Cords", command= lambda: self.onClickMapCords(sessInfo['latitude'], sessInfo['longitude']))
				self.DisplayCordsBtn.grid(row=14, column=5, sticky='nsew', pady=2, padx=2)

			self.GPSCordsVal.grid(row=14, column=2, columnspan=2, sticky='nw', pady=2, padx=2)

			#check if crittercism logs exist
			if os.path.exists(os.path.join(dirname, 'f', 'com.crittercism')): 
				#Crittercism Logs Label
				self.CrittercismLogsLbl = Label(self.ovrViewFrame, text='Crittercism Logs Detected', font='TkDefaultFont 10 bold')
				self.CrittercismLogsLbl.grid(row=15, column=0, columnspan=2, sticky='nw', pady=2, padx=2)

				#Crittercism Logs Button 
				self.CrittercismLogsBtn = Button(self.ovrViewFrame, text='Map Logs', command=self.mapCrittercismLogs)
				self.CrittercismLogsBtn.grid(row=15, column=2, columnspan=2, sticky='nw', pady=2, padx=2)
			else: 
				self.evtLogger.logEvent(self, 'Crittercism Logs not detected.')

			#Account Name
			prefs = os.path.join(dirname, 'sp', 'com.nianticlabs.pokemongo.PREFS.xml')
			if os.path.isfile(prefs):
				tree = ET.parse(prefs)
				root = tree.getroot()

				for child in root: 
					if child.attrib['name'] == 'accountName': 
						sessInfo['accountName'] = child.text 

				#display results 
				self.AccountNameLbl = Label(self.ovrViewFrame, text='Account Name: ', font='TkDefaultFont 10 bold')
				self.AccountNameLbl.grid(row=19, column=0, columnspan=2, sticky='nw', padx=2, pady=2)

				self.AccountNameVal = Label(self.ovrViewFrame, text=sessInfo['accountName'], font='TkDefaultFont 10')
				self.AccountNameVal.grid(row=19, column=2, columnspan=2, sticky='nw', padx=2, pady=2)

				self.evtLogger.logEvent(self, 'Found Account Name!')
			else: 
				self.evtLogger.logEvent(self, prefs+' not found!', True)
			
			self.ovrViewFrame.grid(row=5, column=0, columnspan=2, sticky='new')
			#add overview frame to notebook view
			self.nb.add(self.ovrViewFrame, text="Overview")
			#select current tab
			self.selectCurrentTab()

if __name__ =="__main__":
	#Global Variables 
	logfile = "activityLog.txt"
	googleAPI ="AIzaSyD2RBTizPqfDs_T9P55rYX6QBhla07jUkw"

	app = App()