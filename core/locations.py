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

from framework.pluginregistry import LocationRegistry

class Locations(type, metaclass=LocationRegistry):
	"""Stores Location classes in a centralized location.

	Locations implementing this mount should provide the following attributes:

	========  ==================================================================
	__doc__   Please provide information on what args are passed to the handler
			  and what the expected behavior upon returning a True truth value
			  should be (e.g. consume message in LocEvMsg).
	========  ==================================================================

	"""

	def __new__(cls, name, bases, attrs):
		# We use __new__ to ensure `Locations` is a metaclass of all locations
		# this allows locations to inhereit from `Location` rather than
		# explicitly defining `Locations` as a metaclass.
		# Force only the actual location classes to use `Locations` as a
		# metaclass, without this check all hooks would metaclass `Locations`
		if bases and Location in bases:
			attrs.update({"__metaclass__": Locations})
		return type.__new__(cls, name, bases, attrs)

	def __init__(cls, name, bases, attrs):
		if not bases:
			return
		if not hasattr(cls, 'hooks'):
			# As with the top level registry, this branch only exceutes when
			# processing the mount point itself (in this case the location).
			# Because of this we want to add it to the `Locations` plugin
			# dictionary.

			# Because `Location` is merely a convenience wrapper for
			# Locations.__new__ we don't want to add it to the list of locations
			# Note: Hard coding the name limits the scope of this trick
			if name != "Location":
				cls.plugins[name] = cls
				cls.hooks = {}
		else:
			if cls != Location:
				cls.hooks[cls.name] = cls
				# Defining 'states' on Locations means 'states' is shared
				# by every location and every hook, therefore, if we define it
				# on each individual hook the dictionary is specific to that hook.
				cls.states = {}


class Location(metaclass=Locations):
	# Lets children define a custom name without silly hacks like:
	# (getattr(cls, "name", cls.__name__))
	@property
	@classmethod
	def name(cls): return cls.__name__
	# Enable hooks to use a single global state rather than many user states.
	use_global_state = False

	@classmethod
	def get_or_init_state(cls, name, context, *initial_args):
		#import logging
		#log = logging.getLogger('pygab.plugins')
		thread = None
		if name in cls.hooks:
			hook = cls.hooks[name]
			if hook.use_global_state:
				context = "__global__"

			#log.info('name: %s | hooks: %s | hook: %s | states: %s' % (
			#	name, cls.hooks, hook, hook.states)
			#)

			states = hook.states

			thread = states.get(context, None)
			if not thread or thread.gi_frame is None:
				thread = hook.thread(*initial_args)
				states[context] = thread
				next(thread)

		#log.info('name: %s | context: %s | thread: %r | locals: %s' % (
		#	name, context, thread, thread.gi_frame.f_locals)
		#)
		return thread

	@classmethod
	def remove(cls):
		# Since locations implement this method and they're static we have to
		# filter them.
		#assert cls.mro()[1] is not Location, "Attempting to remove location: %s" % cls
		assert not cls.__subclasses__(), "Attempting to remove location: %s | %s" % (cls, cls.__subclasses__())

		name = cls.name
		del cls.hooks[name]
		del cls.states
		del cls

	@classmethod
	def clean(cls, name, context):
		if name in cls.hooks:
			hook = cls.hooks[name]
			if context in hook.states:
				if hook.use_global_state:
					context = "__global__"
				del hook.states[context]

	@classmethod
	def evaluate(cls, bot, *args):
		"""Process each hook and return True if any return a truthy value.

		Arguments:
			bot - A PyGab instance

		"""
		# If True the calling function should break execution
		break_ = False

		for hook in list(cls.hooks):
			thread = cls.get_or_init_state(hook, bot.active_user.bare, bot)
			#FIXME: This is a hack to solve a missing hook when unloading a
			# plugin which contains a hook at a location that fires as a result
			# of the unload command itself.
			if not thread:
				continue
			try:
				break_ |= bool(thread.send(args))
				next(thread)
			except StopIteration:
				cls.clean(hook, bot.active_user.bare)

		return break_

	@classmethod
	def get_hooks_for(self, path):
		return (hook for hook in list(self.hooks.values()) if hook.file == path)


class Initializers(Location): pass

class SendTo(Location):
	"""Hooks are called for messages sent to a single user

	Arguments:
		message - The text of the message wrapped in a list to enable mutability
					This behavior is abnormal and should be fixed in the future.

	Truthy Return Behavior:
		Drop the message
	"""

