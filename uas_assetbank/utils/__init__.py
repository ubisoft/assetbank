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
import os
import json
import shutil
from typing import List

import bpy


def get_thumbnail_path(blend, collection_name):
    """
    Return a unique default thumbnail path.
    """
    blend = Path(blend)
    return str(blend.parent.joinpath("thumbnails", f"UASBANK_{blend.stem}_{collection_name}.jpg"))


def export_thumbnails(context, path, resolution=256):
    """
    Takes a screenshot of the scene and output it to a file.
    """
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    backup_out_path = context.scene.render.filepath
    backup_extention = context.scene.render.image_settings.file_format
    backup_res_x = context.scene.render.resolution_x
    backup_res_y = context.scene.render.resolution_y
    context.scene.render.resolution_y = resolution
    context.scene.render.resolution_x = resolution

    context.scene.render.filepath = path
    context.scene.render.image_settings.file_format = "JPEG"
    bpy.ops.render.opengl(write_still=True)
    context.scene.render.image_settings.file_format = backup_extention
    context.scene.render.filepath = backup_out_path
    context.scene.render.resolution_y = backup_res_y
    context.scene.render.resolution_x = backup_res_x


def backup_file(filepath):
    path = Path(filepath)
    if path.is_file():
        shutil.copy(path, path.parent.joinpath(f"{path.stem}_backup{path.suffix}"))


def add_entry(
    json_path,
    key,
    collection_name,
    blend_path,
    thumbnail_path=None,
    tags: List[str] = None,
    metadata: dict = None,
    backup=True,
):
    """
    Add an asset entry into a json librarie and optonnaly backup the existing json prior to adding the entry.
    """
    data = dict()
    if json_path and Path(json_path).exists():
        if backup:
            backup_file(json_path)
        with open(json_path, "r") as f:
            data = json.load(f)

    with open(json_path, "w") as f:
        d = dict(blend_path=blend_path, data_name=collection_name)
        if thumbnail_path is not None:
            d["thumbnail_path"] = thumbnail_path
        if tags is not None:
            d["tags"] = tags
        if metadata is not None:
            d["metadata"] = metadata

        data[key] = d
        if data:
            json.dump(data, f, indent=2)


def delete_entry(json_path, key, backup=True):
    """
    Remove the asset in the json and optionnaly backup the current json.
    """
    if json_path and Path(json_path).exists():
        if backup:
            backup_file(json_path)
        with open(json_path, "r") as f:
            data = json.load(f)
        with open(json_path, "w") as f:
            if key in data:
                del data[key]
                json.dump(data, f, indent=2)


def list_entries(json_path) -> List[dict]:
    """
    Reads a jsonand return its content.
    """
    if json_path and Path(json_path).exists():
        with open(json_path, "r") as f:
            data = json.load(f)
        return data.items()
    return list()


def get_entry_name(name, blend_path):
    """
    Get a unique entry name from a collection and a .blend path.
    """
    return f"{name}:{Path ( blend_path ).stem}"


def asset_match_filter(asset, filters: List[str], matched_value):
    """
    Filter assets based on various criteria such as name, filename or tags. This is used for the list view in the ui.
    """
    flag = matched_value
    to_search = f"{asset.library} {asset.data_name} {Path ( asset.file ).stem} {asset.tags}".lower().strip()

    for filter in filters:
        if filter not in to_search:
            flag &= 0

    return flag
