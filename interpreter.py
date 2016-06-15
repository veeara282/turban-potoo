import mdl
from display import *
from matrix import *
from matrix import matrix_mult as mmult
from draw import *
from shapes import *
from stack import Stack
from animate import *
from shading import Light

from json import dumps as jsonfmt

from math import *

def run(filename, frame=-1):
    """
    This function runs an mdl script
    """
    p = mdl.parseFile(filename)

    if p:
        commands, symbols = p

        light = Light()
        light.set_constant('ambient', RED, 1)
        light.set_constant('ambient', GREEN, 1)
        light.set_constant('ambient', BLUE, 1)
        light.set_constant('diffuse', RED, 1)
        light.set_constant('diffuse', GREEN, 1)
        light.set_constant('diffuse', BLUE, 1)
        light.set_constant('specular', RED, 1)
        light.set_constant('specular', GREEN, 1)
        light.set_constant('specular', BLUE, 1)
        light.normalize_constants()

        light.set_ambient_light([64, 64, 64])
        light.add_light([-500, 500, 500], [255, 255, 255])

        if is_animated(commands):
            frames = num_frames(commands)

            #print symbols

            # Set knob values for each frame
            knobs = make_knobs(commands, frames)

            #print jsonfmt(knobs, sort_keys=True, indent=4)

            basename = get_basename(commands)
            # Construct format string using format string
            fmt_string = "%s-%%0%dd.gif" % (basename, int(1 + max(log10(frames), 0)) )
            #print fmt_string

            screen = new_screen()

            if frame < 0:
                for i in range(frames):
                    print "Drawing frame %d of %d ..." % (i, frames - 1)
                    draw_frame(commands, symbols, screen, knobs, light=light, frame=i)
                    save_extension(screen, fmt_string % (i))

                print '''


Done making your animation.

To show it, run the following ImageMagick terminal commands:

$ convert %s-*.gif %s.gif && animate -loop 0 %s.gif

                        - or -

$ animate -loop 0 %s-*.gif

Have a nice day!
                    ''' % (basename, basename, basename, basename)
            else:
                print "Drawing frame %d of %d ..." % (frame, frames - 1)
                draw_frame(commands, symbols, screen, knobs, light=light, frame=frame)
                save_extension(screen, fmt_string % (frame))
        else:
            draw_frame(commands, symbols, light=light)
    else:
        print "Parsing failed."
        return


# Draw ONE frame
def draw_frame(commands, symbols, screen = None, knobs = None, frame = 0, light = None, verbose = False):
    # Setup drawing environment *after* the error checking to prevent prematurely allocating too much memory
    color = [255, 255, 255]
    stack = Stack()

    if screen:
        clear_screen(screen)
    else:
        screen = new_screen()

    env = (color, stack, screen, symbols, knobs, frame, light)
    #print [type(o) for o in env]

    # Pick a function to execute from the dict(string, function)
    x_map = {
        # 2-D drawing routines
        "line": line,
        "circle": circle,
        "hermite": hermite,
        "bezier": bezier,
        # 3-D drawing routines
        "box": box,
        "sphere": sphere,
        "torus": torus,
        # Matrix stack operations
        "push": push,
        "pop": pop,
        # Transformations
        "move": move,
        "scale": scale,
        "rotate": rotate,
        # Display and save
        "display": display_img,
        "save": save_img
    }

    for command in commands:
        if verbose:
            print command
        cmd = command[0]
        if cmd in x_map:
            x_map[cmd](command, env)

    return screen

# Functions for executing commands

# 2-D drawing routines

def line(args, env):
    # Semantic analyzer
    x0, y0, z0, x1, y1, z1 = args[1:]
    color, stack, screen, symbols, knobs, frame = env

    # Immediately draw line to screen
    edges = []
    add_edge(edges, x0, y0, z0, x1, y1, z1)
    mmult(stack.peek(), edges)
    draw_lines(edges, screen, color)

def circle(args, env):
    # Semantic analyzer
    pass

def hermite(args, env):
    pass

def bezier(args, env):
    pass

# 3-D drawing routines

def box(args, env):
    x, y, z, width, height, depth = args[1:]
    color, stack, screen, symbols, knobs, frame, light = env

    polygons = []
    add_box(polygons, x, y, z, width, height, depth)
    mmult(stack.peek(), polygons)
    draw_polygons(polygons, screen, color, light)

def sphere(args, env):
    x, y, z, r, coord_system = args[1:]

    color, stack, screen, symbols, knobs, frame, light = env
    step = int(round(2 * sqrt(r)))

    polygons = []
    add_sphere(polygons, x, y, z, r, step)
    mmult(stack.peek() if coord_system is None else coord_system, polygons)

    draw_polygons(polygons, screen, color, light)

def torus(args, env):
    x, y, z, r, R, coord_system = args[1:]
    color, stack, screen, symbols, knobs, frame, light = env
    step = int(round(4 * sqrt(r)))

    polygons = []
    add_torus(polygons, x, y, z, r, R, step)
    mmult(stack.peek() if coord_system is None else coord_system, polygons)
    draw_polygons(polygons, screen, color, light)


# Matrix stack operations

def push(args, env):
    color, stack, screen, symbols, knobs, frame, light = env

    stack.push()

def pop(args, env):
    color, stack, screen, symbols, knobs, frame, light = env

    stack.pop()

# Transformations

def move(args, env):
    x, y, z, knob = args[1:]
    color, stack, screen, symbols, knobs, frame, light = env

    c = knobs[knob][frame] if knobs and knob else 1

    u = make_translate(x*c, y*c, z*c)
    stack.mult(u)

def scale(args, env):
    x, y, z, knob = args[1:]
    #print "knob", type(knob)

    color, stack, screen, symbols, knobs, frame, light = env

    #print "knobs", type(knobs)
    #print jsonfmt(knobs, indent=4)
    #print knobs['bigenator']
    #print frame, type(frame)

    knob_content = knobs[knob] if knobs and knob else None
    c = knob_content[frame] if knob_content else 1

    u = make_scale(x*c, y*c, z*c)
    stack.mult(u)

def rotate(args, env):
    axis, degrees, knob = args[1:]
    color, stack, screen, symbols, knobs, frame, light = env

    rot = {
        "x": make_rotX,
        "y": make_rotY,
        "z": make_rotZ
    }

    c = knobs[knob][frame] if knobs and knob else 1

    u = rot[axis](radians(degrees)*c)
    stack.mult(u)

# Display and save

def display_img(args, env):
    color, stack, screen, symbols, knobs, frame, light = env
    display(screen)

def save_img(args, env):
    filename = args[1]
    color, stack, screen, symbols, knobs, frame, light = env

    if filename is not None:
        if filename[-4:].lower() == ".ppm":
            save_ppm(screen, filename)
        else:
            save_extension(screen, filename)
