from django.conf import settings
from django import template

register = template.Library()


class SettingsExportNode(template.Node):
    def render(self, context):
        for setting in settings.SETTINGS_EXPORT:
            context[setting] = getattr(settings, setting, None)
        return ""


@register.tag
def update_context_with_settings_export(parser, token):
    return SettingsExportNode()
