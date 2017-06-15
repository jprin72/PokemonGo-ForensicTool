import os, time, datetime, ntpath, tarfile

'''
Custom Utility Functions
'''

def extractTarFile(path, dest): 
    '''
    Function to extract the entire contents of a tar file to a directory. 
    @path: Tar file to extract. 
    @dest: Destination to extract Tar file.
    '''
    tar = tarfile.open(path)
    tar.extractall(dest)
    tar.close()


def getFileNameFromPath(path): 
    '''
    Function to get file name from path. 
    RETURNS: filename
    '''
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def hexdump(x, dump=True):
    '''
    Function to print contents of a buffer in hex. 
    '''
    s = "Offset    00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F\n\n"
    x = str(x)
    l = len(x)
    i = 0

    while i < l:
        s += "%08x  " % i
        for j in xrange(16):
            if i+j < l:
                s += "%02X" % ord(x[i+j])
            else:
                s += "  "
            s += " "
        s += " "
        s += sane_color(x[i:i+16])
        i += 16
        s += "\n"
 
    if s.endswith("\n"):
        s = s[:-1]
    if dump:
        return s
    else:
        print s

def sane_color(x):
    '''
    Function to generate ASCII Text from a line of hex
    '''
    r=""
    for i in x:
        j = ord(i)
        if (j < 32) or (j >= 127):
            r=r+"."
        else:
            r=r+i
    return r

def get_timestamp(path):
    '''
    Function to return the last modified timestamp of a file. 
    @path: path to file 
    '''
    #get timestamp
    ts = os.path.getmtime(path)
    if ts!= 0.0:
        timestamp = time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(ts))
    else: 
        timestamp = ""
    return timestamp

def get_fileSize(path): 
    '''
    Function to return the file size of a file. 
    @path: path to file
    '''
    #get file size 
    if os.path.isfile(path) is True: 
        fs = os.path.getsize(path)
    else: 
        fs = ""
    return fs   

def timestamp(): 
    '''
    Funtion to return the current date and time. 
    '''
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%m-%d-%Y %H:%M:%S')