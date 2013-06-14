from __future__ import print_function

import os
import shutil
import operator
import itertools
from datetime import datetime

import yaml

from straight.command import Command, SubCommand, Option
from straight.plugin import load

import jules


def now_minute():
    return datetime.now().replace(second=0, microsecond=0)


class Init(Command):

    version = "0.1"
    help = "Create a new site based on a starter template."

    projectname = Option(dest='projectname', action='store')

    def execute(self, **kwargs):
        projectname = kwargs["projectname"]
        if not projectname:
            print("error: You must specify a project name")
        elif os.path.exists(projectname):
            print("error: The path '{}' already exists".format(projectname))
        else:
            starter_path = os.path.join(os.path.dirname(jules.__file__), 'starters', 'default')
            shutil.copytree(starter_path, projectname)
        

class Build(Command):

    version = "0.2"

    help = "Build the site, rendering all the bundles found."

    force = Option(short='-f', dest='force', action='store_true')

    def execute(self, **kwargs):
        engine = jules.JulesEngine(os.path.abspath('.'))
        engine.prepare()
        output_dir = engine.config.get('output', self.parent.args['output'])
        if not os.path.exists(output_dir) or self.args['force']:
            engine.render_site(output_dir)
            
        else:
            print("error: Refusing to replace {} output directory!".format(output_dir))


class Tags(Command):
    def execute(self, **kwargs):
        engine = jules.JulesEngine(os.path.abspath('.'))
        engine.prepare()
        tags = set()
        for key, bundle in engine.bundles.items():
            for tag in bundle.meta.get('tags', []):
                tags.add(tag)
        for tag in tags:
            print(tag)


class Serve(Command):

    port = Option(dest='port', default=8000)
    
    help = "Serve the site from the output directing, using a test server. Defaults to port 8000"

    def execute(self, port, **kwargs):
        output_dir = self.parent.args['output']

        # python 2
        try:
            import SimpleHTTPServer
            import SocketServer
            handler = SimpleHTTPServer.SimpleHTTPRequestHandler
            server = SocketServer.TCPServer
        # python 3
        except ImportError:
            from http.server import SimpleHTTPRequestHandler as handler
            from http.server import HTTPServer as server

        handler.extensions_map[''] = 'text/html'
        httpd = server(("", int(port)), handler)

        os.chdir(output_dir)
        httpd.serve_forever()


class BundleMeta(Command):
    """Update or view meta data for a bundle.

    If no property is specified, all are shown.
    If property is specified, but not value, the current value is shown.
    If property and value are specified, it is changed.
    """

    key = Option(dest='key')
    prop = Option(dest='prop', default=None)
    value = Option(dest='value', default=None)

    def execute(self, key, prop, value, **kwargs):
        engine = jules.JulesEngine(os.path.abspath('.'))
        engine.prepare()
        engine.prepare_bundles()

        bundle = engine.get_bundle(key=key)
        label = bundle.meta.get('title', key)
        print("Bundle %s" % label)
        if prop:
            if value is not None:
                bundle.meta[prop] = value
            print("%s = %s" % (prop, bundle.meta.get(prop)))
        else:
            for prop in bundle.meta:
                print("%s = %s" % (prop, bundle.meta.get(prop)))


class UpdateBundle(Command):
    """Sets a datetime meta property to the current time."""

    key = Option(dest='key')
    prop = Option(dest='prop', default='updated_time')

    def execute(self, key, prop, **kwargs):
        engine = jules.JulesEngine(os.path.abspath('.'))
        engine.prepare()
        engine.prepare_bundles()

        bundle = engine.get_bundle(key=key)
        label = bundle.meta.get('title', key)

        bundle.meta[prop] = now_minute()
        bundle.write_meta()
        print("Bundle %s updated at %s" % (label, bundle.meta['updated_time']))


class PublishBundle(Command):
    """Sets the publish_time and updated_time and sets status as "published"."""

    key = Option(dest='key')

    def execute(self, key, **kwargs):
        engine = jules.JulesEngine(os.path.abspath('.'))
        engine.prepare()
        engine.prepare_bundles()

        bundle = engine.get_bundle(key=key)
        meta = bundle.meta
        label = meta.get('title', key)

        meta['publish_time'] = now_minute()
        meta['updated_time'] = meta['publish_time'].replace()
        meta['status'] = 'published'
        bundle.write_meta()
        print("Bundle %s updated at %s" % (label, meta['updated_time']))

class JulesCommand(Command):

    version = "0.2"

    output = Option(short='-o', long='--output', dest='output', nargs=1, default='_build', help="The destination directory to build to")

    basecopy = SubCommand('build', Build)
    serve = SubCommand('serve', Serve)
    init = SubCommand('init', Init)
    update = SubCommand('update', UpdateBundle)
    meta = SubCommand('meta', BundleMeta)
    publish = SubCommand('publish', PublishBundle)
    tags = SubCommand('tags', Tags)

def main():
    import sys
    JulesCommand().run(sys.argv[1:])

if __name__ == '__main__':
    main()