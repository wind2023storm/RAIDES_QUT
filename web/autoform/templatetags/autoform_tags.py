from django import template
from django.template.loader import get_template
from django.contrib.auth import get_user_model

import re
import operator as op

from functools import reduce

User = get_user_model()

register = template.Library()

field_template = get_template('autoform/fields/autofield.html')


@register.filter
def from_to(a, b):
    return range(a, b)


@register.filter
def append(a, b):
    return f"{a}{b}"


@register.filter
def prepend(a, b):
    return f"{b}{a}"


@register.filter(name="int")
def to_int(a):
    """Converts input to integer"""
    return int(a)


@register.simple_tag
def calc(string, **operands):
    """Performs simple calculation, using only known operators (for security reasons)
    Accepted operators:  `* + / ^ ( ) %`

    Parameters
    ----------
    string : str
        Math string to evaluate, infix format e.g., 2 + 5 % 4
    operands : dict
        A dictionary of operands such that alpha operands can be replaced by numerical values.

    Examples
    --------

    >>> {% calc "b + 3" b=2 %}
    >>> 5

    >>> {% calc "(2 * (a + 5) / 3 % (4 + 9))" a=3 %}
    >>> 5.33333

    Returns
    -------
    result : float
        The result of the calculation
    """
    if string.count('(') != string.count(')'):
        raise SyntaxError('Parenthesis Mismatch')

    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2, '^': 3}
    operator_funcs = {'+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv, '^': op.pow, '%': op.mod}
    operators = precedence.keys()

    def infix_to_postfix(infix: str):
        """Converts an infix equation into postfix (reverse polish notation) format. It's easier to calculate
        this notation programmatically."""
        tokens = re.sub(r' +|[\+\*\/\^]', lambda m: ' ' + m.group() + ' ', infix).split()
        stack = []
        output = []

        for token in tokens:
            if token.isdigit():
                # Numerical operands just get put straight onto the queue
                output.append(token)
            elif token in operators:
                # Handle the operators
                while stack and stack[-1] in operators and (
                        precedence[token] < precedence[stack[-1]] or (
                        precedence[token] == precedence[stack[-1]] and token != '^')):
                    output.append(stack.pop())
                stack.append(token)
            # Handle the parenthesis stuff now
            elif token == '(':
                stack.append(token)
            elif token == ')':
                # Organize the contents of the brackets until open bracket is met
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                stack.pop()  # remove the open bracket
            else:
                # If anything other than an operand or operator was used, raise a token error
                raise ValueError("Invalid Infix Token Input")
        while stack:
            # Move the remaining contents of the stack into the queue
            output.append(stack.pop())

        return output

    def evaluate_postfix(postfix: list):
        """Evaluate the supplied postfix token list. Return the result as float"""
        stack = []

        for token in postfix:
            if token.isdigit():
                stack.append(float(token))
            elif token in operators:
                b = stack.pop()
                a = stack.pop()
                stack.append(operator_funcs[token](a, b))
            else:
                raise ValueError("Invalid Postfix Token Input")

        return stack.pop()

    # Setup evaluation
    for k, v in operands.items():
        string = re.sub(k, str(v), string)

    string = infix_to_postfix(string)

    return evaluate_postfix(string)


@register.simple_tag
def join(*args, sep=''):
    return sep.join([str(x) for x in args])


@register.simple_tag(takes_context=True)
def auto_field(context, field, description="", type="text", content="", css="", style=""):
    """Creates an auto-field for use on the autoform, any item passed to the 'field_data' context entry are accepted as
    automatically populating auto-fields.

    Parameters
    ----------
    context : dict
        Context being passed to the view via the render function
    field : str
        The field ID, contents will be pulled from attached input
    description : str, optional
        Description of the field, this will be displayed when the field is empty
    type : str, optional
        Type of field to be displayed
    content : str, optional
        Default content for a field if required, generally this is not used

    Returns
    -------
    html : str
        HTML of the field
    """
    if not description:
        description = field.replace('_', ' ').replace('.', ' ').title()

    if not content:
        def inner(acc, key):
            """Manages searching the dict handles indexing for either dicts or lists e.g.,

            'field_data': {'foo': [{'bar': 123}, ...]}

            field = `foo.0.bar` = 123
            """
            try:
                return acc[key]
            except KeyError:
                return ''
            except TypeError:
                try:
                    return acc[int(key)]
                except (TypeError, ValueError, IndexError):
                    return ''

        content = reduce(lambda acc, key: inner(acc, key), field.split('.'), context['field_data'])

    return field_template.render({
        'field': field,
        'description': description,
        'css': css,
        'style': style,
        'type': type,
        'content': content
    })
