import pyglet
import math
import time
import vec2

INJECTOR = 0
EXTRACTOR = 1
MULTIPLEXER = 2

NONE = 0
INPUT_CONNECTOR = 1
OUTPUT_CONNECTOR = 2
SPECIAL_CONNECTOR = 3
ALL = 4

DRAG_END = 1
DRAG_BEGINNING = 2

directions = [
        [ (-92, 0), (92, 0), (32, 64) ],
        [ (-92, 0), (92, 0), (-32, -64) ],
        [ None ]
        ]

sides = [
        [ DRAG_BEGINNING, DRAG_END, DRAG_BEGINNING ],
        [ DRAG_BEGINNING, DRAG_END, DRAG_END ],
        [ None ]
        ]

window = pyglet.window.Window(640, 400)

i = 0

points = [ (1.0, 0.0), (2.0, 0.0), (3.0, 0.0), (4.0, 0.0) ]

class Entity:

    def __init__(self, kind, x, y):

        self.kind = kind
        if kind == INJECTOR:
            image = pyglet.image.load("injector.png")
            x -= image.width/2
            y -= image.height/2
            self.attach_points = [(1+x, 19+y), (52+x, 19+y), (42+x, 46+y)]
        elif kind == EXTRACTOR:
            image = pyglet.image.load("extractor.png")
            x -= image.width/2
            y -= image.width/2
            self.attach_points = [(1+x, 28+y), (52+x, 28+y), (12+x, 1+y)]
        elif kind == MULTIPLEXER:
            image = pyglet.image.load("multiplexer.png")
        self.sprite = pyglet.sprite.Sprite(image, x, y)
        self.x = x
        self.y = y
        self.width = image.width
        self.height = image.height
        self.hover = 0
        self.connections = [None, None, None]
        self.drag_offset = (0, 0)
        
        self.mouse_update(x, y)

    def mouse_update(self, mouse_x, mouse_y):

        if mouse_x > self.x-5 and mouse_x < self.x+self.width+5 and mouse_y > self.y-5 and mouse_y < self.y+self.height+5:
            for i in range(len(self.attach_points)):
                point = self.attach_points[i]
                d = vec2.abs(vec2.sub([mouse_x, mouse_y], point))
                if vec2.abs(vec2.sub([mouse_x, mouse_y], point)) <= 6:
                    self.hover = i+1
                    return
            self.hover = ALL
        else:
            self.hover = NONE

    def mouse_drag(self, mouse_x, mouse_y):

        global entities, drag_entity

        if drag_entity == self:
            dx = mouse_x - self.x - self.drag_offset[0]
            dy = mouse_y - self.y - self.drag_offset[1]
            self.x = self.sprite.x = mouse_x - self.drag_offset[0]
            self.y = self.sprite.y = mouse_y - self.drag_offset[1]
            self.attach_points = [ vec2.add( (dx, dy), point ) for point in self.attach_points ]
            self.hover = NONE

            for i in range(3):
                connection = self.connections[i]
                if connection:
                    connection.update_endpoint(self, self.attach_points[i])

            if mouse_x < 0 or mouse_x > window.width or mouse_y < 0 or mouse_y > window.height:
                for connection in self.connections:
                    if connection:
                        connection.remove()

                entities.remove(self)
                drag_entity = None
                del(self)

    def mouse_press(self, mouse_x, mouse_y):

        global drag_connection, drag_entity

        if self.hover > NONE and self.hover < ALL:

            if drag_connection == None:
                if self.connections[self.hover-1] == None:
                    direction = directions[self.kind][self.hover-1]
                    drag_connection = self.connections[self.hover-1] = Connection(self.attach_points[self.hover-1], direction, self, sides[self.kind][self.hover-1] )
                else:
                    self.connections[self.hover-1].begin_drag(self)
                drag_connection.mouse_update(mouse_x, mouse_y)

            else:
                if drag_connection.in_entity != self and drag_connection.out_entity != self:

                    previous_connection = self.connections[self.hover-1]

                    self.connections[self.hover-1] = drag_connection
                    drag_connection.end_drag(self.attach_points[self.hover-1], directions[self.kind][self.hover-1], self)

                    if previous_connection:
                        previous_connection.begin_drag(self)
                        previous_connection.mouse_update(mouse_x, mouse_y)

        elif self.hover == ALL:
            if drag_entity == None and drag_connection == None:
                drag_entity = self
                self.drag_offset = (mouse_x-self.x, mouse_y-self.y)

    def mouse_release(self, mouse_x, mouse_y):

        global drag_connection, drag_entity

        if drag_entity == self:
            drag_entity = None

    def draw(self):

        self.sprite.draw()
        if self.hover > 0 and self.hover < ALL:
            draw_circle(self.attach_points[self.hover-1], 6)
        for connection in self.connections:
            if connection:
                connection.draw()


