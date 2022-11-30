"""
WSGI config for testproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

application = get_wsgi_application()

# DELETE ME
# """
# WSGI config for hearo project.

# This module contains the WSGI application used by Django's development server
# and any production WSGI deployments. It should expose a module-level variable
# named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
# this application via the ``WSGI_APPLICATION`` setting.

# Usually you will have the standard Django WSGI application here, but it also
# might make sense to replace the whole Django WSGI application with a custom one
# that later delegates to the Django one. For example, you could introduce WSGI
# middleware here, or combine a Django application with an application of another
# framework.

# """
# import os
# from django.core.wsgi import get_wsgi_application
# from whitenoise import WhiteNoise

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.local")

# # This application object is used by any WSGI server configured to use this
# # file. This includes Django's development server, if the WSGI_APPLICATION
# # setting points here.
# application = get_wsgi_application()

# application = WhiteNoise(application)
# application.add_files('/media/images/', prefix='images')
# application.add_files('/code/static/', prefix='public')
