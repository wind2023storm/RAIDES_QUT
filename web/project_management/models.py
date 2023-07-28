import os
from django.db import models

from adminsortable.fields import SortableForeignKey
from adminsortable.models import SortableMixin
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Board(models.Model):
    restID = models.CharField(max_length=32, default= 1, unique=True)
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="owned_boards"
    )
    members = models.ManyToManyField(User, related_name="boards")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        is_new = self.pk is None
        super().save(force_insert, force_update, using, update_fields)
        if is_new:
            self.members.add(self.owner)


class Column(SortableMixin):
    """
    restID: use for communicating with front-end.
    """
    restID = models.CharField(max_length=32, default= 1)
    title = models.CharField(max_length=255)
    board = models.ForeignKey("Board", related_name="columns", on_delete=models.CASCADE)
    column_order = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    is_valid = models.BooleanField(default=1)

    class Meta:
        ordering = ["column_order"]

    def __str__(self):
        return f"{self.title}"


class Label(models.Model):
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7)
    board = models.ForeignKey("Board", related_name="labels", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "board"], name="unique_name_board")
        ]


class Priority(models.TextChoices):
    HIGH = "H", "High"
    MEDIUM = "M", "Medium"
    LOW = "L", "Low"

def get_report_file_uploader_path(instance, filename):
    return os.path.join('task', f"{filename}")

class Task(SortableMixin):
    """
    restID: use for communicating with front-end.
    """
    restID = models.CharField(max_length=32, default= 1)
    title = models.CharField(max_length=255, blank=False, error_messages={'required': 'Enter title for the task.'})
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=1, choices=Priority.choices, default=Priority.MEDIUM
    )
    file = models.FileField(
        upload_to=get_report_file_uploader_path,
        max_length=1000,
        null=True,
        blank=True
    )
    date = models.DateField(blank=True, null=True)
    labels = models.ManyToManyField(Label, related_name="tasks")
    assignees = models.ManyToManyField(User, related_name="tasks")
    column = SortableForeignKey(Column, related_name="tasks", on_delete=models.CASCADE)
    task_order = models.PositiveIntegerField(default=0)
    is_valid = models.BooleanField(default=1)

    def __str__(self):
        return f"{self.id} - {self.title}"

    class Meta:
        ordering = ["id"]


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="comments")
    text = models.TextField()