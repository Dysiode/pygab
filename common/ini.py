﻿import traceback

from	dict4ini	import	DictIni
from	os.path		import	abspath, curdir, join

global iMan

class DictIniWrapper(DictIni):
	def has_entry(self, section, key, entry):
		'''has_entry(str section, str key, * entry) -> bool

		Return true if 'entry' is in the 'key' of 'section' of 'ini'

		'''
		if self.has_key(section) and self[section].has_key(key):
			return entry in self[section][key]
		return False

	def add_entry(self, section, key, entry):
		'''add_entry(str section, str key, * entry) -> bool

		Add 'entry' to 'key' in 'section'. Return False if entry exists.

		'''
		if self.has_entry(section, key, entry):
			return False

		if self.has_key(section) and self[section].has_key(key):
			self[section][key].append(entry)
		else:
			self[section][key] = [entry]
		self.save()
		return True

	def del_entry(self, section, key, entry):
		'''del_entry(str section, str key, * entry) -> bool

		"del an flag, return 0 if they didn't have the flag"

		'''
		if not self.has_entry(section, key, entry):
			return False

		self[section][key].remove(entry)
		if not self[section][key]:
			del self[section][key]
		self.save()
		return True

	def set_entry(self, section, key, entry):
		'''set_entry(str section, str key, * entry) -> bool

		Replace all entries in 'key' in 'section' with 'entry'

		'''
		self[section][key] = [entry]
		self.save()
		return True


class IniManager(object):

	'''IniManager is a convience class for managing ini files.

	It provides functions for loading and unloading ini files and
	for managing the files.

	'''

	def __init__(self, temp_path='templates'):
		'''IniManager(str temp_path='templates') -> None

		'''
		self.temp_path = (curdir, temp_path)

	def __get__(self, name):
		'''__get__(str name) -> bool

		Return True if 'name'.ini is loaded.

		'''
		assert isinstance(name, basestring), 'Recived a %s typed variable' % type(name)

		return self.__dict__.has_key(name.lower())

	def load(self, name, *subfolders):
		'''load_ini(str name, *subfolders) -> Bool

		Loads 'name'.ini making it available for use.
		Return True if 'name'.ini loaded properly.

		'''
		name = name.lower()
		path = [curdir]
		path.extend(subfolders)
		path.append("%s.ini" % name)
		try:
			ini = DictIniWrapper(join(*path), encoding = "utf8")
			self.__dict__[name] = ini
			ini.read()
			return True
		except IOError:
			return False
		except:
			traceback.print_exc()
			return False

	def loaded(self, name):
		'''loaded(str name) -> bool

		Return True if 'name'.ini is loaded.

		'''
		return self.__get__(name)

	def unload(self, name, save=False):
		'''unload(str name, bool save=False) -> bool

		Unloads 'name'.ini.
		If 'save' is true ini.save will be called.

		'''
		name = name.lower()
		if name in self.__dict__:
			if save:
				self.__dict__[name].save()
			del self.__dict__[name]
			return True
		return False

	def rename(self, name, new_name):
		'''rename(str name, str new_name) -> None

		Renames the ini 'name' to 'new_name'.

		'''
		name = name.lower()
		ini = self.__dict__[name]
		ini.setfilename(new_name)
		ini.save()

	def readall(self):
		'''readall() -> None

		Read all loaded ini files.

		'''
		for ini in self.__dict__.itervalues():
			if not isinstance(ini, DictIni):
				continue
			ini.read()

	def saveall(self):
		'''readall() -> None

		Save all loaded ini files.

		'''
		for ini in self.__dict__.itervalues():
			if not isinstance(ini, DictIni):
				continue
			ini.save()
			#print "DEBUG: Saving %s" % ini.getfilename()

		#print "Debug: IniManager has saved all ini files."

	def has_entry(self, ini, section, key, entry):
		'''has_entry(* ini, str section, str key, * entry) -> bool

		Return true if 'entry' is in the 'key' of 'section' of 'ini'

		'''
		if not isinstance(ini, DictIni):
			# Always returns False if the ini hasn't been loaded.
			try:
				ini = self.__dict__[ini]
			except KeyError:
				return False

		if ini.has_key(section) and ini[section].has_key(key):
			return entry in ini[section][key]
		return False

	def add_entry(self, ini, section, key, entry):
		'''add_entry(* ini, str section, str key, * entry) -> bool

		Add 'entry' to 'key' in 'section'. Return False if entry exists.

		'''
		if not isinstance(ini, DictIni):
			# Always returns False if the ini hasn't been loaded.
			try:
				ini = self.__dict__[ini]
			except KeyError:
				return False

		if self.has_entry(ini, section, key, entry):
			return False

		if ini.has_key(section) and ini[section].has_key(key):
			ini[section][key].append(entry)
		else:
			ini[section][key] = [entry]
		ini.save()
		return True

	def del_entry(self, ini, section, key, entry):
		'''del_entry(* ini, str section, str key, * entry) -> bool

		"del an flag, return 0 if they didn't have the flag"

		'''
		if not isinstance(ini, DictIni):
			# Always returns False if the ini hasn't been loaded.
			try:
				ini = self.__dict__[ini]
			except KeyError:
				return False

		if not self.has_entry(ini, section, key, entry):
			return False

		ini[section][key].remove(entry)
		if not ini[section][key]:
			del ini[section][key]
		ini.save()
		return True

	def set_entry(self, ini, section, key, entry):
		'''set_entry(* ini, str section, str key, * entry) -> bool

		Replace all entries in 'key' in 'section' with 'entry'

		'''
		if not isinstance(ini, DictIni):
			# Always returns False if the ini hasn't been loaded.
			try:
				ini = self.__dict__[ini]
			except KeyError:
				return False

		ini[section][key] = [entry]
		ini.save()
		return True

	def _merge_template(self, ini, template):
		'''_merge_template(DictIni ini, DictIni template) -> DictIni

		Fills in any missing entries from the config.
		Note: You can pass any dictionary style object through this.

		'''
		if not isinstance(ini, DictIni):
			ini = self.__dict__[ini]

		for (section, key) in template.items():
			if not ini.has_key(section) or not ini[section].has_key(key):
				self._read_or_prompt(ini, section, key, template.get_comment(key))
				ini[section][key] = template[section][key]
		return ini

	def _read_or_prompt(self, ini, section, option, description):
		'''Read an option from 'ini', or prompt for it'''
		if not ini[section].get(option):
			ini[section][option] = raw_input('%s\nLeave Blank to use Default > ' % description)

iMan = IniManager()