class SendToAll(Location):
	"""Hooks are called for messages sent to all users

	Arguments:
		message - The text of the message wrapped in a list to enable mutability
					This behavior is abnormal and should be fixed in the future.

	Truthy Return Behavior:
		Drop the message
	"""
class SendMsgPerMsg(Location):
	"""Hooks are called once for every message sent

	Arguments:
		message - The text of the message wrapped in a list to enable mutability
					This behavior is abnormal and should be fixed in the future.

	Truthy Return Behavior:
		Drop the message
	"""

class SendMsgPerUser(Location):
	"""Hooks are called once for every user a message is sent to

	Arguments:
		recipient 	- JID of the message recipient
		message 	- The message stanza

	Truthy Return Behavior:
		Drop the message for that user

	"""

class SendMsgPerResource(Location):
	"""Hooks are called once for every user a message is sent to

	Arguments:
		user		- JID of the message recipient
		resource	- Resource of the message recipient
		message 	- The message stanza

	Truthy Return Behavior:
		Drop the message for that resource

	"""

class EvMsg(Location):
	"""Hooks are called once for every message the bot receives

	Arguments:
		user		- JID of the sender
		message		- original message stanza

	Truthy Return Behavior:
		Do not process the message further

	"""

class PreEvMsg(Location): pass
class PostEvMsg(Location): pass

class EvIq(Location):
	"""Hooks are called once for every iq the bot receives

	Arguments:
		user		- JID of the sender
		iq			- original iq stanza

	Truthy Return Behavior:
		Do not process the iq further

	"""

class PreEvIq(Location): pass
class PostEvIq(Location): pass

class EvOnline(Location):
	"""Call hooks once for every Away presence nofitication

	Arguments:
		user		- JID of the sender
		status		- original presence stanza

	Truthy Return Behavior:
		Stop any potential processing

	"""

class PreEvOnline(Location): pass
class PostEvOnline(Location): pass

class EvAway(Location):
	"""Call hooks once for every Away presence nofitication

	Arguments:
		user		- JID of the sender
		status		- original presence stanza

	Truthy Return Behavior:
		Stop any potential processing

	"""

class PreEvAway(Location): pass
class PostEvAway(Location): pass

class EvChat(Location):
	"""Call hooks once for every Chat status nofitication

	Arguments:
		user		- JID of the sender
		status		- original presence stanza

	Truthy Return Behavior:
		Stop any potential processing

	"""

class PreEvChat(Location): pass
class PostEvChat(Location): pass

class EvDnd(Location):
	"""Call hooks once for every DND status nofitication

	Arguments:
		user		- JID of the sender
		status		- original presence stanza

	Truthy Return Behavior:
		Stop any potential processing

	"""

class PreEvDnd(Location): pass
class PostEvDnd(Location): pass

class EvXa(Location):
	"""Call hooks once for every XA status nofitication

	Arguments:
		user		- JID of the sender
		status		- original presence stanza

	Truthy Return Behavior:
		Stop any potential processing

	"""

class PreEvXa(Location): pass
class PostEvXa(Location): pass

class EvUnavailable(Location):
	"""Call hooks once for every Unavailable notification

	Arguments:
		user		- JID of the sender
		presence	- original presence stanza

	Truthy Return Behavior:
		Stop any potential processing

	"""

class PreEvUnavailable(Location): pass
class PostEvUnavailable(Location): pass

class EvSubscribe(Location):
	"""Call hooks once for every Unavailable notification

	Arguments:
		user		- JID of the sender
		presence	- original presence stanza

	Truthy Return Behavior:
		Stop any potential processing

	"""

class PreEvSubscribe(Location): pass
class PostEvSubscribe(Location): pass

class EvSubscribed(Location):
	"""Call hooks once for every Unavailable notification

	Arguments:
		user		- JID of the sender
		presence	- original presence stanza

	Truthy Return Behavior:
		Stop any potential processing

	"""

class PreEvSubscribed(Location): pass
class PostEvSubscribed(Location): pass

class EvUnsubscribe(Location):
	"""Call hooks once for every Unavailable notification

	Arguments:
		user		- JID of the sender
		presence	- original presence stanza

	Truthy Return Behavior:
		Stop any potential processing

	"""

class PreEvUnsubscribe(Location): pass
class PostEvUnsubscribe(Location): pass

class EvUnsubscribed(Location):
	"""Call hooks once for every Unavailable notification

	Arguments:
		user		- JID of the sender
		presence	- original presence stanza

	Truthy Return Behavior:
		Stop any potential processing

	"""

class PreEvUnsubscribed(Location): pass
class PostEvUnsubscribed(Location): pass
