from django.template import loader

from utils import render_appropriately


def handler500(request):
    """
    500 error handler which includes ``request`` in the context.

    Templates: `500.html`
    Context: None
    """
    t = loader.get_template("500.html")
    return render_appropriately(request, t, {})


def handler404(request, exception):
    t = loader.get_template("404.html")
    return render_appropriately(request, t, {})
