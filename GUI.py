#!/usr/bin/env python


# we need pygtk for the basic GUI
import pygtk
pygtk.require('2.0')

# we also need gtk, duuuh
import gtk
import pango

# this is the object chooser stuff: import the ObjectChooser class from the sugar.graphics package

from sugar.graphics.objectchooser import ObjectChooser
from sugar.graphics.toolbutton import ToolButton
from gettext import gettext as _

# All these settings might have worked under a different window manager, 
# but Sugar is not the friendly type
# Sets the border width of the window.t ObjectChooser

# and the datastore from the sugar.datastore pack. We're not using datastore yet, but you know
# we will >:)
from sugar.datastore import datastore
from sugar.graphics.toolbutton import ToolButton
import tempfile
import shutil
import os
from sugar import mime
from sugar.activity.registry import ActivityRegistry
from ArchiveItem import ArchiveItem
# this is the main class that works as a parent window

#I am doing this separately in each class, intentionally. ~J
import logging

from datetime import datetime

class GUI:
    _logger = None
    _bundle = None
    widget = None
    
    def set_bundle(self,  bundleInstance):
        self._bundle = bundleInstance;
    # this is a callback function that reacts to the event of deleting the window
    
    def delete_event(self, widget, event, data=None):
        # If you return FALSE in the "delete_event" signal handler,
        # GTK will emit the "destroy" signal. Returning TRUE means
        # you don't want the window to be destroyed.
        # This is useful for popping up 'are you sure you want to quit?'
        # type dialogs.
        print "delete event occurred"
        # Change FALSE to TRUE and the main window will not be destroyed
        # with a "delete_event".
        return False

    # this is the callback for destroying the window.
    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gtk.main_quit()

    # this is a callback for the event of clicking the "Remove" button that we
    # are going to add to the GUI. Read the init function and then come back here.
    # NO complaints, please
    def remove_cb(self, widget, data=None):
        
        # find the selected item in the TreeView component
        tree_selection = self.tree.get_selection()

        # set the selection mode of the tree to single, so people can't select multiple items
        tree_selection.set_mode(gtk.SELECTION_SINGLE)

        # get the selected item into a treeIter, which will be of TreeIterator class
        (model, treeIter) = tree_selection.get_selected()
        
        object_id = self.list.get_value(treeIter,  3)
        if (self.list.get_value(treeIter,  2) == "Already in Zip"):
            item = ArchiveItem(file_name = object_id)
            item.to_delete = True
            index = self._bundle.objList.index(item)
            self._logger.debug("Searching for %s",  item.title)
            self._logger.debug("Found at %i",  index)
            if (index > -1):
                self._logger.debug("Setting %s to DELETE",  item.title)
                self._bundle.objList[index] = item
                self._logger.debug("Succesfully set to %s",  self._bundle.objList[index] .to_delete)
        else:
            item = ArchiveItem(object_id = object_id)
            #self.list.append(["selected object id is",  object_id])
            self._bundle.erase(item)
        
        # if it's not blank, call the list field (which is of type ListStore) and delete the thing
        # once this is done, the TreeView magically updates itself
        if treeIter != None:
            self.list.remove(treeIter)

    # this is the callback method for clicking the "add" button. More explanations on what we are doing with the
    #Object Chooser will come	    
    def add_cb(self, widget, data=None):
        # this is the tricky part:
        # TRY to call an instance of the object chooser UI 
        try:
            # first create the instance, and pass it the xid of the window, a handle
            # used by the OS to show the ObjectChooser as a modal dialog box whose
            # parent is our window
            obj_chooser = ObjectChooser(self.xid,  gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
            # let's run the service now	
            result = obj_chooser.run()
    
            # apparently, according to the Browse activity source code, the response should be
            # a gtk.RESPONSE_ACCEPT. 
            if result == gtk.RESPONSE_ACCEPT:
                # get the id of the selected object (usually a hash value)
                jobject = obj_chooser.get_selected_object()
                # if it's not black [and the user actually selected som)ething]
                if jobject != None:
                    if jobject.file_path != None:
                        new_item = ArchiveItem(object_id = jobject.object_id,  default_color = self.parent.metadata['icon-color'])
                        self.parent.add_item(new_item)
                        jobject.destroy()
         # finally ... 
        finally:
            # get rid of this ObjectChooser guy
            obj_chooser.destroy()
            del obj_chooser

    def extractOne_cb(self,  widget,  data = None):
        if self._bundle.status == self._bundle.packed:
            # find the selected item in the TreeView component
            tree_selection = self.tree.get_selection()
            # set the selection mode of the tree to single, so people can't select multiple items
            tree_selection.set_mode(gtk.SELECTION_SINGLE)
            # get the selected item into a treeIter, which will be of TreeIterator class
            (model, treeIter) = tree_selection.get_selected()
            
            file_name2 = self.list.get_value(treeIter,  3)
            item = ArchiveItem(file_name = file_name2)
            self._extract_write_file(item)
    
    def _extract_write_file(self,  item):
        self._logger.debug("extract write file called for file %s",  item.file_name)
        try:
            dest_file = os.path.join(self.parent.scratchDir,  os.path.split(item.file_name)[1])
            f = open(dest_file,  'wb')
            f.write(self._bundle.extractOne(item))
            f.close()
            jobject = datastore.create()
            self._logger.debug("here's some text %s", os.path.splitext(os.path.split(item.file_name)[1])[0].rpartition("_HASH")[0])
            jobject.metadata['title'] = item.title
            jobject.metadata['mime_type'] = item.mime_type
            jobject.metadata['icon-color'] = self.parent.metadata['icon-color']
            jobject.metadata['activity'] = item.activity
            jobject.file_path = dest_file
            datastore.write(jobject)
            jobject.destroy()
        except Exception,  e:
                self._logger.debug(["Exception",  str(e)])
            
    def extractAll_cb(self,  widget,  data = None):
        if self._bundle.status == self._bundle.packed:       
            for (item) in self._bundle.objList:
                if item.status == self._bundle.inZip:
                    self._extract_write_file(item)
    
    def pack_cb(self,  widget,  data = None):
#        self.list.append(["Calling the temp files copying", ""])
        self.parent.get_temp_files()
#        self.list.append(["Zipping this stuff",  ""])
        if ((self._bundle.status == self._bundle.unpacked) or True): #bypass this condition for now, used
        # for modifying the archive ~C
            f,  temp_zip = tempfile.mkstemp(".zip",  dir = self.parent.scratchDir)
            del f
#            self.list.append(["Zipping to",  temp_zip])
            result = self._bundle.pack(temp_zip) 
            if (result == 0):
                self.parent.update_file_entry(temp_zip)
                self.statusBar.set_text(_("Status: Packed Archive"))
                self.parent.activity_toolbar.keep.set_state(gtk.STATE_INSENSITIVE)
            elif (result == -1):
                self.parent.activity_toolbar.keep.set_sensitive(True)
                # just act as if we started from scratch: empty list, unpacked state
                self._bundle.status = self._bundle.unpacked
                self.parent.metadata['mime_type'] = "application/x-zebra"
                f,  tmp2 = tempfile.mkstemp(dir = self.parent.scratchDir)
                del f
                self.list.clear()
                self.statusBar.set_text("Status: Unpacked Archive / List of Files")
                self.parent._jobject.file_path = tmp2
                self.parent.save()
          
    def buildAppearance(self):   
        # we will need a CellRenderer. Apparently GTK is too arrogant to just display
        # text in a column of a table. So it needs to display "cells", which will be rendered
        # by a CellRendererText instance
        self.cell = gtk.CellRendererText()
        self.cell2 = gtk.CellRendererText()
        self.cellIcon = gtk.CellRendererPixbuf()
        self.cell3 = gtk.CellRendererText()
        
        # first off, we will create a TreeViewColumn, which basically is a column in a table,
        # with an associated title. So far we'll just add the Name column, many more to come later
        # - not too difficult to add
        self.listColumn = gtk.TreeViewColumn(_("Name"))
        self.listColumn.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        #self.listColumn.set_expand(True)
        self.listColumn3 = gtk.TreeViewColumn(_("Date"))
        self.listColumn3.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        #self.listColumn3.set_expand(True)
        self.listColumn2 = gtk.TreeViewColumn(_("Object ID"))
        self.listColumn2.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        #self.listColumn2.set_min_width(200)
        
        # now let's create the actual storage structure that remembers what we are adding to
        # to the tree view. This is the TreeStore class
        self.list = gtk.ListStore(gtk.gdk.Pixbuf, str,  str,  str)

        # now the main GUI element, the TreeView class
        self.tree = gtk.TreeView(model = self.list) 
        self.tree.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
        
        # let's add that column in there, so we know we're not playing
        self.tree.append_column(self.listColumn)
        self.tree.append_column(self.listColumn3)
        # Only add the object ID column if you want to make sure things are going well
        #self.tree.append_column(self.listColumn2)
        
        # now, we will pack the cell into the TreeViewColumn as we would pack stuff in a VBox (see below)
        self.listColumn.pack_start(self.cellIcon, False)
        self.listColumn.pack_start(self.cell,  True)
        self.listColumn2.pack_start(self.cell2, True)
        self.listColumn3.pack_start(self.cell3,  True)
        # this one has no specific explanation, just write ith
        self.fontDesc = pango.FontDescription("sans bold 12")
        self.listColumn.add_attribute(self.cell, 'text', 1) 
        self.cell.set_property('font_desc',  self.fontDesc)
        #self.listColumn.add_attribute(self.cellIcon,  stock_id = 0)
        # this one has no specific explanation, just write ith
        self.listColumn2.add_attribute(self.cell2, 'text', 3) 
        self.listColumn3.add_attribute(self.cell3, 'text', 2)
        self.fontDesc = pango.FontDescription("sans normal 12")
        self.cell3.set_property('font_desc',  self.fontDesc)
        self.listColumn.add_attribute(self.cellIcon,  'pixbuf',  0)
        
        self.bundleToolbar = self.parent.get_main_toolbar()
        
        self.addButton = ToolButton()
        self.addButton.set_icon("plus.sugar")
        self.addButton.set_tooltip(_("Add Item"))
        self.addButton.connect("clicked", self.add_cb)
        
        self.eraseButton = ToolButton()
        self.eraseButton.set_icon("minus.sugar")
        self.eraseButton.set_tooltip(_("Remove Item"))
        self.eraseButton.connect("clicked", self.remove_cb)
        
        self.packButton = ToolButton()
        self.packButton.set_icon("pack.sugar")
        self.packButton.set_tooltip(_("Pack Bundle"))
        self.packButton.connect("clicked",  self.pack_cb)
     
        self.extractOneButton = ToolButton()
        self.extractOneButton.set_icon("unpack.sugar")
        self.extractOneButton.set_tooltip(_("Extract Item"))
        
        self.extractOneButton.connect("clicked",  self.extractOne_cb)
        
        self.extractAllButton = ToolButton()
        self.extractAllButton.set_icon("unpackall.sugar")
        self.extractAllButton.set_tooltip(_("Extract All"))
        
        self.extractAllButton.connect("clicked",  self.extractAll_cb)
        
        self.bundleToolbar.insert(self.addButton, -1)    
        self.bundleToolbar.insert(self.eraseButton, -1)
        self.bundleToolbar.insert(self.packButton, -1)
        self.bundleToolbar.insert(self.extractOneButton, -1)
        self.bundleToolbar.insert(self.extractAllButton, -1)
        
        self.mainFrame = gtk.VBox(False, 0)
        
        self.statusBar = gtk.Label(_("Status: Unpacked Archive / List of Files"))
        
        self.mainFrame.pack_start(self.statusBar,  False,  True,  0)
        # you're free to enlarge the tree as high as the window is
        self.mainFrame.pack_start(self.tree, True)
        
        # now let's add the entire container to the window
        #self.window.add(self.mainFrame)
        
        # finally, we need to call the methods to show all the created widgets:
        self.addButton.show()
        self.eraseButton.show()
        self.packButton.show()
        self.extractAllButton.show()
        self.extractOneButton.show()
        self.tree.show()
        self.statusBar.show()
        self.bundleToolbar.show()
        self.mainFrame.show()
        self.widget = self.mainFrame
        
    def __init__(self,  parent):
        self.parent = parent
        self.buildAppearance()
        self._logger = logging.getLogger('bundle.BundleActivity')
        self._logger.setLevel(logging.DEBUG) # Show ALL messages
        # self._logger.setLevel(logging.WARNING) # Ignore DEBUG/INFO msgs
        self._logger.debug("Launching GUI.")
    
    def update_row_data(self):
        aList = self._bundle.objList
        self.list.clear()
        for str in aList:
            self.list.append(str)
            
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
    bundleWindow = GUI()
    bundleWindow.main()
