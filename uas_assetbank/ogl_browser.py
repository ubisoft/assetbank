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


import math
import time

import bpy
import blf
import bgl
import gpu

from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from .utils import asset_match_filter
from .thumbnails import get_thumbnail

#
# Drawing utils.
#

image_2d_fragment_shader = """
    in vec2 texCoord_interp;
    out vec4 fragColor;
    uniform sampler2D image;

    void main()
    {
      fragColor = pow(texture(image, texCoord_interp), vec4(2.2));
    }

"""

UNIFORM_SHADER_2D = gpu.shader.from_builtin("2D_UNIFORM_COLOR")
IMAGE_SHADER_2D = gpu.types.GPUShader(
    gpu.shader.code_from_builtin("2D_IMAGE")["vertex_shader"], image_2d_fragment_shader
)


def draw_square(position, width, height, color):
    vertices = (
        (position.x, position.y),
        (position.x + width, position.y),
        (position.x, position.y + height),
        (position.x + width, position.y + height),
    )
    indices = ((0, 1, 2), (2, 1, 3))

    batch = batch_for_shader(UNIFORM_SHADER_2D, "TRIS", {"pos": vertices}, indices=indices)

    UNIFORM_SHADER_2D.bind()
    UNIFORM_SHADER_2D.uniform_float("color", color)
    batch.draw(UNIFORM_SHADER_2D)


def draw_image(position, width, height, textureid):
    vertices = (
        (position.x, position.y),
        (position.x + width, position.y),
        (position.x, position.y + height),
        (position.x + width, position.y + height),
    )
    indices = ((0, 1, 2), (2, 1, 3))

    batch = batch_for_shader(
        IMAGE_SHADER_2D, "TRIS", {"pos": vertices, "texCoord": ((0, 0), (1, 0), (0, 1), (1, 1))}, indices=indices,
    )

    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, textureid)
    IMAGE_SHADER_2D.bind()
    IMAGE_SHADER_2D.uniform_int("image", 0)
    batch.draw(IMAGE_SHADER_2D)


class GlTexture:
    def __init__(self, image_preview):
        width, height = image_preview.image_size
        self._texture_id = bgl.Buffer(bgl.GL_INT, 1)
        self.pixel_buffer = bgl.Buffer(bgl.GL_FLOAT, width * height * 4, list(image_preview.image_pixels_float))

        bgl.glGenTextures(1, self._texture_id)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self._texture_id[0])
        bgl.glTexImage2D(
            bgl.GL_TEXTURE_2D, 0, bgl.GL_RGB, width, height, 0, bgl.GL_RGBA, bgl.GL_FLOAT, self.pixel_buffer,
        )

        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)

    def __del__(self):
        bgl.glDeleteTextures(1, self._texture_id)

    @property
    def texture_id(self):
        return self._texture_id[0]


#
#   Misc
#
def get_region_at_xy(context, x, y):
    """
    Does not support quadview right now

    :param context:
    :param x:
    :param y:
    :return: the region and the area containing this region
    """
    for area in context.screen.areas:
        if area.type != "VIEW_3D":
            continue
        # is_quadview = len ( area.spaces.active.region_quadviews ) == 0
        i = -1
        for region in area.regions:
            if region.type == "WINDOW":
                i += 1
                if region.x <= x < region.width + region.x and region.y <= y < region.height + region.y:

                    return region, area

    return None, None


class BlWidget:
    def __init__(self, context, parent=None):
        self._context = context
        self._parent = parent
        self._position = Vector((0, 0))  # Relative Position from parent
        self._height = 0.0
        self._width = 0.0

    @property
    def context(self):
        return self._context

    @property
    def parent(self) -> "BlWidget":
        return self._parent

    @property
    def absolute_position(self):
        parent_pos = Vector((0, 0)) if self._parent is None else self.parent.absolute_position
        return parent_pos + self.position

    @property
    def position(self) -> Vector:
        return self._position

    @position.setter
    def position(self, value: Vector):
        self._position = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value

    @property
    def bbox(self):
        return (
            Vector([self.position.x, self.position.y]),
            Vector([self.position.x + self.width, self.position.y + self.height]),
        )

    @property
    def absolute_bbox(self):
        my_low, my_high = self.bbox
        if self.parent is not None:
            my_low += self.parent.absolute_position
            my_high += self.parent.absolute_position

        return my_low, my_high

    def is_inside(self, x, y):
        low, high = self.absolute_bbox
        if low.x <= x < high.x and low.y <= y < high.y:
            return True

        return False

    def handle_event(self, event) -> bool:
        """
        Return True if you want the event to be processed by other widgets.
        :param event:
        :return:
        """
        return False

    def draw(self):
        pass


