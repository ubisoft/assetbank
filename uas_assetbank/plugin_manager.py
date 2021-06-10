# GPLv3 License
#
# Copyright (C) 2020 Ubisoft
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Basic plugin loading/unloading.
"""

from pathlib import Path
import importlib.util


def _nop(*args, **kwargs):
    """
    Do nothing function.
    """
    pass


#
# Callbacks.
#
on_import_post = _nop

# The plugin module when one is specified in the ui.
plugin_module = None


def register_plugin(plugin_path):
    """
    Load a python plugin as a module, calls its register (because of the banking operator) and swap the plugin manager callbacks with the plugin's ones.
    """
    global plugin_module
    plugin_path = Path(plugin_path)
    if plugin_path.parent == Path(__file__).parent:  # For the default plugin
        name = f"{__package__}.{plugin_path.stem}"
    else:
        name = plugin_path.stem

    spec = importlib.util.spec_from_file_location(name, plugin_path)
    plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin_module)
    plugin_module.register()

    global on_import_post
    if hasattr(plugin_module, "on_import_post"):
        on_import_post = plugin_module.on_import_post


def unregister_plugin():
    if plugin_module is not None:
        plugin_module.unregister()
    global on_import_post
    on_import_post = _nop
