from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from project.models import Project, ProjectMember, Permission
from media_file.models import MediaFile, MediaFileRelationship
from tms.utils import scraper
from django.shortcuts import redirect
import string
import random

User = get_user_model()


def create_dummy_file(filename):
    """Creates a dummy file for model testing purposes"""
    random_byte_string = ''.join(random.choices(string.ascii_lowercase, k=random.randint(10, 10000))).encode()
    return SimpleUploadedFile(filename, random_byte_string)


def create_dummy_files(project):
    """Creates some dummy files."""

    random_byte_string = ''.join(random.choices(string.ascii_lowercase, k=random.randint(10, 10000))).encode()

    parent_file = SimpleUploadedFile("parent_file.csv", b"a,b,c,d,e,")
    child_file = SimpleUploadedFile("child_file.txt", random_byte_string)

    # Create some files, the filename is generated automatically
    mf1 = MediaFile.objects.create(file=parent_file, tag=MediaFile.DATASET, file_path=project.file_directory())
    mf2 = MediaFile.objects.create(file=child_file, tag=MediaFile.DATASET, file_path=project.file_directory())

    MediaFileRelationship.objects.create(parent=mf1, child=mf2)

    project.files.add(mf1, mf2)


def platform_debug_setup_view(request):
    """This is just a temporary debug setup view,
    creates a superuser, some users and a couple of projects/tenements
    Logins::
        admin@email.com//admin : superuser
        user1@email.com//pass : user
        user2@email.com//pass : user
        user3@email.com//pass : user
    """
    from django.contrib.auth import login

    # Creates/Logs in a new superuser
    su = User.objects.create_superuser('admin@email.com', 'admin', first_name='Mein',
                                            last_name='Luftkissenfahrzeug')
    login(request, su)

    u1 = User.objects.create_user('user1@email.com', 'pass', first_name='George', last_name='Costanza')
    u2 = User.objects.create_user('user2@email.com', 'pass', first_name='Ronald', last_name='Weasley')
    u3 = User.objects.create_user('user3@email.com', 'pass', first_name='Hubert', last_name='Cumberdale')
    u4 = User.objects.create_user('user4@email.com', 'pass', first_name='Geraldine', last_name='Willis')
    u1.save()
    u2.save()
    u3.save()
    u4.save()

    # Creates a project
    project1 = Project.objects.create(**{
        'name': 'Owner Project',
        'owner': request.user,
        'objective': 'owner test',
        'locality': 'someplace neat',
        'credits': 12345
    })
    ProjectMember.objects.create(project=project1, user=su, permission=Permission.OWNER)
    ProjectMember.objects.create(project=project1, user=u1, permission=Permission.WRITE)
    ProjectMember.objects.create(project=project1, user=u2, permission=Permission.READ)
    ProjectMember.objects.create(project=project1, user=u3, permission=Permission.ADMIN)
    ProjectMember.objects.create(project=project1, user=u4, permission=Permission.ADMIN)

    create_dummy_files(project1)

    # Create a second project
    project2 = Project.objects.create(**{
        'name': 'Admin Project',
        'owner': u1,
        'objective': 'admin test',
        'locality': 'someplace even cooler',
        'credits': 42
    })
    ProjectMember.objects.create(project=project2, user=su, permission=Permission.ADMIN)
    ProjectMember.objects.create(project=project2, user=u2, permission=Permission.READ)
    ProjectMember.objects.create(project=project2, user=u4, permission=Permission.ADMIN)

    create_dummy_files(project2)

    # Create a second project
    project3 = Project.objects.create(**{
        'name': 'Write Project',
        'owner': u1,
        'objective': 'write test',
        'locality': 'someplace even cooler',
        'credits': 9001
    })
    ProjectMember.objects.create(project=project3, user=su, permission=Permission.WRITE)
    ProjectMember.objects.create(project=project3, user=u2, permission=Permission.ADMIN)
    ProjectMember.objects.create(project=project3, user=u4, permission=Permission.ADMIN)

    create_dummy_files(project3)

    # Create a second project
    project4 = Project.objects.create(**{
        'name': 'Read Project',
        'owner': u1,
        'objective': 'read test',
        'locality': 'someplace even cooler',
        'credits': 1337
    })
    ProjectMember.objects.create(project=project4, user=su, permission=Permission.READ)
    ProjectMember.objects.create(project=project4, user=u2, permission=Permission.ADMIN)
    ProjectMember.objects.create(project=project4, user=u4, permission=Permission.ADMIN)

    create_dummy_files(project4)

    # Create a second project
    project5 = Project.objects.create(**{
        'name': 'nonmember',
        'owner': u1,
        'objective': 'nonmember test',
        'locality': 'someplace even cooler',
        'credits': 1234
    })
    ProjectMember.objects.create(project=project5, user=u2, permission=Permission.READ)
    ProjectMember.objects.create(project=project5, user=u3, permission=Permission.WRITE)
    ProjectMember.objects.create(project=project5, user=u4, permission=Permission.ADMIN)

    create_dummy_files(project5)

    # Adds some tenements to the project
    t1, _ = scraper.scrape_tenement('QLD', 'EPM', '28118')
    t2, _ = scraper.scrape_tenement('QLD', 'EPM', '28119')
    t1.project = project1
    t2.project = project1
    t1.save()
    t2.save()

    t3, _ = scraper.scrape_tenement('QLD', 'EPM', '28120')
    t4, _ = scraper.scrape_tenement('QLD', 'EPM', '28121')
    t3.project = project2
    t4.project = project2
    t3.save()
    t4.save()

    t5, _ = scraper.scrape_tenement('QLD', 'EPM', '28122')
    t6, _ = scraper.scrape_tenement('QLD', 'EPM', '28123')
    t5.project = project3
    t6.project = project3
    t5.save()
    t6.save()

    t7, _ = scraper.scrape_tenement('QLD', 'EPM', '28116')
    t8, _ = scraper.scrape_tenement('QLD', 'EPM', '28117')
    t7.project = project4
    t8.project = project4
    t7.save()
    t8.save()

    return redirect('project:index')