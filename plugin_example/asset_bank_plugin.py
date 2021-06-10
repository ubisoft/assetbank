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

import os
import subprocess

import bpy
from bpy.props import StringProperty, BoolProperty

from uas_assetbank.api import UAS_AssetBank_Store, EntryData


def on_import_post(scene, imported_collection):
    # You could do something to the newly imported collection here.
    pass


class MY_STORE(UAS_AssetBank_Store):
    # You could expose other things like a category or description so you could fill in other type of informations
    # on an asset tracker. Although they won't be used by the addon nor showed.
    asset: StringProperty()
    tags: StringProperty(description="Multiple tags should be separated by semi colons")

    do_thumbnail: BoolProperty(name="Export Thumbnail", default=True)

    def invoke(self, context, event):
        collection = context.window_manager.uas_asset_bank.collection
        if collection:
            self.asset = collection.name

        return context.window_manager.invoke_props_dialog(self)

    def plugin_execute(self, collection, library_dir):
        # self.backup = False # If you don't need backup
        # self.export_thumbnail = False  # Handle thumbnail generation here if you have other ways of making/getting the thumbnail.

        asset_name = self.asset
        collection.name = asset_name
        bpy.ops.wm.save_as_mainfile()

        dst_blend = os.path.join(library_dir, f"{asset_name}.blend")
        subprocess.call(
            [
                bpy.app.binary_path,
                "--python",
                os.path.dirname(__file__) + "/asset_bank_publish.py",
                "--",
                dst_blend,
                bpy.data.filepath,
                collection.name,
            ]
        )

        return EntryData(
            asset_name,
            dst_blend,
            os.path.join(
                library_dir, f"thumbnails/{asset_name}.jpg"
            ),  # Currenly jpeg is hardcoded in the builtin thumbnail exporter. Don't put other extension because they will get overriden.
            tags=[s.strip() for s in self.tags.split(";")],
        )


def register():
    bpy.utils.register_class(MY_STORE)


def unregister():
    bpy.utils.unregister_class(MY_STORE)
