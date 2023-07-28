import os
import uuid
from mimetypes import guess_type

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum, QuerySet
from django.http import FileResponse
from django.utils.translation import gettext_lazy as _

User = get_user_model()


def instanced_file_path(instance, filename):
    return os.path.join(f'%s/%s' % (instance.file_path, filename))

class MediaFile(models.Model):
    """An MediaFile is a way to have one model that stores files for multiple different models easily
    much cleaner than the current process file model

    Basic Implementation and Usage: ::

        # Model implementation
        class ExampleModel(models.Model):
            files = models.ManyToManyField(MediaFile, related_name='example_files', blank=True)

            def file_directory(self):
                return self.some_file_directory

        # Basic setup
        parent_file = SimpleUploadedFile("parent_file.txt", b"file contents")
        child_file = SimpleUploadedFile("child_file.txt", b"file contents")

        # Create some files, the filename is generated automatically
        mf1 = MediaFile.objects.create(file=parent_file, tag=MediaFile.DATASET, file_path=project.file_directory())
        mf2 = MediaFile.objects.create(file=child_file, tag=MediaFile.DATASET, file_path=project.file_directory())

        # Create a relationship, this is optional
        MediaFileRelationship.objects.create(parent=mf1, child=mf2)

        # Add the files to our models file field
        project.files.add(mf1, mf2)

        # Querying
        datasets = model.files.filter(tag=MediaFile.DATASET)

        # Getting dependants
        print(mf1.children.all())
        <QuerySet [<MediaFile: child_file.txt>]>
        print(mf2.parents.all())
        <QuerySet [<MediaFile: parent_file.txt>]>
    """

    class Extensions:
        """For use in the CreateMultipleMediaFileForm allowed_extensions"""
        DOCUMENT = ['doc', 'dot', 'docx', 'dotx', 'docm', 'dotm', 'txt', 'md', 'rtf']
        PDF = ['pdf']
        IMAGE = ['png', 'jpg', 'jpeg', 'jpe', 'bmp', 'tif', 'tiff']
        EXCEL = ['xls', 'xlt', 'xla', 'xlsx', 'xltx', 'xlsm', 'xltm', 'xlam', 'xlsb']
        DATA = ['csv', 'xml', 'json', 'yaml']
        POWERPOINT = ['ppt', 'pot', 'pps', 'ppa', 'pptx', 'potx', 'ppsx', 'ppam', 'pptm', 'potm', 'ppsm']
        MODELS = ['pickle', 'mdl']  # TODO: Figure out what extensions models will have
        COMPRESSED = ['zip', 'gzip', '7z', 'rar', 'tar', 'tar.gz', 'tar.lz']

    DATASET = 0
    DOCUMENT = 1
    REPORT = 2
    FORM = 3

    CLEANER = 4
    APPLICATION = 5
    COMPLIANCE = 6
    RECEIPT = 7
    MODEL = 8
    TASK = 9
    CLEANER_REPORT = 10
    ANALYSIS_REPORT = 11

    TAG_CHOICES = (
        (DATASET, _('Dataset')),
        (DOCUMENT, _('Document')),
        (REPORT, _('Report')),
        (FORM, _('Form')),
        (CLEANER, _('Cleaner')),
        (APPLICATION, _('Application')),
        (COMPLIANCE, _('Compliance')),
        (RECEIPT, _('Receipt')),
        (MODEL, _('Model')),
        (TASK, _('Task')),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=256, editable=True)
    content_type = models.CharField(max_length=256, editable=False)
    file = models.FileField(upload_to=instanced_file_path, editable=True, max_length=500)  # editable=False
    file_size = models.PositiveIntegerField(editable=False)

    date_created = models.DateTimeField(auto_now_add=True)

    # Change this to a many-to-many field if you want files to have more than one tag
    # TODO: If we go with Postgres we can use an ArrayField
    tag = models.PositiveIntegerField(choices=TAG_CHOICES, null=True)

    # This field is used to maintain a relationship between files, e.g., a Dataset and a Dataclean or Report
    # Where the dataset is the parent and the dataclean is a child
    children = models.ManyToManyField('self', related_name='parents', symmetrical=False,
                                      through='MediaFileRelationship')

    def __init__(self, *args, **kwargs):
        """Initialize the file path from the keyword argument, the file_path argument is not stored in the database"""
        self.file_path = kwargs.pop('file_path', 'misc')

        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Override the default save method to autopopulate the filename and content_types from the uploaded file"""

        self.filename = str(self.file)
        self.file_size = self.file.size
        self.content_type, self.encoding = guess_type(self.file.path, strict=False)

        super().save(*args, **kwargs)

        return self

    @property
    def base_name(self) -> str:
        """The files base name on the disk"""
        return os.path.basename(self.file.name)

    @property
    def file_size_str(self) -> str:
        """Returns the files size as a formatted string using MediaFile.format_file_size()"""
        return MediaFile.format_bytes(self.file_size)

    @staticmethod
    def format_bytes(size: int) -> str:
        """Converts a file size in bytes to a formatted string of appropriate size and units.

        Examples: ::

        >>> one_kilobyte = 1024
        >>> print(MediaFile.format_bytes(one_kilobyte))
        1.00 KB

        >>> two_million_bytes = 2000000
        >>> print(MediaFile.format_bytes(two_million_bytes))
        1.91 MB

        Parameters
        ----------
        size : int
            File size in bytes

        Returns
        -------
            File size formatted as string of appropriate units.
        """
        try: 
            if size < 1024:
                base, unit = 1, 'B'
            elif size < 1024 ** 2:
                base, unit = 1024, 'KB'
            elif size < 1024 ** 3:
                base, unit = 1024 ** 2, 'MB'
            elif size < 1024 ** 4:
                base, unit = 1024 ** 3, 'GB'
            else:
                base, unit = 1024 ** 4, 'TB'
            
            return '{:,.2f} {}'.format(size / base, unit)
        except:
            return 0

    @staticmethod
    def bytes_sum(queryset: QuerySet['MediaFile']) -> int:
        """Returns the sum of all file sizes (in bytes) within the supplied MediaFile queryset"""
        bytes_sum = queryset.aggregate(Sum('file_size'))['file_size__sum']

        return bytes_sum if bytes_sum else 0

    @staticmethod
    def bytes_sum_str(queryset: QuerySet['MediaFile']) -> str:
        """Returns the sum of all file sizes within the supplied MediaFile queryset formatted by appropriate units"""
        return MediaFile.format_bytes(MediaFile.bytes_sum(queryset))

    def to_file_response(self):
        """Returns the file as a FileResponse, typically used in downloading a file."""
        file_path = self.file.path
        file_data = open(file_path, "rb")

        return FileResponse(file_data, filename=self.filename, content_type=self.content_type, as_attachment=True)

    def __str__(self):
        return str(self.filename)


class MediaFileRelationship(models.Model):
    """Used to create a parent/child relationship between two files. e.g., a Dataset being the parent and a Report
    being the child"""
    parent = models.ForeignKey(MediaFile, on_delete=models.CASCADE, related_name="+")
    child = models.ForeignKey(MediaFile, on_delete=models.CASCADE, related_name="+")

    class Meta:
        # These constraints are supposed to make it such that a media file can't be a child/parent of itself.
        # needs testing though.
        constraints = [
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_unique_relationships",
                fields=["parent", "child"]
            ),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_prevent_self_add",
                check=~models.Q(parent=models.F("child")),
            ),
        ]


# THE BELOW MODEL DEMONSTRATES HOW TO USE MANYTOMANY FIELDS
# they are very easy to set up in django and mitigates the need to have nested queries
# which makes for cleaner code and minimises the number of queries to retrieve related objects
"""
class FileTest(models.Model):
    # This model demonstrates the power of a many-to-many field
    name = models.CharField(max_length=20)
    files = models.ManyToManyField(MediaFile, related_name="file_tests", related_query_name="file_test")

    @staticmethod
    def related_name_example():
        # We can use the related_name to return ALL FileTests that store the MediaFile
        media = MediaFile(filename='media_file_example')
        media.save()

        # Create a bunch of tests we can store a MediaFile into
        test1 = FileTest(name="test1")
        test1.save()
        test2 = FileTest(name="test2")
        test2.save()

        # Add the file to a bunch of tests
        test1.files.add(media)
        test2.files.add(media)

        # related_name returns all of the FileTest objects that have that MediaFile in it
        all_tests = media.file_tests.all()

        print("related_name example\n", '-'*20)
        print("media.file_tests.all() =", [x.name for x in all_tests])
        print('-'*20)

        test1.delete()
        test2.delete()
        media.delete()

        # Result:
        # related_name example
        # --------------------
        # media.file_tests.all() = ['test1', 'test2']

        return True

    @staticmethod
    def related_query_name_example():
        # We can use the related_query_name to get all MediaFile objects from within a single FileTest object
        media1 = MediaFile(filename='media1')
        media1.save()
        media2 = MediaFile(filename='media2')
        media2.save()

        test = FileTest(name="test")
        test.save()

        test.files.add(media1, media2)

        # related_query_name returns all of the MediaFiles 
        print("related_query_name examples\n", '-'*20)
        all_media = MediaFile.objects.filter(file_test__name='test').all()

        # doing the above is much cleaner than doing as it's easier to tell that the above
        # query is trying to get MediaFiles 
        all_media_bad = FileTest.objects.get(name='test').files.all()
        
        
        print("MediaFile.objects.filter(file_test__name='test').all() =", [x.filename for x in all_media])
        print("FileTest.objects.get(name='test').files.all() =", [x.filename for x in all_media_bad])
        print('-'*20)

        media1.delete()
        media2.delete()
        test.delete()

        # Result:
        # related_query_name examples
        # --------------------
        # MediaFile.objects.filter(test__name='test').all() = ['media1', 'media2']
        # FileTest.objects.get(name='test').files.all() = ['media1', 'media2']

        return True
"""
