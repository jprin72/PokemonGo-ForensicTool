import urllib2
import os

class StaticMaps(): 
	'''
	Class to generate static map objects with Google's Static Maps API
	'''
	apikey = ''
	tmp = ''
	size = ''
	scale = ''
	format = '' 

	def __init__(self, key, tmp, size, scale, format): 
		'''
		Initalize Static Maps Object. 
		@key: Google Maps API key.
		@tmp: Directory to store downloaded images. 
		@size: Size of the map. 
		@scale: Scale of the map (1|2)
		@format: Format of map. 
		'''
		self.apikey = key
		self.tmp = tmp 
		self.size = size
		self.scale = scale
		self.format = format

		#check to make sure dir exists. if not make it. 
		if not os.path.exists(tmp):
			os.makedirs(tmp)
		
	def getMap(self, zoom, cords, saveFile): 
		'''
		Function to get a map image using Google's Static Maps API. 
		@zoom: Zoom level for the map. 
		@cords: List of GPS Cordinates for each marker.  List also contains a boolean to indicate color. 
		@saveFile: File to save downloaded map image. 
		'''
		#base url 
		url = 'https://maps.googleapis.com/maps/api/staticmap?size='+self.size+'&scale='+self.scale+'&zoom='+zoom+'&format='+self.format
		label = 'A'

		#add each marker to url 
		for x in cords: 
			#check if color indicator is set. 
			if x[2]: 
				#if true then set color to blue 
				url = url+'&markers=color:blue%7clabel:'+label+'%7c'+x[0]+','+x[1]
			else: 
				#color is default (red) 
				url = url+'&markers=label:'+label+'%7c'+x[0]+','+x[1]
				
			#increment label by one
			label = chr(ord(label)+1)

		#add api key to url 
		url = url+'&key='+self.apikey

		#make HTTPS request 
		r = urllib2.urlopen(url)
		#save file
		with open(os.path.join(self.tmp, saveFile), 'wb') as f: 
			f.write(r.read())