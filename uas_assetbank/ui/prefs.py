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
This module defines the Preference menu.
"""

import bpy
from bpy.types import Menu


#############
# Preferences
#############


class ASSETBANK_MT_prefs_main_menu(Menu):  # noqa 801
    bl_idname = "ASSETBANK_MT_prefs_main_menu"
    bl_label = "AssetBank Settings"

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.operator(
            "preferences.addon_show", text="Add-on Preferences..."
        ).module = "uas_assetbank"

        # row = layout.row(align=True)
        # row.operator(
        #     "assetbank.open_documentation_url", text="Documentation"
        # ).path = "https://gitlab.com/ubisoft-animation-studio/mixer#mixer"

        row = layout.row(align=True)
        row.operator("assetbank.about", text="About...")

        layout.separator()
        row = layout.row(align=True)


_classes = (ASSETBANK_MT_prefs_main_menu,)


def register():

    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
