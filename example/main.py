import itertools
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ecs import *
from pyray import *  # type: ignore


class Shape(Enum):
    RECTANGLE = 0
    CIRCLE = 1


@dataclass
class Position(Component):
    x: float = 0.0
    y: float = 0.0


@dataclass
class Velocity(Component):
    dx: float = 0.0
    dy: float = 0.0
    max_speed: float = 1000.0


@dataclass
class Drawing(Component):
    shape: Shape = Shape.RECTANGLE
    color: Color = Color(*BLACK)
    parameters: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.shape == Shape.RECTANGLE:
            self.parameters.setdefault("width", 100)
            self.parameters.setdefault("height", 100)
        elif self.shape == Shape.CIRCLE:
            self.parameters.setdefault("radius", 50)


@dataclass
class Collision(Component):
    layer: int = 0
    mask: int = 0
    shape: Shape = Shape.RECTANGLE
    parameters: dict = field(default_factory=dict)

    last_collision: Optional[Entity] = None

    def __post_init__(self):
        if self.shape == Shape.RECTANGLE:
            self.parameters.setdefault("width", 100)
            self.parameters.setdefault("height", 100)
        elif self.shape == Shape.CIRCLE:
            self.parameters.setdefault("radius", 50)


WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = Color(*BLACK)
LAYER_BARS = 1
LAYER_BALL = 2

world = Entity(
    "world",
    [],
    [
        Entity(
            "left_bar",
            [
                Position(x=100, y=HEIGHT / 2 - 50),
                Drawing(
                    shape=Shape.RECTANGLE,
                    color=Color(*WHITE),
                    parameters={"width": 10, "height": 100},
                ),
                Collision(
                    layer=LAYER_BARS,
                    mask=LAYER_BALL,
                    shape=Shape.RECTANGLE,
                    parameters={"width": 10, "height": 100},
                ),
            ],
        ),
        Entity(
            "right_bar",
            [
                Position(x=WIDTH - 100, y=HEIGHT / 2 - 50),
                Drawing(
                    shape=Shape.RECTANGLE,
                    color=Color(*WHITE),
                    parameters={"width": 10, "height": 100},
                ),
                Collision(
                    layer=LAYER_BARS,
                    mask=LAYER_BALL,
                    shape=Shape.RECTANGLE,
                    parameters={"width": 10, "height": 100},
                ),
            ],
        ),
        Entity(
            "ball",
            [
                Position(x=WIDTH / 2, y=HEIGHT / 2),
                Velocity(dx=100, dy=0),
                Drawing(
                    shape=Shape.RECTANGLE,
                    color=Color(*WHITE),
                    parameters={"width": 10, "height": 10},
                ),
                Collision(
                    layer=LAYER_BALL,
                    mask=LAYER_BARS,
                    shape=Shape.RECTANGLE,
                    parameters={"width": 10, "height": 10},
                ),
            ],
        ),
    ],
)

query = Query(world)


def move_ball(query: Query, delta: float):
    if ball := query.get(
        [HasId("ball"), HasComponent(Position), HasComponent(Velocity)]
    ):
        vel = ball.get(Velocity)
        pos = ball.get(Position)

        # check for collisions
        if collision := ball.get(Collision):
            if collision.last_collision:
                vel.dx *= -1
                collision.last_collision = None

                # add speed
                vel.dx *= 1.2
                vel.dy *= 1.2

        new_vel = Vector2(vel.dx, vel.dy)

        # limit velocity
        new_vel = vector2_clamp_value(new_vel, 0, vel.max_speed)

        # update position
        vel.dx = new_vel.x
        vel.dy = new_vel.y

        pos.x += vel.dx * delta
        pos.y += vel.dy * delta


def check_collisions(query: Query):
    entity_list = query.filter([HasComponent(Position), HasComponent(Collision)])
    for A, B in itertools.combinations(entity_list, 2):
        a_coll = A.get(Collision)
        b_coll = B.get(Collision)
        a_pos = A.get(Position)
        b_pos = B.get(Position)

        if a_coll.mask == b_coll.layer or a_coll.layer == b_coll.mask:
            a_rec = Rectangle(
                round(a_pos.x),
                round(a_pos.y),
                a_coll.parameters["width"],
                a_coll.parameters["height"],
            )
            b_rec = Rectangle(
                round(b_pos.x),
                round(b_pos.y),
                b_coll.parameters["width"],
                b_coll.parameters["height"],
            )

            if check_collision_recs(a_rec, b_rec):
                a_coll.last_collision = B
                b_coll.last_collision = A


def draw(query: Query):
    for entity in query.filter([HasComponent(Position), HasComponent(Drawing)]):
        pos = entity.get(Position)
        draw = entity.get(Drawing)

        if draw.shape == Shape.RECTANGLE:
            draw_rectangle(
                round(pos.x),
                round(pos.y),
                draw.parameters["width"],
                draw.parameters["height"],
                draw.color,
            )
        elif draw.shape == Shape.CIRCLE:
            draw_circle(
                round(pos.x), round(pos.y), draw.parameters["radius"], draw.color
            )


################################################################################


init_window(WIDTH, HEIGHT, "pong example")
set_target_fps(60)


while not window_should_close():
    # update
    delta = get_frame_time()
    move_ball(query, delta)
    check_collisions(query)

    # render
    begin_drawing()
    clear_background(BACKGROUND_COLOR)
    draw(query)
    end_drawing()

close_window()
