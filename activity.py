# Load GTK
import gtk
import pygtk
pygtk.require('2.0')

from Bundle import Bundle
from GUI import GUI
import copy
from ArchiveItem import  ArchiveItem
from gettext import gettext as _

# Load sugar libraries
# I hear this is _import_ant ;) ~J
from sugar.activity import activity  
from sugar.datastore import datastore
from sugar.datastore import dbus_helpers
from sugar.graphics.toolbutton import ToolButton
import tempfile
import shutil
import logging
import zipfile
import os
from sugar.activity.registry import ActivityRegistry
from datetime import datetime

class BundleActivity(activity.Activity):
    
    zip_mime = ["application/x-zip",  "application/zip",  "application/x-zip-compressed"]
    _logger = None
    
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        self._name = handle
        # Set up logging. We're sending messages to the default log directory,
        # which can be browsed with the Log activity.
        
        self._logger = logging.getLogger('bundle.BundleActivity')
        self._logger.setLevel(logging.DEBUG) # Show ALL messages
        # self._logger.setLevel(logging.WARNING) # Ignore DEBUG/INFO msgs
        self._logger.debug("Initializing BundleActivity.")

        # Set title for our Activity
        self.set_title('Bundle Activity')

        # Attach sugar toolbox (Share, ...)
        toolbox = activity.ActivityToolbox(self)
        self.set_toolbox(toolbox)
        #toolbox.show()
        
        self.activity_toolbar = toolbox.get_activity_toolbar()
        
        #create toolbar
        self.main_toolbar = gtk.Toolbar()
        #self.main_toolbar.show()
        
        toolbox.add_toolbar(_('Bundle'),  self.main_toolbar)
        toolbox.set_current_toolbar(1)
        toolbox.show()
        
        # Create the main container
        self._main_view = gtk.VBox()

        # Import our class Bundle():

        # Step 1: Load class, which creates Bundle.widget
        self.myBundle = Bundle(None)
        self._logger.debug("Bundle instance created.")
        self.myBundle.parent = self
        
        self.myGUI = GUI(self)
        self.myGUI.xid = handle
        self.myGUI.myBundle = self.myBundle
        self.myGUI.set_bundle(self.myBundle)
        #self.myGUI.parent = self
 
        # Step 3: We attach that widget to our window
        self._main_view.pack_start(self.myGUI.widget)

        # Display everything
        self.myGUI.widget.show()
        self._main_view.show()
        self.set_canvas(self._main_view)
        self.show_all()
        
        self.scratchDir = os.path.join(self.get_activity_root(),  'instance')
        self._logger.debug("Scratch dir is %s", self.scratchDir)
        self._logger.debug("__init__() finished")
        
        self.activityRegistry = ActivityRegistry()
        #self.myGUI.statusBar.set_text(self._logger.get_logs_dir())
        

    def write_file(self,  file_path):
        self._logger.debug("write_file() called with path = %s", file_path)
        if self.myBundle.status == self.myBundle.unpacked:
            # this means we have a list of items to save, so the mime-type
            # will be set to "application/x-zebra
            self.metadata['mime_type'] = "application/x-zebra"
            
            f = open(file_path,  'w')
            for (item) in self.myBundle.objList:
                f.write(item.object_id + "\n")
            f.close()
            
        elif self.myBundle.status == self.myBundle.packed:
            x = 1
            
    def get_temp_files(self):
        self._logger.debug("get_temp_files called")
        for (item) in self.myBundle.objList:
            if item.status == self.myBundle.notInZip:
                self._logger.debug("Getting file for object = %s", item.object_id)

                jobject = datastore.get(item.object_id)
                filename = jobject.file_path
                self._logger.debug("Copying file %s", filename)

                ext = os.path.splitext(filename)[1]
                self._logger.debug("File extension = %s", ext)
                f,  temp_file = tempfile.mkstemp(ext, prefix= jobject.metadata['title']+"_HASH",   dir = self.scratchDir) 
                # the changes to the line above should preserve and uniquify our filenames  ~J
                #Might be more sensible to use the file name, but I think this'll work...............                
                self._logger.debug("Copying %s", jobject.metadata['title'])
                if (os.path.exists(filename)):
                    shutil.copy(filename,  temp_file)
                    self._logger.debug("Copying DONE");
                    self.myBundle.tempFileList.append((temp_file, jobject.metadata['title'])) 
                else:
                    self._logger.debug("Item %s does not have a file associated",  jobject.metadata['title'])
                    
                jobject.destroy()
        # this segment right here handles modified archives
        # basically modification is also handled when we click "Pack" (after adding new items)
        # just that here we unpack the existing files in the archive to put them in a new archive 
        # file. Files flagged with the "to_delete" flag are not extracted
        if (self.myBundle.status == self.myBundle.packed):
            self._logger.debug("Attempting to re-pack the archive")
            # extract all the files that are not flagged as "TO DELETE"
            for (item) in self.myBundle.objList:
                self._logger.debug("Found item with title %s and to_delete %s",  item.title,  item.to_delete)
                if ((item.status == self.myBundle.inZip) and (item.to_delete == False)):
                   try:
                        f,  temp_file = tempfile.mkstemp(item.ext, prefix= item.title+"_HASH",   dir = self.scratchDir) 
                        del f;
                        f = open(temp_file,  'wb')
                        f.write(self.myBundle.extractOne(item))
                        f.close()
                        self.myBundle.tempFileList.append((temp_file, " "))
                   except Exception,  e:
                       self._logger.error("EXCEPTION: %s",  str(e))
                       
    def updateListView(self):
        self._logger.debug("Updating List View");
        for (item) in self.myBundle.objList:
            self.add_item(item,  justDraw = True)
        
    def add_item(self,  item,  justDraw = False):
        res = 1
        if (justDraw == False):
            res = self.myBundle.add(item)
        if (res == 1):    
            if (item.icon_path):
                pixbuf = gtk.gdk.pixbuf_new_from_file(item.icon_path)
            else:
                pixbuf = None
                
            if (item.mtime):
                timeStamp = datetime.strptime(item.mtime, "%Y-%m-%dT%H:%M:%S").strftime("%m-%d-%Y  %I:%M %p")
            else:
                timeStamp = "Already in Zip"
                
            if (item.object_id):
                self.myGUI.list.append([pixbuf, item.title, timeStamp,  item.object_id])
            else:
                self.myGUI.list.append([pixbuf, item.title, timeStamp,  item.file_name])

    
    def update_file_entry(self,  archive_name):
        self._logger.debug("Sending %s to Journal", self._jobject.object_id)

        self.metadata['mime_type'] = "application/x-zip"
        self.metadata['title'] = "[PACKED]" + self.metadata['title']
        self._logger.debug("Archive_name = %s", archive_name);
        file_name = os.path.split(archive_name)[1]
        filepath = os.path.join(self.get_activity_root(), 'instance', file_name)
        self._logger.debug("Saving to %s", archive_name);
        #shutil.copy(archive_name,  filepath)
        try:
            os.chmod(archive_name, 0744)
            self._logger.debug("Trying to put %s in journal",  archive_name)
            self._jobject.file_path = archive_name
            datastore.write(self._jobject,  transfer_ownership=True)
            self._logger.debug("Written to datastore");
        except Exception,  e:
            self._logger.error("Write to datastore failed: %s", str(e))
            #self.myBundle.myGUI.list.append(
            #    ["This guy caused a general exception mess",  str(e)])

        # Sanity check - see if the object can be retrieved from the datastore
        jobject = datastore.get(self._jobject.object_id)
        self._logger.debug("Successfully retrieved archive info from data store")
        self._logger.debug("mime_type: %s  file_path: %s", jobject.metadata['mime_type'], jobject.file_path)
        self.myBundle.objList = []
        self.myGUI.list.clear()
        #f,  tmp = tempfile.mkstemp()
        self.read_file(jobject.get_file_path())
        jobject.destroy()


    def read_file(self,  file_path):       
        self._logger.debug("read_file found mime_type %s for file_path %s", self.metadata['mime_type'], file_path);

        # mime_type "application/x-zebra" indicates that the archive was
        # not packed before the activity was suspended or terminated, so
        # the file information is just a list of objects that had been
        # added to the file.
        if (self.metadata['mime_type'] == "application/x-zebra"):
            #start reading the list from the file]
            f = open(file_path,  'r')
            self.myBundle.status = self.myBundle.unpacked
            for aLine in f:
                new_item = ArchiveItem(object_id = aLine.rstrip('\n'),  default_color = self.metadata['icon-color'])
                self.myBundle.add(new_item)

            self._logger.debug("Updating list view with files from list.");
            self.updateListView()
            #self.myBundle.myGUI.statusBar.set_text(
            #    "Status: Unpacked Archive / List of Files")
        elif self.metadata['mime_type'] in self.zip_mime:
            # print a report of all files in there
            self._logger.debug("Loading file list from existing archive");
            self.myBundle.status =  self.myBundle.packed
            try:
                self.myBundle.zipFrom =  zipfile.ZipFile(file_path, "r")
            except Exception, e:
                self._logger.error(
                    "read_file: opening zip file %s failed", file_path)
                self._logger.error("Exception is %s", str(e))
                
            try:
                #disable the keep buttonlist.append
                self.activity_toolbar.keep.set_state(gtk.STATE_INSENSITIVE)
                #-------------------------------------
            except Exception,  e:
                self._logger.debug("Error changing state of keep button: %s", str(e));
                #self.myBundle.myGUI.list.append(["Error:",  str(e)])
                
            for aFile in self.myBundle.zipFrom.namelist():
                self._logger.debug("Found file: %s", aFile)
                new_item = ArchiveItem(file_name = aFile,  default_color = self.metadata['icon-color'])
                self.myBundle.add(new_item)
                
            self.updateListView()
            self.myGUI.statusBar.set_text("Status: Packed Archive")
        else:
            self._logger.debug("Unknown mime_type %s", self.metadata['mime_type']);
    def get_main_toolbar(self):
        return self.main_toolbar
