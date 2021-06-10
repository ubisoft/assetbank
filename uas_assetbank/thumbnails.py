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
from pathlib import Path

import bpy
import bpy.utils.previews

from .utils import get_thumbnail_path
previews_cols = dict()


def clean_thumbnails():
    global previews_cols
    for pcoll in previews_cols.values():
        bpy.utils.previews.remove(pcoll)
    previews_cols.clear()


def reload_thumbnail(library, asset_identifier):
    """
    Reload an asset thumbnail. This is used when banking an asset.
    """
    global previews_cols
    if library and asset_identifier:
        if library in previews_cols:
            if asset_identifier in previews_cols[library]:
                previews_cols[library][asset_identifier].reload()


def get_thumbnail(asset):
    """
    Get the thumbnail for an asset ( of type UAS_AssetBank_Asset ). The thumbnail is loaded from disk if not previously loaded.
    """
    global previews_cols
    thumb = previews_cols["BUILDTIN"]["no_preview"]
    if asset.library not in previews_cols:
        previews_cols[asset.library] = bpy.utils.previews.new()

    if asset.identifier not in previews_cols[asset.library]:
        if asset.thumbnail_path:
            thumb_path = asset.thumbnail_path
        else:
            thumb_path = get_thumbnail_path(asset.file, asset.data_name)
        if Path(thumb_path).is_file():
            thumb = previews_cols[asset.library].load(
                asset.identifier, thumb_path, "IMAGE"
            )
    else:
        thumb = previews_cols[asset.library][asset.identifier]

    return thumb


def register():
    global previews_cols
    pcoll = bpy.utils.previews.new()
    pcoll.load(
        "no_preview", os.path.join(os.path.dirname(__file__), "no_preview.jpg"), "IMAGE"
    )
    previews_cols["BUILDTIN"] = pcoll


def unregister():
    clean_thumbnails()
