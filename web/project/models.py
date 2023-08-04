import os
import uuid
import django.core.validators as validators

from http import HTTPStatus

from django.contrib.gis.db.models import Union
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from django.core.cache import cache, caches

from media_file.models import MediaFile
from project.managers import ProjectManager

User = get_user_model()


class Permission(models.IntegerChoices):
    """Permission class, bitwise operations are used to have a waterfall like effect. e.g., Admins also have
    read/write permissions."""
    # `Error` related to __getitem__ should be ignored as inherited meta classes have the function implemented
    READ = 1, _('Read')
    WRITE = 1 << 1 | READ[0], _('Write')
    ADMIN = 1 << 2 | WRITE[0], _('Admin')
    OWNER = 1 << 3 | ADMIN[0], _('Owner')

    @staticmethod
    def choices_less(level):
        """Returns a list of tuples where permissions are below a supplied integer"""
        return [(i, permission) for i, permission in Permission.choices if i < level]


class AustraliaStateChoices(models.TextChoices):
    ACT = 'ACT', 'Australian Capital Territory'
    NSW = 'NSW', 'New South Wales'
    NT = 'NT', 'Northern Territory'
    QLD = 'QLD', 'Queensland'
    SA = 'SA', 'South Australia'
    TAS = 'TAS', 'Tasmania'
    VIC = 'VIC', 'Victoria'
    WA = 'WA', 'Western Australia'


class Project(models.Model):
    """The Project Model, it contains Tenements, ProjectMembers and is the general backbone for the PWC

    Reverse Relations::

        project.members : ProjectMember[]
            All project "ProjectMembers"
        project.tenements : Tenement[]
            All project Tenements
    """
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    slug = models.SlugField(max_length=200, unique=True)  # This will auto generated upon object saving
    state = models.CharField(max_length=3, choices=AustraliaStateChoices.choices, default=AustraliaStateChoices.QLD)
    objective = models.CharField(max_length=250)
    locality = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    credits = models.DecimalField(default=0.0, decimal_places=2, max_digits=65,
                                  validators=[validators.MinValueValidator(0.0)])

    # # The below stuff is for the updated schema, fix whenever i guess
    # # Relationships
    # owner   = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='owned_projects', null=False)
    # biller  = models.ForeignKey(UserModel, related_name='billed_projects', on_delete=models.SET_NULL, null=True) # not sure if this is necessary, was there before so ill leave it for now
    # members = models.ManyToManyField(User, through='ProjectMember', related_name='projects',
    #                                  related_query_name='project')

    files = models.ManyToManyField(MediaFile, related_name='project_files', blank=True)

    objects = ProjectManager()

    def __str__(self):
        return self.slug

    def get_geometry(self):
        """Returns the geometry of a project which is an aggregation of all tenement polygons."""
        return self.tenements.all().aggregate(Union('area_polygons')).get('area_polygons__union')

    def get_absolute_url(self) -> str:
        return reverse('project:dashboard', kwargs={'slug': self.slug})

    def file_directory(self) -> str:
        """This path is used for storing media files using the MediaFile object"""
        return 'project/{self.slug}'

    def get_file_url(self, file_uuid) -> str:
        """Returns the download link of a specified url. Please make sure the file exists in ``self.files`` before usage."""
        return reverse('project:get_file', kwargs={'slug': self.slug, 'uuid': str(file_uuid)})

    def disk_space_usage(self) -> int:
        """Total disk space used by uploaded project files in bytes"""
        return MediaFile.bytes_sum(self.files.all().only('file'))

    def disk_space_usage_str(self) -> str:
        """Total disk space used by uploaded project files formatted to appropriate units."""
        return MediaFile.bytes_sum_str(self.files.all().only('file'))

    def save(self, *args, **kwargs):
        """Override the save method to auto-generate a slug and add the owner to members if not already exist"""
        if not self.pk:
            # If the project hasn't been created yet, it won't have a PK, thus we can auto-generate the slug
            self.slug = slugify(self.name)

            # The slug should be unique and if it exists already, append a counter to the end
            suffix = Project.objects.filter(slug__startswith=self.slug).count()

            if suffix:
                self.slug = f'{self.slug}-{suffix + 1}'

        # Have to save the model before accessing many-to-many fields
        super().save(*args, **kwargs)

        # Add the owner to the members if the owner isn't in the members field
        # if self.owner not in self.members.all():
        #     self.members.add(self.owner, through_defaults={'permission': Permission.OWNER})

    def add_member(self, user, permission) -> bool:
        try:
            ProjectMember.objects.create(project=self, user=user, permission=permission)
            return True
        except Exception:
            return False
    #
    # def is_owner(self, user) -> bool:
    #     return True if self.owner == user else self.has_perm(user, Permission.OWNER)
    #
    # def is_read(self, member) -> bool:
    #     return self.has_perm(user, Permission.READ)
    #
    # def is_write(self, member) -> bool:
    #     return self.has_perm(user, Permission.WRITE)
    #
    # def is_admin(self, member) -> bool:
    #     return self.has_perm(user, Permission.ADMIN)
    #
    # def has_perm(self, user, permission: Permission, allow_sudo=False) -> bool:
    #     """Checks to see if a user has some permission.
    #
    #     As this function is heavily used and performs queries on many-to-many relationship fields, the result for the
    #     supplied arguments is cached for a period of 10 seconds.
    #
    #     Caching is mostly relevant for using the Django Template Tags "``project|is_admin:request.user``" since
    #     it's generally called more than once per template
    #
    #     Parameters
    #     ----------
    #     user : User
    #         The user to check permissions for
    #     permission : Permission
    #         The permission to check for
    #     allow_sudo : bool, default = True
    #         Whether the permission check should allow Django super-users to bypass the permission requirements
    #
    #     Returns
    #     -------
    #         bool : Whether the user has the expected permission
    #     """
    #     # Allow super-users to bypass the permission check if the flag is set
    #     if allow_sudo and user.is_superuser:
    #         return True
    #
    #     # Check if this query has been performed recently
    #     # cache_key = f'Project:{self.id}:has_perm:{user.id}:{permission}'
    #     # cache_value = cache.get(cache_key)
    #     #
    #     # # If the cached value exists just return it
    #     # if cache_value is not None:
    #     #     return cache_value
    #
    #     # Otherwise check if the member exists within the project
    #     try:
    #         member = self.members.get(user=user)
    #     except ObjectDoesNotExist:
    #         return False
    #
    #     # Perform binary operation to check if their permission matches
    #     has_perm = member.permission & permission == permission
    #
    #     # Store the result in the cache for 10 seconds
    #     # cache.set(cache_key, has_perm, 10)
    #
    #     return has_perm

    class Meta:
        ordering = ['last_modified', 'created_at']


class ProjectMember(models.Model):
    """
    This model manages a users permissions within a certain project which are independant of site-wide permissions,
    e.g., they may have read/write or administrative access to a specific project
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='memberships')
    # TODO: Implement some kind of conditional uniqueness constraint that only allows one `Permission.OWNER`
    permission = models.PositiveIntegerField(choices=Permission.choices, default=Permission.READ, null=False)
    join_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A User can only have one permission type per project
        unique_together = ('project', 'user',)
        ordering = ['-permission']

    def has_permission(self, permission):
        return self.permission & permission == permission

    def is_read(self):
        return self.has_permission(Permission.READ)

    def is_write(self):
        return self.has_permission(Permission.WRITE)

    def is_admin(self):
        return self.has_permission(Permission.ADMIN)

    def is_owner(self):
        return self.has_permission(Permission.OWNER)

    def __str__(self):
        return self.user.full_name
