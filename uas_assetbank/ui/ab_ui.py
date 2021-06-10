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

from .. import utils
from .. import icons

from .. import preferences
from .. import display_version
from ..thumbnails import get_thumbnail

import bpy

"""
UI elements and panels
"""


class UAS_PT_AssetInfo(bpy.types.Panel):
    bl_label = "Asset Info"
    bl_idname = "UAS_PT_AssetInfo"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "UAS Asset Bank"
    bl_parent_id = "UAS_PT_AssetBank"

    @classmethod
    def poll(cls, context):
        prefs = preferences.get_preferences()
        return any([lib.enabled for lib in prefs.libraries])

    def draw(self, context):
        props = context.window_manager.uas_asset_bank
        layout = self.layout
        if props.selected_index >= 0:
            box = layout.box()
            # box.prop ( props, "thumbnail_scale", text = "Preview Size" )
            asset = props.assets[props.selected_index]
            thumb = get_thumbnail(asset)
            box.template_icon(thumb.icon_id, scale=10)
            box.operator(
                "uas.asset_bank_generate_thumbnail",
                text="Regenerate Thumbnail",
                icon="FILE_REFRESH",
            ).index = props.selected_index

            box = layout.box()
            split = box.split(factor=0.1, align=True)
            split.label(text="Collection:")
            col = split.column()
            col.enabled = False
            col.prop(props.assets[props.selected_index], "data_name", text="")

            split = box.split(factor=0.1, align=True)
            split.label(text="Blend File:")
            col = split.column()
            col.alert = True
            col.enabled = False
            if not Path(props.assets[props.selected_index].file).is_file():
                col.alert = True
            else:
                col.alert = False
            col.prop(props.assets[props.selected_index], "file", text="")

            split = box.split(factor=0.1, align=True)
            split.label(text="Tags:")
            col = split.column()
            col.enabled = False
            col.prop(props.assets[props.selected_index], "tags", text="")


class UAS_PT_AssetBank(bpy.types.Panel):
    bl_label = f"Asset Bank   V. {display_version or '(Unknown version)'}"
    bl_idname = "UAS_PT_AssetBank"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Asset Bank"

    def __init__(self):
        props = bpy.context.window_manager.uas_asset_bank
        if props.initialized is False:
            bpy.ops.uas.asset_bank_refresh()
            props.initialized = True

    def draw_header(self, context):
        self.layout.emboss = "NONE"
        icon = icons.icons_col["AssetBank_32"]
        row = self.layout.row(align=True)
        row.operator("assetbank.about", text="", icon_value=icon.icon_id)

    def draw_header_preset(self, context):
        self.layout.emboss = "NONE"
        row = self.layout.row(align=True)
        # blue BG not available in panel title bar
        # row.operator(
        #     "uas.asset_bank_toggle_overlay",
        #     text="",
        #     icon="VIEW3D",
        #     depress=props.toggle_overlay,
        # )
        row.separator(factor=0.5)
        row.menu("ASSETBANK_MT_prefs_main_menu", icon="PREFERENCES", text="")
        row.separator(factor=1.0)

    def draw(self, context):
        props = context.window_manager.uas_asset_bank
        prefs = preferences.get_preferences()
        layout = self.layout

        if not any([lib.enabled for lib in prefs.libraries]):
            layout.separator()
            row = layout.row()
            col = row.column()
            col.alert = True
            col.label(text="No valid asset library found.")
            col.label(text="Please add a library in the addon preferences:")
            row = layout.row()
            row.operator(
                "preferences.addon_show", text="Add-on Preferences..."
            ).module = "uas_assetbank"
            layout.separator()
        else:
            layout.operator(
                "uas.asset_bank_toggle_overlay",
                icon="VIEW3D",
                depress=props.toggle_overlay,
            )

            col = layout.column()
            if not bpy.data.filepath:
                row = col.box()
                row.alert = True
                row.label(text="Banking not available. Scene not saved.")
            elif all([lib.readonly for lib in prefs.libraries]):
                row = col.box()
                row.alert = True
                row.label(text="Banking not available. All banks are read-only.")
            else:
                box = col.box()
                col = box.column(align=True)
                col.prop(props, "library", text="Bank to", icon="HOME")
                row = col.row()
                row.scale_y = 2
                row.prop(props, "collection", text="")
                # row.operator ( "uas.asset_bank_store", text = "", icon = "EXPORT" )

            col = layout.column()
            col.separator(factor=2)
            row = col.row()
            row.operator(
                "uas.asset_bank_refresh", text="Reload Libraries", icon="FILE_REFRESH"
            )
            col.template_list(
                "UAS_UL_AssetBank_Items",
                "",
                props,
                "assets",
                props,
                "selected_index",
                rows=10,
            )


class UAS_UL_AssetBank_Items(bpy.types.UIList):
    def __init__(self):
        self.use_filter_show = True

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        thumb = get_thumbnail(item)
        # layout.scale_y = 2 Not working correctly
        col = layout.column(align=True)
        row = col.row(align=True)
        split = row.split(factor=0.75)
        row = split.row()
        row.template_icon(icon_value=thumb.icon_id)
        row.label(text=f"{item.nice_name}")
        row = split.row(align=True)
        row.label(text=f"{item.library}")
        op = row.operator("uas.asset_bank_import", text="", icon="IMPORT")
        op.index = index
        op.append = True

        op = row.operator("uas.asset_bank_import", text="", icon="LINK_BLEND")
        op.index = index
        op.append = False

        row.alert = True
        row.operator("uas.asset_bank_delete", text="", icon="TRASH").index = index
        row.alert = False

    def draw_filter(self, context, layout):
        props = context.window_manager.uas_asset_bank
        row = layout.row()

        subrow = row.row(align=True)
        subrow.prop(props, "filter_name", text="")
        icon = "ZOOM_OUT" if self.use_filter_invert else "ARROW_LEFTRIGHT"
        subrow.prop(self, "use_filter_invert", text="", icon=icon, toggle=True)

        icon = "TRIA_UP" if self.use_filter_sort_reverse else "TRIA_DOWN"
        row.prop(self, "use_filter_sort_reverse", text="", icon=icon)

    def filter_items(self, context, data, prop):
        helper_funcs = bpy.types.UI_UL_list
        assets = getattr(data, prop)
        flt_flags = []
        filter_name = context.window_manager.uas_asset_bank.filter_name
        if filter_name:
            for asset in assets:
                flag = utils.asset_match_filter(
                    asset, filter_name.strip().lower().split(), self.bitflag_filter_item
                )
                flt_flags.append(flag)

        flt_neworder = helper_funcs.sort_items_by_name(assets, "data_name")

        return flt_flags, flt_neworder


classes = (
    UAS_PT_AssetBank,
    UAS_PT_AssetInfo,
    UAS_UL_AssetBank_Items,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
