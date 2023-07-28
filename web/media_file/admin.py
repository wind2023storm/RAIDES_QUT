from django.contrib import admin

from . import models

# Register your models here.


class MediaFileChildrenAdmin(admin.TabularInline):
    model = models.MediaFile.children.through
    fk_name = 'parent'
    verbose_name = "Child"
    verbose_name_plural = "Children"
    readonly_fields = ('file',)
    extra = 0

    def file(self, obj):
        return obj.child.file


class MediaFileParentAdmin(admin.TabularInline):
    model = models.MediaFile.children.through
    fk_name = 'child'
    verbose_name = "Parent"
    verbose_name_plural = "Parents"
    readonly_fields = ('file',)
    extra = 0

    def file(self, obj):
        return obj.parent.file


@admin.register(models.MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'content_type', 'file_size_str', 'date_created', 'file')
    search_fields = ('filename',)
    # readonly_fields = ('file', 'content_type', 'file_size_str', 'date_created',)
    readonly_fields = ('content_type', 'date_created',)
    list_editable = ('file',)
    list_display_links = ('filename',)

    inlines = (
        MediaFileParentAdmin,
        MediaFileChildrenAdmin,
    )

    def size(self, obj):
        return obj.file_size_str
