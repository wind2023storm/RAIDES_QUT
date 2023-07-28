from django import forms
from django.template import loader
from django.utils.safestring import mark_safe

class TargetInputWidget(forms.Widget):
    template_name = 'interactive_map/target_map_widget.html'

    def get_context(self, name, value, attrs=None):
        return {'widget': {
            'name': name,
            'value': value,
        }}
    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)