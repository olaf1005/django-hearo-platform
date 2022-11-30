from django.template import Library, Node

register = Library()

try:
    import ipdb as pdb
except ImportError:
    import pdb


class PdbNode(Node):
    def render(self, context):
        # Access vars at the prompt for an easy reference to
        # variables in the context
        vars = []
        for d in context.dicts:
            for k, v in list(d.items()):
                vars.append(k)
                locals()[k] = v
        del v
        del k
        del d
        pdb.set_trace()
        return ""


@register.tag("pdbdebug")
def pdbdebug_tag(parser, token):
    """Tag that inspects template context.

    Usage:
    {% pdbdebug %}

    You can then access your context variables directly at the prompt.

    The vars variable additonally has a reference list of keys
    in the context.
    """
    return PdbNode()


@register.filter("pdbdebug")
def pdbdebug_filter(value, arg=None):
    """Filter that inspects a specific
    variable in context.

    Usage:
    {{ variable|pdbdebug }}
    """
    pdb.set_trace()
    return ""
