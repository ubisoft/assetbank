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

Provides the UAS_AssetBank_Store class which needs to be inherited from in order to provide custom ui and behavior when banking.
The plugin is python file which needs
You plugin needs:
 - to inherit from the Operator UAS_AssetBank_Store and override the plugin_execute method.
 - provide a register/unregister method to register/unregister your operator using the blender api.
 - (Optionnal) Define on_import_post ( scene, newly_created_col_or_instance ) function. It will be called at the end of the import.

 Look at the plugin_example folder for an example.
"""

__all__ = ["UAS_AssetBank_Store", "EntryData"]

import os
from dataclasses import dataclass
from typing import List

import bpy

from .utils import get_thumbnail_path, get_entry_name, add_entry, export_thumbnails
from . import preferences
from .thumbnails import reload_thumbnail


@dataclass
class EntryData:
    """
    Fields used to tell the bank what is the collection name and where to find it.
    Other fields are optionnal.
    """

    collection_name: str
    blend_path: str
    thumbnail_path: str = None
    tags: List[str] = None  # Used for filtering in the list view.
    metadata: dict = None  # These are stored in the json but that's all currently ie they are not displayed in the panel nor used.


class UAS_AssetBank_Store(bpy.types.Operator):
    """
    Base implementation of an operator being called for banking. This is the builtin behavior used in default_plugin.
    Since this is an operator you'll need to register/unregister.

    Fill the database, generate thumbnails and refresh the ui.

    In order to customize it you need to inherit from it and override the plugin_execute method.

    .. info::

        This is an operator because this is the only way to have custom ui.

    .. warning::

        As of 2.83, properties are not inherited, and mixin classes did not work either on an operator => No blender properties for the base class.

    """

    bl_idname = "uas.asset_bank_store"
    bl_label = "Store Collection"
    bl_description = "Store Collection."
    bl_options = {"INTERNAL"}

    def __init__(self):
        self._do_backup = True
        self._do_thumbnail = True

    @property
    def backup(self):
        return self._do_backup

    @backup.setter
    def backup(self, value: bool):
        self._do_backup = value

    @property
    def export_thumbnail(self):
        return self._do_thumbnail

    @export_thumbnail.setter
    def export_thumbnail(self, value: bool):
        self._do_thumbnail = value

    def execute(self, context):
        # This is a bit hacky. But properties being not implemented I prefer to manage the collection here instead of having to redefine it in subclasses.
        collection = context.window_manager.uas_asset_bank.collection
        if collection is None:
            return {"CANCELLED"}

        props = context.window_manager.uas_asset_bank
        prefs = preferences.get_preferences()

        lib_to_bank = None
        for lib in prefs.libraries:
            if props.library == lib.name:
                lib_to_bank = lib
        if prefs.auto_save:
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        entry_data = self.plugin_execute(collection, os.path.dirname(lib_to_bank.path))

        if entry_data.thumbnail_path is None:
            thumbnail_path = get_thumbnail_path(entry_data.blend_path, entry_data.collection_name)
        else:
            thumbnail_path = entry_data.thumbnail_path

        entry_id = get_entry_name(entry_data.collection_name, entry_data.blend_path)
        add_entry(
            lib_to_bank.path,
            entry_id,
            entry_data.collection_name,
            entry_data.blend_path,
            entry_data.thumbnail_path,
            tags=entry_data.tags,
            metadata=entry_data.metadata,
            backup=self.backup,
        )

        if self._do_thumbnail:
            export_thumbnails(context, thumbnail_path, prefs.thumbnails_resolution)
        reload_thumbnail(props.library, entry_id)

        bpy.ops.uas.asset_bank_refresh()
        context.window_manager.uas_asset_bank.collection = None  # clear the property in order to clear the ui.
        self.report({"INFO"}, f"Successfully Banked {entry_data.collection_name}.")

        return {"FINISHED"}

    def plugin_execute(self, collection: bpy.types.Collection, library_dir: str) -> EntryData:
        """
        Takes in the collection chosed by the user.
        It needs to return a filled Entry_data in order for the bank to be add a new entry into the database.
        You could for instance launch a subprocess creating a new blend file with a collection
        and filling the Entry_data with the path of this new blend_file and collection.

        :param collection: The collection being processed.
        :param library_dir: Directory containing the database (json). Can be usefull if you need to put files in the same directory.
        :return: An Entry_data.
        """
        return EntryData(collection.name, bpy.data.filepath)
