# MediaFile Guide
The ``MediaFile`` model is a dynamic file upload/download model for usage across
the entire platform. Any model can utilize the MediaFile by introducing a many-to-many field.

A MediaFiles fields are read-only to keep the filesystem safe (except the tag field).

An example object utilizing a many-to-many field:

    class ExampleModel(models.Model):
        name = models.CharField(max_size=256)
        files = models.ManyToManyField(MediaFile, related_name='example_files', blank=True)

        def file_directory(self):
            """Returns the directory in which ExampleModel files would be saved"""
            return f"example/{self.name}/"

Note that the model implements a `file_directory()` method. This is commonplace across the platform, and is required 
when using the built-in MediaFile Forms.

The majority of these can be handled manually within views, but it'd be nice to have a modular version at some point.

## Creating a MediaFile and MediaFileRelationship:
MediaFile also has an intermediate class that allows a *relationship* which operates similarly to a graph,
in that a file can have many parents and many children.
    
Create some Dummy files using the ``SimpleUploadedFile`` class:
    
    parent_file = SimpleUploadedFile("parent_file.txt", b"file contents")
    child_file = SimpleUploadedFile("child_file.txt", b"file contents")

Create some MediaFile objects under an instance directory (note that the ``file_path`` is not stored in the database).
    
    example = ExampleModel.objects.create(name="Example Test")
    mf1 = MediaFile.objects.create(file=parent_file, tag=MediaFile.DATASET, file_path=example.file_directory())
    mf2 = MediaFile.objects.create(file=child_file, tag=MediaFile.DOCUMENT, file_path=example.file_directory())
    
    example.files.add(mf1, mf2)
    
    >>> print(mf1.file.path)
    %DJANGO_PATH%/media_root/media/example/Example Test/child_file.txt

If a file is a descendant of another (in the instance that a file was created from another as seen in the DataCleaner)
a relationship can be created as follows

    MediaFileRelationship.objects.create(parent=mf1, child=mf2)

And given the versatility of a file relationships, the files can be accessed in multiple different ways to fit your usage:

    >>> print(mf1.children.all())
    <QuerySet [<MediaFile: child_file.txt>]>

    >>> print(mf2.parents.all())
    <QuerySet [<MediaFile: parent_file.txt>]>

    >>> print(example.files.all())
    <QuerySet [<MediaFile: child_file.txt>, <MediaFile: parent_file.txt>]>

    >>> print(example.files.filter(tag=MediaFile.DOCUMENT).all())
    <QuerySet [<MediaFile: parent_file.txt>]>
    
## Downloading a File:
Using the ``to_file_response()`` function, you can easily serve files to the client. It's important to consider checking whether
a user has access to the file before serving it, as a UUID can be forged by anyone. E.g., only allow file download
through an objects many-to-many field for example in the ``ExampleModel`` used in previous examples.

Example ``urls.py``:
    
    app_name = 'example'

    urlpatterns = [
        path('', views.home_view, name='home'),
        path('/<int:example_id>/<str:file_uuid>', views.get_file, name='file_download'),
    ]
    
Example ``views.py``:
    
    def get_file(request, example_id, file_uuid):
        """Returns the file as a response"""
        example = ExampleModel.objects.get(id=example_id)

        # Query for the file within the example is safer as it can mitigate UUID forgery
        file = example.files.get(id=file_uuid)

        return file.to_file_response()
    
    def home_view(request):
        """Page with a download link to a file"""
        example = ExampleModel.objects.get(name="Example Test")
        file = example.files.first()

        context = {
            'file_url': reverse('example:file_download' kwargs={
                'example_id': example.id, 
                'file_uuid': file.id
            })
        }
        return render(request, "example/template.html", context)
    

Example ``template.html``:
    
    <a href="{{ file_url }}" download>Click to Download</a>

*Note: You cannot generate the URL in the template using ``{% url ... %}`` as you can't put context variables inside 
tags e.g., ``{{ request.user }}``. Though alternatively you can just use Javascript and AJAX.*

## MediaFile Deletion:
- When a MediaFile is deleted, the file attached to it is automatically deleted from the server drive.
- As ManyToMany fields are not affected by ``models.CASCADE``, it is important to perform manual deletion when necessary.
Using signals is probably the best solution.
- The Django Admin page will show all relationships between files on their respective pages.
- If you delete the local database, you'll have to delete the uploaded files manually.

## Potential Upgrades
- File size limits for a file
- Project-wise file size limit 
- A FileResponse function that compresses a queryset of files before serving (e.g., in a zip file)