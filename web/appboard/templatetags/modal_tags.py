from django import template
from django.template.loader import get_template
from django.template.base import Node, token_kwargs
from typing import Union
from django.contrib.auth import get_user_model


UserModel = get_user_model()

register = template.Library()


class ModalNode(Node):
    def __init__(self, nodelist, id, title, size="lg", cancel_text='Cancel', **kwargs):
        """

        Parameters
        ----------
        nodelist
        id
        title
        size
        cancel_text
        kwargs
        """
        self.nodelist = nodelist
        self.data = {
            'id': id,
            'title': title,
            'size': size,
        }

    def render(self, context, **kwargs):
        return get_template("appboard/macros/modal.html").render({
            'request': context['request'],
            'content': self.nodelist.render(context),
            **self.data,
        })


class ModalFormNode(Node):
    def __init__(self, nodelist, id, title, size='lg', action='', method='', enctype='', cancel_text='Cancel', submit_text='Submit', submit_type='submit', submit_class='btn-ofx-green', btn_type="submit", **kwargs):
        """
        Parameters
        ----------
            id : str
                ID for both the modal and the button for use in identifying requests.
            title : str
                String to be shown in the header of the modal card
            action : str
                Action to be taken upon submission
            method : str
                Whether the form is a POST or GET request
            cancel_text : str, default='Cancel'
                Text shown on the cancel or close button
            submit_text : str, default='Submit'
                Text to be shown on the submission button.
            submit_class : str, default='btn-ofx-green'
                Any extra classes to be added to the submit button
        """
        # super().__init__(nodelist, id, title, size, **kwargs)

        self.nodelist = nodelist
        self.data = {
            'id': id,
            'title': title,
            'size': size,
            'action': action,
            'enctype': enctype,
            'cancel_text': cancel_text,
            'submit_text': submit_text,
            'submit_type': submit_type,
            'submit_class': submit_class,
            'btn_type': btn_type,
            'kwargs': kwargs,
        }

    def render(self, context, **kwargs):
        return get_template("appboard/macros/modal_form.html").render({
            'request': context['request'],
            'content': self.nodelist.render(context),
            **self.data,
        })


@register.tag('modal')
def show_modal(parser, token):
    """Creates a standard formatted modal using /pwc/macros/modal_form.html as a template.
    All the contents between the tags are placed within the modal body.

    The general usage for the ``modalform`` requires a ``csrf_token``::

        {% modal id='modalName' title='This is the Modal Title'
            {{ csrf_token }}
            {{ form.as_p }}
        {% endmodal %}

    A button to open the modal can be linked as such, where ``modalName`` is concatenated with ``Modal``::

        <button data-toggle="modal" data-target="#modalNameModal">

    Returns
    -------
        modal : ModalNode
            The modal HTML rendered with the contents and variables
    """
    token_name, *bits = token.split_contents()
    nodelist = parser.parse(('endmodal',))

    args = {}
    for bit in bits:
        k, v = bit.split('=')
        args[k] = v.strip('"').strip("'")

    parser.delete_first_token()
    return ModalNode(nodelist, **args)


@register.tag('modalform')
def show_modalform(parser, token):
    """Creates a standard formatted modal using /pwc/macros/modal_form.html as a template.
    All the contents between the tags are placed within the modal body.

    The general usage for the ``modalform`` requires a ``csrf_token``::

        {% modalform id='modalName' title='This is the Modal Title'
            {{ csrf_token }}
            {{ form.as_p }}
        {% endmodalform %}

    A button to open the modal can be linked as such, where ``modalName`` is concatenated with ``Modal``::

        <button data-bs-toggle="modal" data-bs-target="#modalNameModal">

    Returns
    -------
        modal : ModalFormNode
            The modal HTML rendered with the contents and variables
    """
    token_name, *bits = token.split_contents()
    nodelist = parser.parse(('endmodalform',))

    args = {}
    for bit in bits:
        k, v = bit.split('=')
        args[k] = v.strip('"').strip("'")

    parser.delete_first_token()
    return ModalFormNode(nodelist, **args)

#
# @register.filter
# def is_owner(project, member) -> bool:
#     """Checks if a user is an admin
#
#     Examples::
#
#         {% if project|is_admin:request.user %}
#             ...
#         {% endif %}
#     """
#     if isinstance(project, pwc.models.Project) and isinstance(member, projects.models.ProjectMember):
#         return project.is_owner(member)
#     else:
#         return False
#
#
# @register.filter
# def is_admin(project, user) -> bool:
#     """Checks if a member is an admin
#
#     Examples::
#
#         {% if project|is_admin:member %}
#             ...
#         {% endif %}
#     """
#     if isinstance(project, pwc.models.Project) and isinstance(user, projects.models.ProjectMember):
#         return project.is_admin(user)
#     else:
#         return False
#
#
# @register.filter
# def is_write(project, member) -> bool:
#     """Checks if a member has write permissions
#
#     Examples::
#
#         {% if project|is_write:member %}
#             ...
#         {% endif %}
#     """
#     if isinstance(project, pwc.models.Project) and isinstance(member, projects.models.ProjectMember):
#         return project.is_write(member)
#     else:
#         return False
#
#
# @register.filter
# def is_read(project, member) -> bool:
#     """Checks if a member has write permissions
#
#     Examples::
#
#         {% if project|is_read:member %}
#             ...
#         {% endif %}
#     """
#     if isinstance(project, pwc.models.Project) and isinstance(member, projects.models.ProjectMember):
#         return project.is_read(member)
#     else:
#         return False
#
#
# @register.filter
# def get_permission_label(project, member):
#     """Returns the label of a users permission
#
#     Examples::
#
#         {{ if project|get_permission_label:member }}
#     """
#     return project.get_permission(member).label

