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
Appends a collection from another blend file. And saves it.
"""

import argparse
import sys
from pathlib import Path
import bpy


def clean_scene():
    bl_data = bpy.data
    for object in bl_data.objects:
        bl_data.objects.remove(object)

    for col in bl_data.collections:
        bl_data.collections.remove(col)


def export(dest_blend, src_blend, collection):
    if Path(src_blend).exists():
        with bpy.data.libraries.load(src_blend, link=False) as (data_from, data_to):
            if collection in data_from.collections:
                data_to.collections.append(data_from.collections[data_from.collections.index(collection)])

        for coll in data_to.collections:
            bpy.context.scene.collection.children.link(coll)

    bpy.ops.wm.save_as_mainfile(filepath=dest_blend)
    sys.exit(0)


if __name__ == "__main__":
    if "--" not in sys.argv:
        argv = []  # as if no args are passed
    else:
        argv = sys.argv[sys.argv.index("--") + 1 :]  # get all args after "--"

    parser = argparse.ArgumentParser()
    parser.add_argument("dest_blend")
    parser.add_argument("src_blend")
    parser.add_argument("collection_to_append")

    args = parser.parse_args(argv)
    clean_scene()
    export(args.dest_blend, args.src_blend, args.collection_to_append)
