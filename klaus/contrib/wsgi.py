from klaus import make_app
from .app_args import get_args_from_env
from flask import render_template

args, kwargs = get_args_from_env()

if kwargs['htdigest_file']:
    with open(kwargs['htdigest_file']) as file:
        kwargs['htdigest_file'] = file
        application = make_app(*args, **kwargs)
else:
    application = make_app(*args, **kwargs)
    
    
@application.errorhandler(404)
def not_found(e):
    # defining function
    return render_template("404.html")
