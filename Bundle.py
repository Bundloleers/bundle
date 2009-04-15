
import zipfile
import pygtk
pygtk.require('2.0')

# we also need gtk, duuuh
import gtk
#import threading
import shutil
import sys
import logging

class Bundle:
        unpacked, packed, unDef = range(3)
        inZip = 5
        notInZip = 6
        _logger = None
        
        
        def __init__(self,  zipFrom):
            self.objList = []
            self.tempFileList = []
            self._logger = logging.getLogger('bundle.BundleActivity')
            self._logger.setLevel(logging.DEBUG) # Show ALL messages
            self._logger.debug("Initializing Bundle")
            if (zipFrom) :
                self.status =  self.packed
                self.zipFrom =  zipfile.ZipFile(zipFrom, "r") # this will crash horribly if you don't hand me a path name :))
                self.objList = [(file, self.inZip) for file in (self.zipFrom.namelist())]  # List comprehensions finally make sense to me.
            else : 
                self.objList = []
                self.zipFrom = None
                self.status =  self.unpacked
            # this does something cool
        
    #  initializes the bundle; if mode ==unpacked, creates an empty bundle;
    #  else if mode == packed, uses the manifest to initialize the bundle.

        def add(self,  item):
            if (item.object_id):
                if (item in self.objList):
                    return 0
                else:
                    self.objList.append(item)
                    return 1
            elif (item.file_name):
                self.objList.append(item)
                return 1
            else:
                return 0
            # code can be added here to scribble this out to the scratch sheet...
#  adds object defined by object_id to the bundle.\par

        def erase(self,  item):
            self._logger.debug(["Got as far as here",  ""])
            if (item in self.objList):  #So.  This is probably unnecessary, but I thought maybe I oughtn't be clever.
                self.objList.remove(item)
            else:
                self.objList.remove(item)
            return 0

#  erases object defined by object_id from the bundle.\par
        def pack(self, archiveName):
            import tempfile
            empty = True
            f,  tmpzip = tempfile.mkstemp(".zip", dir = self.parent.scratchDir)
            del f
            self.status = self.packed
            self._logger.debug(["We need to pack these files",  "to " + archiveName ])
            for file in self.tempFileList:
                self._logger.debug([file,  ""])
            
            self._logger.debug("Opening zipfile for writing")
            try:
                temp = zipfile.ZipFile(archiveName, "w")
            except Exception,  e:
                self._logger.debug("Could not open %s",  str(e))
                
            try:
                for file in self.tempFileList :
                    empty = False
                    self._logger.debug("Zipping file...%s",  file)
                    try:
                        # this was changed from file.encode because nowadays on this system [ubuntu right side]
                        # the file is being passes as a tuple [God knows why]
                        temp.write(file[0].encode("utf-8", "replace"))
                    except Exception,  e:
                        self._logger.debug("Not zipped: %s --- %s",  file[0], str(e))
                        
                    self._logger.debug(["Apparently...",  "Done"])
            except zipfile.BadZipfile:
                self._logger.debug([file+" caused a BAD_ZIP_FILE exception", str(e)])
            except OSError:
                self._logger.debug([file+" caused a OSError exception", str(e)])
            except UnicodeDecodeError,  e:
                self._logger.debug([file+" caused a UNICODE exception",  str(e)])
            except Exception,  e:
                self._logger.debug([file+" caused a general exception",  str(e)])
            finally:
                temp.close()
                #shutil.copy(archiveName)
                for (item) in self.objList:
                    item.status = self.inZip
                    item.object_id = None
                self.tempFileList = []
                self.objList = []
                if (empty):
                    return -1 #archive is empty
                return 0
#  uses Python libraries to compress bundle contents into an archive.\par
#  the documentation is awful.


        def extractOne(self, item):
            if ((item in self.objList) and (self.zipFrom)  and (item.status == self.inZip)):
              #This uses the fact that like C++, non-zero values are true by convention.
               return self.zipFrom.read(item.file_name)  #this apparently returns the bytes of the file?
            self._logger.debug("returning 0")
            return 0
# extracts object defined by object_id from the bundle, adds it to a list extrObjs,\par
# and makes it into a Journal entry by calling myJCtrl.addToJournal(extrObjs).\par

        def extractAll():
            return 0
#  extracts all objects from the bundle, adds them to a list extrObjs,\par
#  and makes them separate Journal entries by calling myJCtrl.addToJournal(extrObjs).\par

        def changeFormat(ext):
            # does nothing in this subset!
            return 0
#  changes the archive format for the bundle to what ext specifies.\par

        def main(self):
            # All PyGTK applications must have a gtk.main(). Control ends here
            # and waits for an event to occur (like a key press or mouse event).
            gtk.main()
# If the program is run directly or passed as an argument to the python
# interpreter then create an instance and show it
# (Cosmin: ) at this point it's used only for debugging purposes. If you run the whole application
# an error in the script will freeze the activity, while running the Bundle with an interpreter will 
# show all python errors in the Terminal
if __name__ == "__main__":
    bundleWindow = Bundle(0)
    bundleWindow.main()
