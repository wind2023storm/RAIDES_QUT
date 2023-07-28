from django.contrib import admin
from django.utils.safestring import mark_safe

from project.models import ProjectMember, Project
from media_file.models import MediaFile

# Register your models here.


class ProjectMemberAdmin(admin.TabularInline):
    model = ProjectMember
    list_display = ('id', 'user', 'permission', 'join_date')
    readonly_fields = ('join_date',)
    fields = ('user', 'permission', 'join_date')
    extra = 0


class ProjectFilesAdmin(admin.TabularInline):
    verbose_name = "Project File"
    model = Project.files.through
    fields = ['file', 'tag', 'content_type', 'size', 'date_created']
    readonly_fields = ['file', 'tag', 'content_type', 'size', 'date_created']
    extra = 0

    def file(self, instance):
        url = instance.project.get_file_url(instance.mediafile.id)
        return mark_safe(f'<a href="{url}" download="download">{instance.mediafile.filename}</a>')

    def tag(self, instance):
        return instance.mediafile.get_tag_display()

    def content_type(self, instance):
        return instance.mediafile.content_type

    def size(self, obj):
        return obj.mediafile.file_size_str

    def date_created(self, obj):
        return obj.mediafile.date_created


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'owner', 'credits', 'disk_space_usage', 'tenement_count', 'member_count', 'created_at', 'last_modified')  # , 'biller'
    search_fields = ('name', 'slug', 'owner', 'locality')
    readonly_fields = ('disk_space_usage', 'files_count',)
    fields = ('name', 'slug', 'state', 'owner', 'objective', 'locality', 'credits', 'files_count', 'disk_space_usage',)
    exclude = ('files',)
    inlines = [
        ProjectMemberAdmin,
        ProjectFilesAdmin,
    ]

    def disk_space_usage(self, obj):
        return obj.disk_space_usage_str()

    def files_count(self, obj):
        return obj.files.count()

    def member_count(self, obj):
        return obj.members.count()

    def tenement_count(self, obj):
        return obj.tenements.count()