class Connection:

    def __init__(self, start, direction, begin_entity, side=DRAG_END):

        global drag_connection

        self.p0 = start
        self.p1 = direction
        self.p2 = self.p3 = vec2.add([1, 1], start)
        self.in_entity = None
        self.out_entity = None

        self.drag = side
        if side == DRAG_END:
            self.p0 = start
            self.p1 = vec2.add(start, direction)
            self.p2 = self.p3 = start
            self.in_entity = begin_entity
            drag_connection = self
        elif side == DRAG_BEGINNING:
            self.p3 = start
            self.p2 = vec2.add(start, direction)
            self.p0 = self.p1 = start
            self.out_entity = begin_entity
            drag_connection = self

    def remove(self):

        if self.in_entity:
            self.remove_from_entity(self.in_entity)
        if self.out_entity:
            self.remove_from_entity(self.out_entity)

    def remove_from_entity(self, entity):

        if entity.connections[0] == self:
            entity.connections[0] = None
        elif entity.connections[1] == self:
            entity.connections[1] = None
        elif entity.connections[2] == self:
            entity.connections[2] = None

    def mouse_update(self, mouse_x, mouse_y):

        if self.drag == DRAG_END:
            self.p2 = self.p3 = (mouse_x, mouse_y)
        elif self.drag == DRAG_BEGINNING:
            self.p0 = self.p1 = (mouse_x, mouse_y)

    def begin_drag(self, entity):

        global drag_connection

        if entity == self.in_entity:
            self.remove_from_entity(self.in_entity)
            self.in_entity = None
            self.drag = DRAG_BEGINNING
            drag_connection = self
        elif entity == self.out_entity:
            self.remove_from_entity(self.out_entity)
            self.out_entity = None
            self.drag = DRAG_END
            drag_connection = self

    def end_drag(self, end, direction, end_entity):

        global drag_connection

        if self.drag == DRAG_END:
            self.p2 = vec2.add(end, direction)
            self.p3 = end
            self.out_entity = end_entity

        elif self.drag == DRAG_BEGINNING:
            self.p1 = vec2.add(end, direction)
            self.p0 = end
            self.in_entity = end_entity

        self.drag = NONE
        drag_connection = None

    def update_endpoint(self, entity, new_endpoint):

        if entity == self.in_entity:
            diff = vec2.sub(new_endpoint, self.p0)
            self.p0 = new_endpoint
            self.p1 = vec2.add(diff, self.p1)

        if entity == self.out_entity:
            diff = vec2.sub(new_endpoint, self.p3)
            self.p3 = new_endpoint
            self.p2 = vec2.add(diff, self.p2)

    def draw(self):

        draw_thick_cubic_bezier([self.p0, self.p1, self.p2, self.p3], 3)

def draw_circle(center, radius):

    nr_segs = 12
    angle_step = 2*math.pi/nr_segs
    points = [center[0], center[1]]
    angle = 0
    for i in range(nr_segs):
        px = int(radius*math.sin(angle)+center[0])
        py = int(radius*math.cos(angle)+center[1])
        points.extend([px, py])
        angle += angle_step

    indices = []
    for i in range(1,nr_segs):
        indices.extend([i, i+1, 0])
    indices.extend([nr_segs, 1, 0])

    pyglet.graphics.draw_indexed(nr_segs+1, pyglet.gl.GL_TRIANGLES, indices,
            ('v2i', tuple(points)),
            ('c4f', (1.0,)*(nr_segs+1)*4)
            )

def draw_cubic_bezier(points):

    t = 0.0
    sx, sy = points[3]
    while t <= 0.9:
        t += 0.1
        ex = points[0][0]*t*t*t+3*points[1][0]*t*t*(1-t)+3*points[2][0]*t*(1-t)*(1-t)+points[3][0]*(1-t)*(1-t)*(1-t)
        ey = points[0][1]*t*t*t+3*points[1][1]*t*t*(1-t)+3*points[2][1]*t*(1-t)*(1-t)+points[3][1]*(1-t)*(1-t)*(1-t)
        #print sx, sy, ex, ey, t, points[0]
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                ('v2i', (int(sx), int(sy), int(ex), int(ey))),
                ('c4f', (1.0,)*8)
                )
        sx = ex
        sy = ey

