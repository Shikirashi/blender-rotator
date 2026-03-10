bl_info = {
    "name": "Orbiter",
    "author": "lazybones",
    "version": (1, 3),
    "blender": (3, 0, 0),
    "location": "3D View",
    "description": "Automatically orbits the viewport if you stop doing anything",
    "category": "3D View",
}

import bpy
import time
import mathutils

IDLE_TIME = 60.0
ORBIT_SPEED = 0.01

last_activity = time.time()
orbiting = False

initial_rotation = None
initial_location = None


def orbit_timer():
    global last_activity, orbiting
    global initial_rotation, initial_location

    context = bpy.context
    idle = time.time() - last_activity

    area = next((a for a in context.screen.areas if a.type == 'VIEW_3D'), None)
    if not area:
        return 0.02

    region_3d = area.spaces.active.region_3d

    # START ORBIT AFTER IDLE TIME
    if idle > IDLE_TIME:

        if not orbiting:
            orbiting = True

            # save starting view
            initial_rotation = region_3d.view_rotation.copy()
            initial_location = region_3d.view_location.copy()

            bpy.context.window_manager.popup_menu(
                lambda self, ctx: self.layout.label(
                    text="No activity detected. Orbiting viewport."
                ),
                title="Orbit Mode",
                icon='INFO'
            )

        # ORBIT MOTION
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

        if event.type == 'MOUSEMOVE':

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

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def start_tracker():
    bpy.ops.wm.idle_tracker()
    return None


def register():
    bpy.utils.register_class(IdleTracker)
    bpy.app.timers.register(orbit_timer)
    bpy.app.timers.register(start_tracker, first_interval=1.0)


def unregister():
    bpy.utils.unregister_class(IdleTracker)


if __name__ == "__main__":
    register()