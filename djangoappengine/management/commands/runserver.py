#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging
import sys

from django.db import connections
from ...boot import PROJECT_DIR
from ...db.base import DatabaseWrapper
from django.core.management.base import BaseCommand
from django.core.exceptions import ImproperlyConfigured


def start_dev_appserver(argv):
    """Starts the App Engine dev_appserver program for the Django project.

    The appserver is run with default parameters. If you need to pass any special
    parameters to the dev_appserver you will have to invoke it manually.
    """
    from google.appengine.tools import dev_appserver_main
    progname = argv[0]
    args = []
    # hack __main__ so --help in dev_appserver_main works OK.
    sys.modules['__main__'] = dev_appserver_main
    # Set bind ip/port if specified.
    addr, port = None, '8000'
    if len(argv) > 2:
        if not argv[2].startswith('-'):
            addrport = argv[2]
            try:
                addr, port = addrport.split(":")
            except ValueError:
                addr = addrport
        else:
            args.append(argv[2])
        args.extend(argv[3:])
    if addr:
        args.extend(["--address", addr])
    if port:
        args.extend(["--port", port])
    # Add email settings
    from django.conf import settings
    if '--smtp_host' not in args and '--enable_sendmail' not in args:
        args.extend(['--smtp_host', settings.EMAIL_HOST,
                     '--smtp_port', str(settings.EMAIL_PORT),
                     '--smtp_user', settings.EMAIL_HOST_USER,
                     '--smtp_password', settings.EMAIL_HOST_PASSWORD])

    # Pass the application specific datastore location to the server.
    for name in connections:
        connection = connections[name]
        if isinstance(connection, DatabaseWrapper):
            for key, path in connection._get_paths().items():
                # XXX/TODO: Remove this when SDK 1.4.3 is released
                if key == 'prospective_search_path':
                    continue

                arg = '--' + key
                if arg not in args:
                    args.extend([arg, path])
            break

    # Reset logging level to INFO as dev_appserver will spew tons of debug logs
    logging.getLogger().setLevel(logging.INFO)

    # Append the current working directory to the arguments.
    dev_appserver_main.main([progname] + args + [PROJECT_DIR])

class Command(BaseCommand):
    """Overrides the default Django runserver command.

    Instead of starting the default Django development server this command
    fires up a copy of the full fledged App Engine dev_appserver that emulates
    the live environment your application will be deployed to.
    """
    help = 'Runs a copy of the App Engine development server.'
    args = '[optional port number, or ipaddr:port]'

    def run_from_argv(self, argv):
        start_dev_appserver(argv)
