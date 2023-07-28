import copy

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms import Widget, fields


class CategoryChoiceWidget(Widget):
    input_type = "select"
    template_name = "forms/category_select.html"
    option_template_name = "forms/category_option.html"
    add_id_index = False
    checked_attribute = {"selected": True}
    option_inherits_attrs = False
    allow_multiple_selected = False

    def __init__(self, attrs=None, categories=()):
        super().__init__(attrs)
        self.categories = categories

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.attrs = self.attrs.copy()
        obj.categories = copy.copy(self.categories)
        memo[id(self)] = obj
        return obj

    def options(self, name, value, attrs=None):
        categories = []
        has_selected = False

        for index, (option_category, option_value, option_label) in enumerate(self.categories):
            if option_value is None:
                option_value = ""

            selected = (not has_selected or self.allow_multiple_selected) and str(
                option_value
            ) in value
            has_selected |= selected
            categories.append(
                self.create_option(
                    name,
                    option_category,
                    option_value,
                    option_label,
                    selected,
                    index,
                    attrs=attrs,
                )
            )

        return categories

    def create_option(self, name, category, value, label, selected, index, attrs=None):
        index = str(index)
        option_attrs = (
            self.build_attrs(self.attrs, attrs) if self.option_inherits_attrs else {}
        )
        if selected:
            option_attrs.update(self.checked_attribute)
        if "id" in option_attrs:
            option_attrs["id"] = self.id_for_label(option_attrs["id"])

        return {
            "name": name,
            "category": category,
            "value": value,
            "label": label,
            "selected": selected,
            "index": index,
            "attrs": option_attrs,
            "type": self.input_type,
            "template_name": self.option_template_name,
            "wrap_label": True,
        }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["categories"] = self.options(
            name, context["widget"]["value"], attrs
        )
        return context

    def value_from_datadict(self, data, files, name):
        getter = data.get
        if self.allow_multiple_selected:
            try:
                getter = data.getlist
            except AttributeError:
                pass
        return getter(name)

    def format_value(self, value):
        """Return selected values as a list."""
        if value is None and self.allow_multiple_selected:
            return []
        if not isinstance(value, (tuple, list)):
            value = [value]
        return [str(v) if v is not None else "" for v in value]


class CategoryChoiceField(fields.Field):
    widget = CategoryChoiceWidget
    default_error_messages = {
        "invalid_choice": _(
            "Select a valid choice. %(value)s is not one of the available choices."
        )
    }

    def __init__(self, *, categories, **kwargs):
        super().__init__(**kwargs)
        self.categories = categories

    def __deepcopy__(self, memo):
        result = super().__deepcopy__(memo)
        result._categories = copy.deepcopy(self._categories, memo)
        return result

    def _get_categories(self):
        return self._categories

    def _set_categories(self, value):
        if callable(value):
            value = fields.CallableChoiceIterator(value)
        else:
            value = list(value)

        self._categories = self.widget.categories = value

    categories = property(_get_categories, _set_categories)

    def validate(self, value):
        super().validate(value)
        if value and not self.valid_value(value):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )

    def valid_value(self, value):
        # text_category = str(category)
        text_value = str(value)
        for c, k, v in self.categories:
            if value == k or text_value == str(k):  # category == c or text_category == str(c)) and (
                return True
        return False