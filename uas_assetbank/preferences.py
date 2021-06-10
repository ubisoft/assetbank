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


from pathlib import Path
import json
import os

import bpy
from bpy.types import AddonPreferences
from bpy.props import (
    StringProperty,
    CollectionProperty,
    IntProperty,
    BoolProperty,
)
from .plugin_manager import unregister_plugin, register_plugin


# API Part
def get_preferences():
    preferences = bpy.context.preferences
    return preferences.addons[__package__].preferences


class UAS_AssetBankPreferences_AddLibrary(bpy.types.Operator):
    bl_idname = "uas.asset_bank_preferences_addlibrary"
    bl_label = "Add a New Library"
    bl_description = "Add a new libary to pick assets from"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        prefs = get_preferences()
        col = prefs.libraries.add()
        col.name = f"Library {len ( prefs.libraries )}"

        return {"FINISHED"}


class UAS_AssetBankPreferences_RemoveLibrary(bpy.types.Operator):
    bl_idname = "uas.asset_bank_preferences_removelibrary"
    bl_label = "Remove Library"
    bl_description = "Remove Library"
    bl_options = {"INTERNAL"}

    index: IntProperty(default=-1)

    def execute(self, context):
        prefs = get_preferences()
        if 0 <= self.index < len(prefs.libraries):
            prefs.libraries.remove(self.index)
            bpy.ops.uas.asset_bank_refresh()
            return {"FINISHED"}

        return {"CANCELLED"}


class UAS_AssetBankPreferences_Library(bpy.types.PropertyGroup):
    def path_updated(self, context):
        self["path"] = bpy.path.abspath(self["path"])
        if not self["path"].endswith(".json"):
            self["path"] += ".json"

        json_path = Path(self["path"])
        os.makedirs(json_path.parent, exist_ok=True)
        if self["path"] and not json_path.exists():
            with open(self["path"], "w") as f:
                json.dump({}, f, indent=2)

        bpy.ops.uas.asset_bank_refresh()

    def refresh_bank(self, context):
        bpy.ops.uas.asset_bank_refresh()

    path: StringProperty(subtype="FILE_PATH", update=path_updated)
    name: StringProperty(update=refresh_bank)
    enabled: BoolProperty(default=True, update=refresh_bank)
    readonly: BoolProperty(default=False)


class UAS_AssetBankPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        layout.label(text="Libraries:")
        for i, library in enumerate(self.libraries):
            box = layout.box()
            row = box.row(align=True)
            row.prop(self.libraries[i], "enabled", text="", emboss=True)
            row.prop(self.libraries[i], "name", text="")
            if library.enabled:
                row = box.row(align=True)
                split = row.split(factor=0.03)
                split.separator()
                col = split.column()
                row = col.row(align=True)
                row.prop(self.libraries[i], "path", text="Path")
                row.operator("uas.asset_bank_preferences_removelibrary", text="", icon="TRASH").index = i
                row = box.row()
                row.prop(self.libraries[i], "readonly", text="Read Only")

        layout.operator("uas.asset_bank_preferences_addlibrary", icon="ADD")
        layout.separator()

        box = layout.box()
        box.prop(self, "thumbnails_resolution", text="Thumbnails Resolution")
        box.prop(self, "auto_save")
        layout.separator()

        box = layout.box()
        box.label(text="Developper options")
        box.prop(self, "plugin_path", text="Plugin Path")

    def plugin_path_updated(self, context):
        unregister_plugin()
        if Path(self.plugin_path).is_file():
            register_plugin(self.plugin_path)
        else:
            register_plugin(Path(__file__).parent.joinpath("default_plugin.py"))

    libraries: CollectionProperty(type=UAS_AssetBankPreferences_Library)
    thumbnails_resolution: IntProperty(default=256, min=32, max=2048)
    auto_save: BoolProperty(
        name="Save Prior To Bank",
        description="Save the scene before banking. Saving can be slow if file is big or on network.",
    )
    plugin_path: StringProperty(subtype="FILE_PATH", update=plugin_path_updated)


_classes = (
    UAS_AssetBankPreferences_Library,
    UAS_AssetBankPreferences,
    UAS_AssetBankPreferences_AddLibrary,
    UAS_AssetBankPreferences_RemoveLibrary,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
