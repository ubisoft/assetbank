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

import bpy
from bpy.props import (
    IntProperty,
    BoolProperty,
    FloatVectorProperty,
)

from . import preferences
from . import plugin_manager
from .utils import get_thumbnail_path, delete_entry, list_entries, export_thumbnails
from .thumbnails import get_thumbnail

"""
Operators for UAS Asset Bank
"""


class UAS_AssetBank_Delete(bpy.types.Operator):
    bl_idname = "uas.asset_bank_delete"
    bl_label = "Delete"
    bl_description = "Delete from database."
    bl_options = {"INTERNAL"}

    index: IntProperty(default=-1)

    def execute(self, context):
        props = context.window_manager.uas_asset_bank
        prefs = preferences.get_preferences()
        if 0 <= self.index < len(props.assets):
            asset = props.assets[self.index]
            for lib in prefs.libraries:
                if asset.library == lib.name:
                    delete_entry(lib.path, asset.identifier)
                    bpy.ops.uas.asset_bank_refresh()
                    props.selected_index = min(self.index, len(props.assets) - 1)
                    break

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text="Delete from database ?")


class UAS_AssetBank_Refresh(bpy.types.Operator):
    bl_idname = "uas.asset_bank_refresh"
    bl_label = "Refresh"
    bl_description = "Refresh"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        props = context.window_manager.uas_asset_bank
        assets = props.assets
        assets.clear()

        addon_prefs = preferences.get_preferences()
        for lib in addon_prefs.libraries:
            if not lib.enabled:
                continue
            for key, values in list_entries(lib.path):
                new_asset = assets.add()
                new_asset.identifier = key
                new_asset.file = values["blend_path"].replace("/", "\\")
                new_asset.data_name = values["data_name"]
                new_asset.library = lib.name
                blend_name = Path(new_asset.file).name
                new_asset.nice_name = f"{new_asset.data_name}::{blend_name}"
                new_asset.thumbnail_path = values.get(
                    "thumbnail_path",
                    get_thumbnail_path(new_asset.file, new_asset.data_name),
                ).replace("/", "\\")
                new_asset.tags = "; ".join(values.get("tags", list("")))

        props.selected_index = min(props.selected_index, len(assets) - 1)
        if context.area is not None:
            context.area.tag_redraw()
        return {"FINISHED"}


class UAS_AssetBank_Import(bpy.types.Operator):
    bl_idname = "uas.asset_bank_import"
    bl_label = "Import Asset"
    bl_description = "Import Asset"
    bl_options = {"INTERNAL"}

    index: IntProperty(default=-1)
    append: BoolProperty(default=False)
    location: FloatVectorProperty()

    def execute(self, context):
        props = context.window_manager.uas_asset_bank
        if 0 <= self.index < len(props.assets):
            asset = props.assets[self.index]
            if Path(asset.file).exists():
                with bpy.data.libraries.load(asset.file, link=not self.append) as (
                    data_from,
                    data_to,
                ):
                    if asset.data_name in data_from.collections:
                        data_to.collections.append(asset.data_name)
                    else:
                        self.report(
                            {"WARNING"},
                            f"{asset.data_name} could not be found in {asset.file}",
                        )

                new_col = data_to.collections[0]
                if self.append:
                    # if coll.name in context.scene.collection.children:
                    # context.scene.collection.children.link ( unlink_hierarchy ( coll ) )
                    # else:
                    try:
                        context.scene.collection.children.link(new_col)
                        plugin_manager.on_import_post(context.scene, new_col)
                        for o in context.selected_objects:
                            o.select_set(False)
                        for o in new_col.objects:
                            o.select_set(True)
                    except RuntimeError:
                        self.report(
                            {"WARNING"},
                            f"{new_col.name} already in {context.scene.collection.name}",
                        )
                        return {"CANCELLED"}
                else:
                    instance = bpy.data.objects.new(new_col.name, None)
                    instance.location = self.location
                    instance.instance_type = "COLLECTION"
                    instance.instance_collection = new_col
                    context.scene.collection.objects.link(instance)
                    plugin_manager.on_import_post(context.scene, instance)
                    for o in context.selected_objects:
                        o.select_set(False)
                    instance.select_set(True)

                return {"FINISHED"}
            else:
                self.report({"WARNING"}, f"{asset.file} does not exists.")
        return {"CANCELLED"}

    def invoke(self, context, event):
        self.location = context.scene.cursor.location
        return self.execute(context)


class UAS_AssetBank_GenerateThumbnail(bpy.types.Operator):
    bl_idname = "uas.asset_bank_generate_thumbnail"
    bl_label = "Generate Thumbnail"
    bl_description = "Generate Thumbnail"
    bl_options = {"INTERNAL"}

    index: IntProperty(default=-1)

    def execute(self, context):
        props = context.window_manager.uas_asset_bank
        if 0 <= self.index < len(props.assets):
            asset = props.assets[self.index]
            export_thumbnails(
                context,
                asset.thumbnail_path,
                preferences.get_preferences().thumbnails_resolution,
            )
            get_thumbnail(asset).reload()
        return {"FINISHED"}


class UAS_AssetBank_ToggleOverlay(bpy.types.Operator):
    bl_idname = "uas.asset_bank_toggle_overlay"
    bl_label = "Display Library Overlay"
    bl_description = "Display the asset thumbnails in the 3D viewport"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        props = context.window_manager.uas_asset_bank
        props.toggle_overlay = not props.toggle_overlay
        return {"FINISHED"}


classes = (
    UAS_AssetBank_Delete,
    UAS_AssetBank_Import,
    UAS_AssetBank_Refresh,
    UAS_AssetBank_GenerateThumbnail,
    UAS_AssetBank_ToggleOverlay,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
