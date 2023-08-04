The LMS templates provide the ability to generate HTML content for a 
queryset of instances, or a singular instance itself.

# Template Example

```html
{% if view.instance %}
    <p>
    The view is rendering an instance. 
    Here we'd want to show a verbose description of the object. 
    Perhaps similar to a Projects Dashboard
    </p>

    <p>
    {% with view.instance as instance %}
        
    {% endwith %}
    </p>

{% elif view.queryset %}
    <p>
    The view is rendering a list of instances.
    Here we'd display a table of items with a brief summary of each instance.
    Perhaps similar to the Project Index.
    </p>

    <ol>
    {% for instance in view.queryset %}
        <li>{{ instance }}</li>        
    {% endfor %}
    </ol>

{% else %}
    The view had no instance or queryset.

{% endif %}
```

# Template Context

As the view itself is passed as context during the rendering. You have
access to any class instance variables set before the rendering process.

```html
This template is called {{ view.template_name }}
This view is in the project {{ view.project }}
The requesting user member object is {{ view.member }}
The URL name defined in urls.py is {{ view.url_name }}

And of course, any of the models fields within the 
instance or queryset objects.
```

# Related Objects

While you can access an objects related fields. It's preferable that you access
them using the appropriate url, as we can enforce permissions that way.
