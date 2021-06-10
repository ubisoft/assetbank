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
This module defines the About panel.
"""

import bpy
from bpy.types import Operator
from .. import display_version


class Assetbank_OT_About(Operator):  # noqa 801
    bl_idname = "assetbank.about"
    bl_label = "About UAS Asset Bank..."
    bl_description = "More information about UAS Asset Bank..."
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        # Version
        ###############
        row = box.row()
        row.separator()
        row.label(
            text=f"Version: {display_version or '(Unknown version)'}   -   ({'March 2021'})   -    Ubisoft Animation Studio"
        )

        # Authors
        ###############
        row = box.row()
        row.separator()
        row.label(text="Written by the R&D team of Ubisoft Animation Studio")

        # Purpose
        ###############
        row = box.row()
        row.label(text="Purpose:")
        row = box.row()
        row.separator()
        col = row.column()
        col.label(
            text="Asset Bank provides an easy way to import assets from libraries"
        )
        col.label(text="directly into the current scene.")

        # Dependencies
        ###############
        # row = box.row()
        # row.label(text="Dependencies:")
        # row = box.row()
        # row.separator()
        #
        # Documentation
        # ##############
        # row = box.row()
        # row.label(text="Documentation:")
        # row = box.row()
        # row.separator()
        # row.operator(
        #     "assetbank.open_documentation_url",
        #     text="Documentation, Download, Feedback...",
        # ).path = "https://gitlab.com/ubisoft-animation-studio/mixer#mixer"

        box.separator()

        layout.separator(factor=1)

    def execute(self, context):
        return {"FINISHED"}


_classes = (Assetbank_OT_About,)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
