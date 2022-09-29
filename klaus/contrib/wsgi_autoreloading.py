from __future__ import print_function
import os
import glob
import time
import threading

from klaus import make_app
from flask import render_template


# Shared state between poller and application wrapper
class _:
    #: the real WSGI app
    inner_app = None
    should_reload = True


def poll_for_changes(interval, dir, *args, **kwargs):
    """
    Polls `dir` for changes every `interval` seconds and sets `should_reload`
    accordingly.
    """

    def list_dir2(pathname):
        files_depth = glob.glob(f'{pathname}/*/*')
        return list(filter(lambda f: os.path.isdir(f), files_depth))

    old_contents = list_dir2(dir)
    while 1:
        time.sleep(interval)
        if _.should_reload:
            # klaus application has not seen our change yet
            continue
        new_contents = list_dir2(dir)
        if new_contents != old_contents:
            # Directory contents changed => should_reload
            old_contents = new_contents
            _.inner_app = make_app(
                [os.path.join(dir, x) for x in os.listdir(dir)],
                args, kwargs
            )
            _.should_reload = True


def make_autoreloading_app(repos_root, *args, **kwargs):
    def app(environ, start_response):
        if _.should_reload:
            # Refresh inner application with new repo list
            print("Reloading repository list...")
            inner_app = _.inner_app if _.inner_app else make_app(
                [os.path.join(repos_root, x) for x in os.listdir(repos_root)],
                *args, **kwargs
            )

            @inner_app.errorhandler(404)
            def not_found(e):
                # defining function
                return render_template("404.html")

            _.inner_app = inner_app
            _.should_reload = False

        return _.inner_app(environ, start_response)

    # Background thread that polls the directory for changes
    poller_thread = threading.Thread(target=(lambda: poll_for_changes(10, repos_root, args, kwargs)))
    poller_thread.daemon = True
    poller_thread.start()

    return app
