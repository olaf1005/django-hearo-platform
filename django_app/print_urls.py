# appended to root urls.py

if __name__ == "__main__":

    import os
    import sys
    from django.urls.resolvers import URLPattern
    from django.urls.resolvers import URLResolver
    from django.utils.termcolors import colorize

    sys.path.append(os.path.abspath(".."))
    os.environ["DJANGO_SETTINGS_MODULE"] = "settings.local"
    from urls import urlpatterns

    def traverse(url_patterns, prefix=""):
        for p in url_patterns:
            if isinstance(p, URLPattern):
                composed = "%s%s" % (prefix, p.pattern)
                composed = composed.replace("/^", "/")
                print(colorize("\t%s" % (composed), fg="green"), "==> ", end=" ")
                try:
                    sys.stdout.write(
                        colorize("%s." % p.callback.__module__, fg="yellow")
                    )
                    print(p.callback.__name__)
                except:
                    print(p.callback.__class__.__name__)
            if isinstance(p, URLResolver):
                traverse(p.url_patterns, prefix=p.pattern)

    traverse(urlpatterns)
