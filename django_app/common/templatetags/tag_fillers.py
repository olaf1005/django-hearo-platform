"""
Filler tags for include apps which are missing tag libraries likely
due to incompatibilities with some included modules.
"""
from django.template import Library

register = Library()


@register.inclusion_tag("common/_pre.html")
def output_all(values):
    # usage: templates/widget/image.html
    return {"values": values}
