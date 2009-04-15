from Bundle import  Bundle
from sugar.activity.registry import  ActivityRegistry
import os
from sugar import mime
from sugar.datastore import datastore
import logging

class ArchiveItem:
    
    object_id = None
    mime_type = None
    file_name = None
    title = None
    status = Bundle.notInZip
    icon_path = None
    icon_color = None
    owner_icon_color = None
    activity = None
    mtime = None
    to_delete = False
    
    def __init__(self,  object_id = None,  file_name = None,  default_color = None):
        self._logger = logging.getLogger('bundle.BundleActivity')
        self._logger.setLevel(logging.DEBUG) # Show ALL messages
        
        self.owner_icon_color = default_color
        
        activityRegistry = ActivityRegistry()
        
        if (object_id):
            self.object_id = object_id
            jobject = datastore.get(object_id)
            if (jobject):
                try:
                    self.mime_type = jobject.metadata['mime_type']
                    self.title =  jobject.metadata['title']
                    
                    self.activity = jobject.metadata['activity']
                    activity_info = activityRegistry.get_activity(self.activity)
                    if (activity_info):
                        self.icon_path = activity_info.icon
                    if (jobject.metadata.has_key('icon-color')):
                        self._logger.debug("The key icon-color exists: %s", jobject.metadata.has_key('icon-color'))
                        self.icon_color = jobject.metadata['icon-color']
                        self.mtime = jobject.metadata['mtime']
                except Exception,  e:
                    self._logger.error("key errors in there:", str(e))
                    
                jobject.destroy()

        elif (file_name):
            self.file_name = file_name
            self.status = Bundle.inZip
            (self.title,  self.ext) = os.path.splitext(os.path.split(self.file_name)[1])
            self.title = self.title.rpartition("_HASH")[0]
            
            self._logger.debug("file is is %s",  self.file_name)
            self._logger.debug("extension is %s",  self.ext)
            self.mime_type = mime.get_from_file_name(self.file_name)
            self._logger.debug("mime is %s",  self.mime_type)
            activity_list = activityRegistry.get_activities_for_type(self.mime_type)
            
            just_once = 0
            for something in activity_list:
                self._logger.debug("Activities used to open this: ",  something.bundle_id)
                if just_once == 0:
                    self.activity = something.bundle_id
                    just_once = 1
            if (self.activity):
                activity_info = activityRegistry.get_activity(self.activity)
            else:
                activity_info = None
            if (activity_info):
                self.icon_path = activity_info.icon
    
    def __eq__(self,  other):
        if (self.object_id):
            return (self.object_id == other.object_id)
        elif (self.file_name):
            return (self.file_name == other.file_name)
        else:
            return False
