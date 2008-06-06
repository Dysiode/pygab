from pluginmount import PluginMount

__all__ = ['CommandMount', 'HookMount']

class CommandMount:
	"""
	Mount point for bot commands normal users can perform.

	Plugins implementing this mount should provide the following attributes:

	=====  =====================================================================
	name   The name of the command, used to call it.

	rank   The rank a user must be inorder to perform this command.

	file   The absolute path to a file. You are able to use __file__.

	=====  =====================================================================

	Plugins implementing this mount should also provide the following functions:
	=========  =================================================================
	__init__   This function gets passed an instance of the bot.

	__exit__   No arguments are passed to this function.

	   run     run gets passed two arguments:
	            - a JID object of the user calling the command
	            - a string object containing whatever the user said.

	=========  =================================================================


	"""
	__metaclass__ = PluginMount

	# A list of constants for user ranks.
	RANK_USER	= 'user'
	RANK_MOD	= 'moderator'
	RANK_ADMIN	= 'admin'

class HookMount:
	"""
	Mount point for hooks into various processes.

	Each hook location calls any available classes. If a hook returns True then
	all futher processing of hooks and code after the hook location is stopped.

	Plugins implementing this mount should provide the following attributes:

	=====  =====================================================================
	name   Not used but still needed. Don't ask.

	loc    The location of the hook to be run.

	=====  =====================================================================

	Plugins implementing this mount should also provide the following functions:
	=========  =================================================================
	__init__   This function gets passed an instance of the bot.

	__exit__   No arguments are passed to this function.

	   run     The number of arguments passed to run vary per location.
	            Hook locations should document what they pass.

	=========  =================================================================

	"""
	__metaclass__ = PluginMount

	# LOC_GET_MSG passes a JID object of the calling user
	# and a string containing their message.
	LOC_GET_MSG = 'get_msg'
