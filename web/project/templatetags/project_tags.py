from django import template
from django.template.loader import get_template
from django.template.base import Node, token_kwargs
from typing import Union
from django.contrib.auth import get_user_model

from project.models import Project, Permission, ProjectMember

User = get_user_model()

register = template.Library()


@register.filter
def is_owner(project, member) -> bool:
    """Checks if a user is an admin

    Examples::

        {% if project|is_owner:request.user %}
            ...
        {% endif %}
    """
    if isinstance(project, Project) and isinstance(member, ProjectMember):
        return member.is_owner()
    else:
        return False


@register.filter
def is_admin(project, member) -> bool:
    """Checks if a member is an admin

    Examples::

        {% if project|is_admin:member %}
            ...
        {% endif %}
    """
    if isinstance(project, Project) and isinstance(member, ProjectMember):
        return member.is_admin()
    else:
        return False


@register.filter
def is_write(project, member) -> bool:
    """Checks if a member has write permissions

    Examples::

        {% if project|is_write:member %}
            ...
        {% endif %}
    """
    if isinstance(project, Project) and isinstance(member, ProjectMember):
        return member.is_write()
    else:
        return False


@register.filter
def is_read(project, member) -> bool:
    """Checks if a member has write permissions

    Examples::

        {% if project|is_read:member %}
            ...
        {% endif %}
    """
    if isinstance(project, Project) and isinstance(member, ProjectMember):
        return member.is_read()
    else:
        return False