class AssetThumbnail(BlWidget):
    def __init__(self, index, asset, context, parent=None):
        BlWidget.__init__(self, context, parent)
        self.asset = asset
        self.texture = GlTexture(get_thumbnail(self.asset))
        self.show_tooltip = False
        self._prev_click = 0
        self.index = index

    def handle_event(self, event) -> bool:
        props = self.context.window_manager.uas_asset_bank
        self.show_tooltip = False
        region, _area = get_region_at_xy(self.context, event.mouse_x, event.mouse_y)
        mouse_x = event.mouse_x - region.x
        mouse_y = event.mouse_y - region.y

        if self.is_inside(mouse_x, mouse_y):
            self.show_tooltip = True
            if event.type == "LEFTMOUSE" and event.value == "PRESS":
                counter = time.perf_counter()
                props.selected_index = self.index
                if counter - self._prev_click < 0.2:
                    bpy.ops.uas.asset_bank_import(
                        append=False, location=self.context.scene.cursor.location, index=self.index,
                    )
                self._prev_click = counter
                return True

        return False

    def draw(self):
        draw_image(self.position, self.width, self.height, self.texture.texture_id)
        if self.show_tooltip:
            p = self.absolute_position
            vertices = (
                (p.x, p.y),
                (p.x + self.width, p.y + 20),
                (p.x, p.y + 20),
                (p.x + self.width, p.y),
            )
            indices = ((0, 1, 2), (0, 1, 3))

            batch = batch_for_shader(UNIFORM_SHADER_2D, "TRIS", {"pos": vertices}, indices=indices)

            UNIFORM_SHADER_2D.bind()
            UNIFORM_SHADER_2D.uniform_float("color", [0, 0, 0, 1])
            batch.draw(UNIFORM_SHADER_2D)

            blf.color(0, 0.99, 0.99, 0.99, 1)
            blf.size(0, 11, 72)
            text_width, text_height = blf.dimensions(0, self.asset.data_name)
            posx = (self.width - text_width) * 0.5 + self.absolute_position.x
            blf.position(0, posx, 8, 0)
            blf.draw(0, self.asset.data_name)


class AssetBrowser(BlWidget):
    def __init__(self, context, parent=None):
        BlWidget.__init__(self, context, parent)
        self.item_per_page = 10
        self.current_page = 0
        self.max_page = self.current_page
        self.asset_thumbnails = list()

        self.paddingx = 2
        self.height = 150
        self.width = self.item_per_page * (self.height + self.paddingx) + self.paddingx
        self.filter_name = self.context.window_manager.uas_asset_bank.filter_name

        self.load_page()

    def load_page(self):
        self.asset_thumbnails = list()
        props = self.context.window_manager.uas_asset_bank
        assets = [(i, a) for i, a in enumerate(props.assets)]
        assets.sort(key=lambda a: a[1].data_name.lower())
        if props.filter_name != "":
            assets = [a for a in assets if asset_match_filter(a[1], props.filter_name.strip().lower().split(), 1)]

        self.max_page = math.floor(len(assets) / self.item_per_page)
        self.current_page = max(0, self.current_page)
        self.current_page = min(self.max_page, self.current_page)
        start = min(self.current_page * self.item_per_page, len(assets))
        end = min(start + self.item_per_page, len(assets))

        assets_to_show = assets[start:end]
        posx = self.paddingx
        for index, asset in assets_to_show:
            at = AssetThumbnail(index, asset, self.context, self)
            at.width = self.height
            at.height = self.height - 4
            at.position.x = posx
            at.position.y = 2
            posx += self.height + 2
            self.asset_thumbnails.append(at)

        self.width = len(assets_to_show) * (self.height + self.paddingx) + self.paddingx

    def handle_event(self, event) -> bool:
        props = self.context.window_manager.uas_asset_bank
        if self.filter_name != props.filter_name:
            self.filter_name = props.filter_name
            self.current_page = 0
            self.load_page()

        region, _area = get_region_at_xy(self.context, event.mouse_x, event.mouse_y)
        mouse_x = event.mouse_x - region.x
        mouse_y = event.mouse_y - region.y
        if self.is_inside(mouse_x, mouse_y):
            if event.type == "WHEELUPMOUSE":
                self.current_page -= 1
                self.load_page()
                return True
            elif event.type == "WHEELDOWNMOUSE":
                self.current_page += 1
                self.load_page()
                return True

        for at in self.asset_thumbnails:
            if at.handle_event(event):
                return True

        return False

    def draw(self):
        self.height = 150
        draw_square(self.position, self.width, self.height, [0.2, 0.2, 0.2, 0.75])
        for at in self.asset_thumbnails:
            at.draw()

        blf.color(0, 0.99, 0.99, 0.99, 1)
        blf.size(0, 11, 72)
        blf.position(0, self.position.x + self.width * 0.5, self.position.y + self.height + 2, 0)
        blf.draw(0, f"{self.current_page + 1}/{self.max_page + 1}")


class UAS_AssetBank_ViewportBrowser(bpy.types.Operator):
    bl_idname = "uas.asset_bank_viewport_browser"
    bl_label = "Viewport Browser"

    def __init__(self):
        self.asset_browser = None

        self.draw_handle = None
        self.draw_event = None

    def modal(self, context, event):
        region, area = get_region_at_xy(context, event.mouse_x, event.mouse_y)

        if region is None:
            return {"PASS_THROUGH"}
        area.tag_redraw()

        if self.asset_browser.handle_event(event):
            return {"RUNNING_MODAL"}

        if context.window_manager.uas_asset_bank.toggle_overlay is False:
            context.window_manager.event_timer_remove(self.draw_event)
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")
            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        self.asset_browser = AssetBrowser(context)
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw, (context,), "WINDOW", "POST_PIXEL")
        self.draw_event = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        self.asset_browser.draw()


_classes = (UAS_AssetBank_ViewportBrowser,)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
