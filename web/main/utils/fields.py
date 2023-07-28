from abc import ABC
from typing import List, Tuple

from django.db.models import Case, CharField, When, Value


class ChoicesLabelCase(Case, ABC):

    def __init__(self, field: str, choices: List[Tuple[int, str]], *args, **kwargs):
        """Used for selecting a 'choice' display option during SQL queries.

        Parameters
        ----------
        field : str
            field to check value for
        choices
            list of choices to select from
        """
        if choices is None:
            raise ValueError("Choices must be provided")

        cases_list = [When(discipline=k, then=Value(v)) for k, v in choices]
        super(ChoicesLabelCase, self).__init__(*cases_list, output_field=CharField(), *args, **kwargs)
