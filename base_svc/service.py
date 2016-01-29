#!/usr/bin/env python3

import sys

import tornado.ioloop
import tornado.web
import argparse

import base_config.settings as csettings
import base_svc.comm
from base_common.dbacommon import close_stdout
from base_common.importer import import_from_settings
from base_common.importer import get_installed_apps
from base_config.service import logs, log

from socket import gaierror

w_arning = '''
###################################################
#        There is no application installed        #
#  Please install one in DigitalBaseAPI settings  #
#####################################k#############

'''


def check_args(installed_apps):

    a = argparse.ArgumentParser()

    if not installed_apps:
        log.critical('There is no one application installed in DigitalBaseAPI')
        a.exit(1, w_arning)

    if len(installed_apps.keys()) > 1:
        a.add_argument("app", help="Application to run with DigitalBaseAPI",
                       choices=[a for (a, b) in installed_apps.items()])
    else:
        a.add_argument("app", help="Application to run with DigitalBaseAPI",
                       choices=[a for (a, b) in installed_apps.items()],
                       default=list(installed_apps.keys())[0], nargs='?')

    a.add_argument("-p", "--port", help="Application port")

    return a.parse_args()


def entry_point(api_module, allowed=None, denied=None):

    try:
        llog = logs[api_module.__name__ .split('.')[0]]
    except KeyError:
        llog = log

    llog.info("Registering {}".format(api_module.name))

    base_pkg = hasattr(api_module,'BASE') and api_module.BASE

    return "^/{}{}".format("" if base_pkg else "{}/".format(api_module.PREFIX), api_module.location), \
           base_svc.comm.GeneralPostHandler, \
           dict(allowed=allowed, denied=denied, apimodule=api_module, log=llog)


def start_base_service():

    close_stdout(csettings.DEBUG)

    imported_modules = []
    installed_apps = {}

    get_installed_apps(installed_apps)
    b_args = check_args(installed_apps)

    svc_port = b_args.port if b_args.port else installed_apps[b_args.app]['svc_port']
    if not svc_port:
        log.critical('No svc port provided, lok in app config or add in commandline')
        print('Please provide svc_port in app init or trough commandline')
        sys.exit(3)

    import_from_settings(imported_modules, b_args.app)

    entry_points = [entry_point(m) for m in imported_modules]

    application = tornado.web.Application([
        (r'^/$', base_svc.comm.MainHandler),
        (r'^/spec.*$', base_svc.comm.MainHandler),
        *entry_points
        ],
        template_path='templates',
        static_path='templates',
        cookie_secret="d1g1t4l", debug=csettings.DEBUG)

    try:
        application.listen(svc_port)
        log.info('Starting base_svc v({}) on port {}'.format(csettings.__VERSION__, svc_port))
        tornado.ioloop.IOLoop.instance().start()

    except gaierror:
        log.critical("Missing port for service, port = {}".format(svc_port))
        print("Missing port for service, port = {}".format(svc_port))

    except Exception as e:
        log.critical("Exception: {}".format(e))
        print("Critical exception: {}".format(e), file=sys.stderr)