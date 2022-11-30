def api_v0(f):
    def wrapper(request, *args, **kwargs):
        if request.user.is_anonymous:
            kwargs["profile"] = None
        else:
            kwargs["profile"] = request.user.person.view
        return f(request, *args, **kwargs)

    wrapper.__doc__ = f.__doc__
    wrapper.__name__ = f.__name__
    return wrapper
