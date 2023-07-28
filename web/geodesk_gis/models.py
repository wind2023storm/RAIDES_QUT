import os
from django.db import models

def get_map_file_uploader_path(instance, filename):
    return os.path.join('map_files', f"{filename}")
    
class MapFile(models.Model):
    """
    Model to store csv map file with coordinates and info points
    """
    header_row = models.IntegerField(default=None, null=True)
    expected_filename = models.CharField(max_length=128, null=True, blank=True)
    file = models.FileField(
        upload_to=get_map_file_uploader_path,
        max_length=1000,
        null=True,
        blank=True
    )
    
    def exact_filename(self):
        return os.path.basename(self.file.name)

class CropFile(models.Model):
    """
    Selected image crop from the magnetic density map
    """
    expected_filename = models.CharField(max_length=128, null=True, blank=True)
    file = models.FileField(
        upload_to=get_map_file_uploader_path,
        max_length=1000,
        null=True,
        blank=True
    )
    
    def exact_filename(self):
        return os.path.basename(self.file.name)