bl_info = {
    "name": "Orbiter",
    "author": "lazybones",
    "version": (1, 5),
    "blender": (3, 0, 0),
    "location": "3D View",
    "description": "Automatically orbits the viewport if you stop doing anything",
    "category": "3D View",
}

import bpy
import time
import mathutils
import aud
import os
from bpy.app.handlers import persistent

IDLE_TIME = 60.0
ORBIT_SPEED = 0.01

last_activity = time.time()
orbiting = False

initial_rotation = None
initial_location = None

audio_device = aud.Device()
audio_handle = None

class OrbiterPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    enable_music: bpy.props.BoolProperty(
        name="Enable Music",
        default=True
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "enable_music")

global audio_sound
audio_sound = None
audio_path = os.path.join(os.path.dirname(__file__), "fly_me_to_the_moon.ogg")
# https://www.youtube.com/watch?v=DtL_giO-EB8

if os.path.exists(audio_path):
    audio_sound = aud.Sound(audio_path)
    print("Audio loaded:", audio_path)
else:
    print("Audio file NOT found:", audio_path)

def orbit_timer():
    global last_activity, orbiting
    global initial_rotation, initial_location
    global audio_handle

    now = time.time()
    idle = now - last_activity

    area = None
    region_3d = None

    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for a in screen.areas:
            if a.type == 'VIEW_3D':
                area = a
                region_3d = a.spaces.active.region_3d
                break
        if area:
            break

    if not region_3d:
        return 0.02

    addon = bpy.context.preferences.addons.get(__name__)
    prefs = addon.preferences if addon else None
    

    if idle > IDLE_TIME:

        if not orbiting:
            print("Starting orbit")
            orbiting = True

            initial_rotation = region_3d.view_rotation.copy()
            initial_location = region_3d.view_location.copy()

            bpy.context.window_manager.popup_menu(
                lambda self, ctx: self.layout.label(
                    text="No activity detected. Orbiting viewport."
                ),
                title="Orbit Mode",
                icon='INFO'
            )

            # Play music if enabled
            if prefs and prefs.enable_music and audio_sound:
                audio_handle = audio_device.play(audio_sound)
                audio_handle.loop_count = -1

        rot = mathutils.Matrix.Rotation(ORBIT_SPEED, 3, 'Z')

        region_3d.view_location = rot @ region_3d.view_location

        region_3d.view_rotation = (
            mathutils.Quaternion((0, 0, 1), ORBIT_SPEED)
            @ region_3d.view_rotation
        )

    return 0.02

class IdleTracker(bpy.types.Operator):
    """Tracks mouse activity"""
    bl_idname = "wm.idle_tracker"
    bl_label = "Idle Tracker"

    _timer = None

    def modal(self, context, event):
        global last_activity, orbiting
        global initial_rotation, initial_location
        global audio_handle

        if event.type == 'MOUSEMOVE' and event.value == 'NOTHING':
            last_activity = time.time()

            if orbiting:

                area = next((a for a in context.screen.areas if a.type == 'VIEW_3D'), None)

                if area:
                    region_3d = area.spaces.active.region_3d

                    if initial_rotation:
                        region_3d.view_rotation = initial_rotation

                    if initial_location:
                        region_3d.view_location = initial_location

                orbiting = False
                initial_rotation = None
                initial_location = None

                # Stop music
                if audio_handle:
                    audio_handle.stop()
                    audio_handle = None

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

def start_tracker():
    print("Starting idle tracker")
    try:
        bpy.ops.wm.idle_tracker('INVOKE_DEFAULT')
    except Exception as e:
        print("IdleTracker failed:", e)
    return None

@persistent
def reset_on_file_load(dummy):
    global last_activity, orbiting
    global initial_rotation, initial_location
    global audio_handle

    print("Blend file loaded, restarting Orbiter")

    last_activity = time.time()
    orbiting = False
    initial_rotation = None
    initial_location = None

    if audio_handle:
        audio_handle.stop()
        audio_handle = None

    # restart the idle tracker operator
    bpy.app.timers.register(start_tracker, first_interval=1.0)

def register():
    bpy.utils.register_class(IdleTracker)
    bpy.utils.register_class(OrbiterPreferences)

    bpy.app.timers.register(orbit_timer)
    bpy.app.timers.register(start_tracker, first_interval=1.0)

    bpy.app.handlers.load_post.append(reset_on_file_load)

def unregister():
    bpy.utils.unregister_class(IdleTracker)
    bpy.utils.unregister_class(OrbiterPreferences)

    if reset_on_file_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(reset_on_file_load)


if __name__ == "__main__":
    register()
