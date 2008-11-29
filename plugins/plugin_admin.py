#!/usr/bin/env python
#
#  PyGab - Python Jabber Framework
#  Copyright (c) 2008, Patrick Kennedy
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#  - Redistributions of source code must retain the above copyright
#  notice, this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright
#  notice, this list of conditions and the following disclaimer in the
#  documentation and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import	argparse
import	os
import	shlex
import	sys
import	time

from	datetime	import	datetime

from	common			import argparse, const, mounts, utils
from	common.ini		import	iMan
#from	common.utils	import	*
#module = get_module()
#exec(get_import(mod=module, from_=['utils']))
#try:
#	exec(get_import(mod=module, from_=['mounts'], import_=['CommandMount']))
#except ImportError, e:
#	print e

class LoadParser(object):
	rank = const.RANK_ADMIN
	file = __file__

	load_parser = argparse.ArgumentParser(prog='!(re|un)load', add_help=False)
	load_parser.add_argument(
		'extra',
		default=False, nargs='?',
		metavar='command', help='Start, stop, restart'
	)
	load_parser.add_argument(
		'-a', '--all',
		action='store_true',
		help='Equvilant to -p -i'
	)
	load_parser.add_argument(
		'-p', '--plugin',
		const=True, default=False, nargs='?',
		metavar='plugin_name', help='(re|un)load plugins'
	)
	load_parser.add_argument(
		'-i', '--ini',
		const=True, default=False, nargs='?',
		metavar='ini_name', help='(re|un)load inis'
	)


class Reload(mounts.CommandMount, LoadParser):
	name = 'reload'

	__doc__ = """Reload parts of the bot.\n%s""" % (LoadParser.load_parser.format_help())

	def __init__(self, parent):
		self.parent = parent

	def run(self, user, args):
		print "Reload args: %s" % args
		args = shlex.split(args.lower())
		print "Reload args: %s" % args
		options = self.load_parser.parse_args(args)

		return self.cmd_reload(user, options)

	def __exit__(self, *args):
		mounts.CommandMount.remove(self.__class__)

	def cmd_reload(self, user, options):
		if options.extra:
			self.parent.error(user, "Please use one of the arguments. Ex. -p user, -i roster")
			return

		if options.ini is True:
			iMan.readall()
			self.parent.sendto(user, 'I have read all ini\'s')
		elif options.ini:
			iMan[options.ini].read()
			self.parent.sendto(user, 'I have read the ini (%s)' % options.ini)

		loaded = []
		plugins_to_load = []
		if options.plugin is True:
			plugins_to_load = iMan.config.system.plugins
		elif options.plugin:
			plugins_to_load.append(options.plugin)

		for i in plugins_to_load:
			try:
				plug_path = self.parent.get_plugin_path(i)
				#self.parent.unload_plugin(plug_path)
				if self.parent.load_plugin(i, plug_path):
					loaded.append(i)

			except IOError:
				self.parent.error(user, 'The plugin "plugin_%s.py" could not be found.' % i)
				continue

			except:
				pluglog = file(os.path.join("errors","PluginError.log"), "a+")
				traceback.print_exc()
				print >>pluglog, "\n Plugin error log for: ", i
				traceback.print_exc(None, pluglog)
				self.parent.error(user, 'There was an error importing the plugin. A report has been logged.')
				continue

		if options.plugin:
			if not loaded:
				loaded.append("None to be refreshed.")
			self.parent.sendto(user, "Plugins reloaded: " + " ".join(loaded))

class Load(mounts.CommandMount, LoadParser):
	name = 'load'

	__doc__ = """Load parts of the bot.\n%s""" % (LoadParser.load_parser.format_help())


	def __init__(self, parent):
		self.parent = parent

	def __exit__(self, *args):
		mounts.CommandMount.remove(self.__class__)

	def run(self, user, args):
		args = shlex.split(args.lower())
		options = self.load_parser.parse_args(args)

		return self.cmd_load(user, options)

	def cmd_load(self, user, options):
		if options.extra:
			self.parent.error(user, "Please use one of the arguments. Ex. -p user, -i roster")
			return

		if options.ini is True:
			self.parent.error(user, "You must pass the name of an ini to load.")
		elif options.ini:
			if iMan.load(options.ini):
				self.parent.sendto(user, 'I have successfully loaded the ini (%s)' % options.ini)
			else:
				self.parent.sendto(user, 'I can\'t load the ini (%s)' % options.ini)

		if options.plugin is True:
			self.parent.error(user, "You must pass the name of a plugin to load.")
		elif options.plugin:
			if options.plugin in self.parent._pluginhash:
				self.parent.error(user,"This plugin has already been loaded. To update it please use '!reload -p'")
			else:
				try:
					i = options.plugin
					plug_path = self.parent.get_plugin_path(i)
					self.parent.load_plugin(i, plug_path)
					self.parent.sendto(user, "Plugin (%s) sucessfully loaded." % i)

				except IOError:
					self.parent.error(user,'The plugin "plugin_%s.py" could not be found.' % i)

				except:
					pluglog = file(os.path.join("errors","PluginError.log"), "a+")
					traceback.print_exc(None, pluglog)
					print >>pluglog, "\n"
					pluglog.close()
					traceback.print_exc()
					self.parent.error(user, 'There was an error importing the plugin. A report has been logged.')

class Unload(mounts.CommandMount, LoadParser):
	name = 'unload'

	__doc__ = """Unload parts of the bot.\n%s""" % (LoadParser.load_parser.format_help())

	def __init__(self, parent):
		self.parent = parent

	def run(self, user, args):
		args = shlex.split(args.lower())
		options = self.load_parser.parse_args(args)

		return self.cmd_unload(user, options)

	def __exit__(self, *args):
		mounts.CommandMount.remove(self.__class__)

	def cmd_unload(self, user, options):
		if options.extra:
			self.parent.error(user, "Please use one of the arguments. Ex. -p user, -i roster")
			return

		if options.ini is True:
			self.parent.error(user, "You must pass the name of an ini to unload.")
		elif options.ini:
			if iMan.unload(options.ini):
				self.parent.sendto(user, 'I have successfully unloaded the ini (%s)' % options.ini)
			else:
				self.parent.sendto(user, 'I can\'t unload the ini (%s)' % options.ini)


		if options.plugin is True:
			self.parent.error(user, "You must pass the name of a plugin to unload.")
		elif options.plugin:
			name = options.plugin
			if name not in self.parent._pluginhash:
				self.parent.error(user, "Plugin (%s) hasn't been loaded or was spelled wrong." % name)
				return

			try:
				plugin_path = self.parent.get_plugin_path(name)
			except IOError, e:
				self.parent.error(user, "I have that plugin loaded but I can't find the file to unload it.")
				return

			self.parent.unload_plugin(plugin_path)

			del self.parent._pluginhash[name]
			self.parent.sendto(user, "Unloaded plugin (%s)" % name)
