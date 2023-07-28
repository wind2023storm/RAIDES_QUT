from django.contrib import admin

from tms.models import Tenement, TenementTask, WorkProgram, WorkProgramReceipt  # , TenementTarget

# Register your models here.


class TenementTaskInline(admin.TabularInline):
    """Inline Task table to be displayed on the Tenement Admin page"""
    model = TenementTask
    search_fields = ('tenement', 'authority', 'name', 'archived',)
    list_filter = ('authority',)
    fields = ('tenement', 'name', 'description', 'authority', 'due_date', 'completion_date')
    extra = 0


class TenementWorkProgramInline(admin.TabularInline):
    """Inline WorkProgram table to be displayed on the Tenement Admin page"""
    model = WorkProgram
    fields = ('slug', 'year', 'discipline', 'activity', 'estimated_expenditure', 'actual_expenditure',)
    readonly_fields = ('slug', 'actual_expenditure',)
    extra = 0


@admin.register(Tenement)
class TenementAdmin(admin.ModelAdmin):
    list_display = ('permit_id', 'project', 'task_count')  # , 'target_count', )
    search_fields = ('permit_type', 'permit_number', 'ea_number', 'project', 'permit_type')
    fields = ('permit_state', 'permit_type', 'permit_number', 'permit_status', 'project',)
    readonly_fields = ('permit_state', 'permit_type', 'permit_number', 'permit_status')
    inlines = [
        TenementTaskInline,
        TenementWorkProgramInline,
    ]

    def task_count(self, instance):
        return instance.tasks.count()


@admin.register(TenementTask)
class TenementTaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenement', 'authority', 'description', 'attachments',)
    list_filter = ('authority',)
    search_fields = ('tenement', 'authority', 'name', 'archived',)
    fields = ('tenement', 'name', 'description', 'authority', 'due_date', 'completion_date')
    readonly_fields = ('tenement',)

    def attachments(self, instance):
        return instance.files.count()


class WorkProgramReceiptInline(admin.TabularInline):
    model = WorkProgramReceipt
    fields = ('id', 'name', 'description', 'cost', 'file')
    readonly_fields = ('id',)
    extra = 0


@admin.register(WorkProgram)
class WorkProgramAdmin(admin.ModelAdmin):
    list_display = ('slug', 'tenement', 'work_program', 'year', 'estimated_expenditure', 'actual_expenditure',)
    fields = ('tenement', 'year', 'discipline', 'activity', 'estimated_expenditure', 'actual_expenditure', 'units', 'quantity',)
    readonly_fields = ('slug', 'actual_expenditure',)
    inlines = [
        WorkProgramReceiptInline
    ]

    def work_program(self, instance):
        return instance.__str__()