def draw_thick_cubic_bezier(points, width):

    t = 0.0
    curve_points = []
    while t <= 1.0:
        x = points[0][0]*t*t*t+3*points[1][0]*t*t*(1-t)+3*points[2][0]*t*(1-t)*(1-t)+points[3][0]*(1-t)*(1-t)*(1-t)
        y = points[0][1]*t*t*t+3*points[1][1]*t*t*(1-t)+3*points[2][1]*t*(1-t)*(1-t)+points[3][1]*(1-t)*(1-t)*(1-t)
        curve_points.append((x, y))
        t += 0.01

    outer_points = []
    inner_points = []
    ortho_vector = vec2.norm(vec2.sub(curve_points[1],curve_points[0]))#TODO: What happens when two points are in the same spot?
    ortho_vector[0], ortho_vector[1] = -1*ortho_vector[1], ortho_vector[0]
    ortho_vector = vec2.mul(ortho_vector, width)
    inner_points.append(vec2.sub(curve_points[0], ortho_vector))
    outer_points.append(vec2.add(curve_points[0], ortho_vector))

    for i in range(1, len(curve_points)-1):
        ortho_vector = vec2.norm(vec2.sub(curve_points[i+1], curve_points[i-1]))
        ortho_vector[0], ortho_vector[1] = -1*ortho_vector[1], ortho_vector[0]
        ortho_vector = vec2.mul(ortho_vector, width)
        inner_points.append(vec2.sub(curve_points[i], ortho_vector))
        outer_points.append(vec2.add(curve_points[i], ortho_vector))

    ortho_vector = vec2.norm(vec2.sub(curve_points[-1], curve_points[-2]))
    ortho_vector[0], ortho_vector[1] = -1*ortho_vector[1], ortho_vector[0]
    ortho_vector = vec2.mul(ortho_vector, width)
    inner_points.append(vec2.sub(curve_points[-1], ortho_vector))
    outer_points.append(vec2.add(curve_points[-1], ortho_vector))

    all_points = []
    for point in inner_points:
        all_points.extend(point)
    for point in outer_points:
        all_points.extend(point)
    all_points = [int(p) for p in all_points]
    all_points = tuple(all_points)

    indices = []
    l = len(inner_points)
    for i in range(l-1):
        indices.append(i)
        indices.append(i+1)
        indices.append(i+l)

        indices.append(i+1)
        indices.append(i+1+l)
        indices.append(i+l)

    pyglet.graphics.draw_indexed(len(all_points)/2, pyglet.gl.GL_TRIANGLES, indices,#TODO: Triangularize!
            ('v2i', all_points),
            ('c4f', (1.0,)*len(all_points)*2)
            )

test = Entity(INJECTOR, 50, 50)
test2 = Entity(INJECTOR, 100, 100)
entities = [test, test2]
drag_connection = None
drag_entity = None

add_dialog = pyglet.text.Label(text="", font_name="Courier", anchor_x="center", anchor_y="center", x=window.width/2, y=window.height/2)
add_dialog.set_style("background_color", (0, 0, 0, 255))
add_dialog_active = False
add_dialog_start = 0

@window.event
def on_draw():

    window.clear()
    for entity in entities:
        entity.draw()

    if add_dialog_active == True:
        add_dialog.draw()

@window.event
def on_mouse_motion(x, y, dx, dy):

    for entity in entities:
        entity.mouse_update(x, y)

    if drag_connection:
        drag_connection.mouse_update(x, y)

@window.event
def on_mouse_press(x, y, button, modifiers):

    global drag_connection, add_dialog_active, add_dialog_start

    if button == pyglet.window.mouse.LEFT:
        for entity in entities:
            entity.mouse_press(x, y)

    elif button == pyglet.window.mouse.RIGHT:
        if drag_connection:
            drag_connection.remove()
            drag_connection = None
        else:
            add_dialog.text = "INJECTOR"
            add_dialog_active = True
            add_dialog_start = (x, y)

@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):

    for entity in entities:
        entity.mouse_drag(x, y)

    if add_dialog_active == True:
        d = add_dialog_start[1] - y
        if d < 10:
            add_dialog.text = "INJECTOR"
        elif d < 30:
            add_dialog.text = "EXTRACTOR"
        elif d < 50:
            add_dialog.text = "MULTIPLEXOR"
        else:
            add_dialog.text = ""


@window.event
def on_mouse_release(x, y, button, modifiers):

    global add_dialog_active

    if button == pyglet.window.mouse.LEFT:
        for entity in entities:
            entity.mouse_release(x, y)
    
    elif button == pyglet.window.mouse.RIGHT and add_dialog_active == True:
        if add_dialog.text == "INJECTOR":
            entities.append(Entity(INJECTOR, add_dialog_start[0], add_dialog_start[1]))
        elif add_dialog.text == "EXTRACTOR":
            entities.append(Entity(EXTRACTOR, add_dialog_start[0], add_dialog_start[1]))
        add_dialog_active = False
        add_dialog_text = ""

pyglet.app.run()
