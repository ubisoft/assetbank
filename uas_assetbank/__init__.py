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

import logging
from pathlib import Path

import bpy
from bpy.props import (
    StringProperty,
    CollectionProperty,
    PointerProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
)

from . import ogl_browser
from . import plugin_manager
from . import preferences

from . import operators
from . import thumbnails
from . import icons
from .utils import utils_ui_operators


"""
Most of the addon is defined in here ie the UI and the operators (except for the bank operator which is implemented in the plugins).
"""

bl_info = {
    "name": "Asset Bank",
    "description": "Simple and fast asset banks manager",
    "author": "Ubisoft Animation Studio",
    "version": (1, 0, 1),
    "blender": (2, 83, 0),
    "location": "View3D",
    "wiki_url": "",
    "tracker_url": "",
    "category": "UAS",
}

__version__ = ".".join(str(i) for i in bl_info["version"])
display_version = __version__
# version_date = "2021-03-19:10:56:00 UTC"   # to do

if __name__ == "__main__":
    logger = logging.getLogger()
else:
    logger = logging.getLogger(__name__)


class UAS_AssetBank_Asset(bpy.types.PropertyGroup):
    identifier: StringProperty()
    file: StringProperty()
    data_name: StringProperty()
    type: StringProperty()
    library: StringProperty()
    nice_name: StringProperty()
    thumbnail_path: StringProperty()
    tags: StringProperty()


class UAS_AssetBank_Props(bpy.types.PropertyGroup):
    def collection_changed(self, context):
        if self.collection is not None:
            bpy.ops.uas.asset_bank_store("INVOKE_DEFAULT")

    def list_libraries(self, context):
        res = list()
        prefs = preferences.get_preferences()
        for lib in prefs.libraries:
            if lib.enabled and not lib.readonly:
                res.append((lib.name, lib.name, ""))

        res.sort(key=lambda x: x[1])
        return res

    def on_toggle_overlay_updated(self, context):
        if self.toggle_overlay:
            bpy.ops.uas.asset_bank_viewport_browser("INVOKE_DEFAULT")

    collection: PointerProperty(type=bpy.types.Collection, update=collection_changed)
    selected_index: IntProperty(default=-1)
    assets: CollectionProperty(type=UAS_AssetBank_Asset)
    initialized: BoolProperty(default=False)
    library: EnumProperty(items=list_libraries)
    filter_name: StringProperty(options={"TEXTEDIT_UPDATE"})
    toggle_overlay: BoolProperty(default=False, update=on_toggle_overlay_updated)


classes = (
    UAS_AssetBank_Asset,
    UAS_AssetBank_Props,
)


def register():
    logging.info(f"Register {__name__} version {__version__}")
    from . import ui
    print("\nRegistering UAS Asset Bank")

    for cls in classes:
        bpy.utils.register_class(cls)

    preferences.register()
    icons.register()
    thumbnails.register()
    operators.register()
    utils_ui_operators.register()
    ui.register()
    ogl_browser.register()

    bpy.types.WindowManager.uas_asset_bank = PointerProperty(type=UAS_AssetBank_Props)
    plugin_path = preferences.get_preferences().plugin_path
    if not Path(plugin_path).is_file():
        plugin_path = Path(__file__).parent.joinpath("default_plugin.py")
    plugin_manager.register_plugin(plugin_path)


def unregister():
    logging.info(f"Unregister {__name__} version {__version__}")
    from . import ui

    ogl_browser.unregister()
    ui.unregister()
    utils_ui_operators.unregister()
    operators.unregister()
    thumbnails.unregister()
    icons.unregister()
    preferences.unregister()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    plugin_manager.unregister_plugin()
    del bpy.types.WindowManager.uas_asset_bank


if __name__ == "__main__":
    register()
