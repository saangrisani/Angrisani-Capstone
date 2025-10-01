from django import template
register = template.Library()

@register.filter
def add_class(field, css):
    """
    Adds a CSS class to a form field.
    Usage: {{ form.field|add_class:"my-class" }}
    """
    attrs = field.field.widget.attrs
    existing = attrs.get("class", "")
    attrs['class'] = (existing + " " + css).strip()
    return field.as_widget(attrs=attrs)
