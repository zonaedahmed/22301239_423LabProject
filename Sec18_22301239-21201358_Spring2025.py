from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# Game state variables
game_over = False
player_dead = False
player_life = 200  # Set initial life to 200 everywhere
game_score = 0
bullets_missed = 0

# Game timer for reaching the finish line
GAME_TIME_LIMIT = 70  # seconds to reach the finish line
game_start_time = None
time_up = False

# Guards shooting time variable
guards_shot_time = None

# Guard firing state: list of dicts with position and next_fire_time
guard_states = []

# Camera-related variables
camera_pos = (0, 500, 500)
camera_angle = 90  # Camera looks along +Y (same as player)
camera_height = 900
camera_mode = "third_person"  # "first_person" or "third_person"
fovY = 120  # Field of view
camera_follow_player = True  # Start with camera following the player

# Player-related variables
player_pos = [0.0, 0.0, 0.0]  # x, y, z coordinates as floats
player_angle = 180  # Face toward +Y axis at start
player_speed = 3  # Slow initial speed for player
rotation_speed = 5  # Rotation speed in degrees
player_decision_made = False
player_moving = False
player_dead = False
player_red_light_move_time = None

# Gun-related variables
gun_height = 50  # Height of the gun from the ground

# Bullet-related variables
BULLET_SIZE = 4  # Even smaller bullets
bullet_size = BULLET_SIZE
bullet_speed = 32  # Even faster bullets
bullets = []  # List to store active bullets

# Field size variables (replace GRID_LENGTH)
FIELD_LENGTH_X = 800  # Increased from 600 to 800 for a wider field
FIELD_LENGTH_Y = 1200  # Make Y much longer

FIELD_HEIGHT = 180  # Increased from 100 to 180 for higher walls

# Random variable for demonstration
rand_var = 423

# Player and enemy shared constants
CHARACTER_HEIGHT = 55  # Standard height for both player and enemies

# Runner-related variables
runner_count = 40  # Increase number of runners
runners = []

# Phase-related variables
phase = "green"  # "green" or "red"
phase_timer = 0
phase_duration = 2  # seconds for each phase, can randomize
last_phase_switch = time.time()

FINISH_LINE_Y = FIELD_LENGTH_Y - 200  # Adjust as needed

# Doll-related variables
doll_angle = 0
doll_rotating = True
doll_looking = False
doll_last_switch = time.time()
doll_rotate_interval = 3.0  # seconds between rotations
doll_rotate_duration = 2.0  # seconds spent rotating
doll_look_duration = 3  # seconds facing players
doll_back_duration = 3  # seconds facing backward
doll_facing_forward = True  # Start by rotating from 0 to 180 (toward players)

# Animation-related variable
animation_time = 0

# Countdown before game starts
COUNTDOWN_TIME = 3  # seconds
countdown_start_time = None
countdown_active = True

# --- Brighter skin color for doll, player, runners, guards ---
SKIN_COLOR = (1.0, 0.95, 0.85)  # Brighter, less yellowish

# Add near your global variables
elimination_messages = []  # List of (number, time_of_elimination)

paused = False

# Initialize runners at the start of the game
def init_runners():
    global runners
    runners = []
    spacing = 40  # Reduce spacing for more runners
    start_y = -FIELD_LENGTH_Y + 120  # Define start_y for runner placement
    for i in range(runner_count):
        x = (i - (runner_count - 1) / 2) * spacing
        y_offset = random.uniform(-30, 30)
        y = start_y + y_offset
        y = max(-FIELD_LENGTH_Y + 60, min(y, -FIELD_LENGTH_Y + 140))
        speed = random.uniform(0.5, 1.0)  # Faster, random speed
        number = random.randint(10, 99)   # 2-digit random number
        runners.append({
            "pos": [x, y, 0],
            "angle": 0,
            "alive": True,
            "speed": speed,
            "moving": False,
            "decision_made": False,
            "move_timer": random.randint(8, 20),
            "number": number
        })

# Initialize guard states at the start of the game
def init_guard_states():
    global guard_states
    guard_states = []
    guard_positions = []
    # Same positions as in draw_wall_guards
    for i in range(-2, 3):
        guard_positions.append([i * 200, FIELD_LENGTH_Y, FIELD_HEIGHT])
        guard_positions.append([i * 200, -FIELD_LENGTH_Y, FIELD_HEIGHT])
    for i in range(-3, 4):
        guard_positions.append([-FIELD_LENGTH_X, i * 300, FIELD_HEIGHT])
        guard_positions.append([FIELD_LENGTH_X, i * 300, FIELD_HEIGHT])

    now = time.time()
    for pos in guard_positions:
        guard_states.append({
            "pos": pos,
            "next_fire_time": now + random.uniform(0, 0.7)  # random delay up to 0.7s
        })

# Fire a bullet from the player's gun
def fire_bullet():
    global bullets, bullets_missed
    if game_over:
        return
    
    # Calculate bullet starting position based on gun position and angle
    gun_length = 100  # Length of the gun barrel
    bullet_x = player_pos[0] + gun_length * math.cos(math.radians(player_angle))
    bullet_y = player_pos[1] + gun_length * math.sin(math.radians(player_angle))
    bullet_z = player_pos[2] + gun_height  # Bullet starts at gun height
    
    # Add bullet to the list with its direction
    bullets.append({
        "pos": [bullet_x, bullet_y, bullet_z],
        "angle": player_angle,
        "distance": 0  # Track distance to limit bullet range
    })

# Draw text on screen (from template)
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1, 1, 1)):
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, 1000, 0, 800)  # left, right, bottom, top
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# Draw the player's character (no gun, no cheat mode)
def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    if player_dead or (game_over and player_life <= 0):
        glRotatef(90, 1, 0, 0)  # Fall flat
        glScalef(0.6, 0.6, 0.6)
    else:
        glRotatef(player_angle - 90, 0, 0, 1)  # <-- Fix: face same way as runners

    # Head (Sphere)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(0, 0, CHARACTER_HEIGHT+5)
    gluSphere(gluNewQuadric(), 10, 20, 20)
    glPopMatrix()

    # Hair (brown cap)
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glTranslatef(0, 0, CHARACTER_HEIGHT + 12)
    glScalef(1.1, 1.1, 0.5)
    gluSphere(gluNewQuadric(), 10, 20, 20)
    glPopMatrix()

    # Body (Cuboid)
    glColor3f(0.1, 0.6, 0.1)  # Darker green dress
    glPushMatrix()
    glTranslatef(0, 0, CHARACTER_HEIGHT / 2)
    glScalef(20, -18, CHARACTER_HEIGHT-20)
    glutSolidCube(1)
    glPopMatrix()

    # Limb swing animation (same as runner)
    swing = math.sin(animation_time * 7) * 25 if player_moving and not player_dead and not game_over else 0

    # Left Arm
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(-18, 0, CHARACTER_HEIGHT - 25)
    glRotatef(-swing, 1, 0, 0)
    glScalef(4, 4, 20)
    glutSolidCube(1)
    glPopMatrix()

    # Right Arm
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(18, 0, CHARACTER_HEIGHT - 25)
    glRotatef(swing, 1, 0, 0)
    glScalef(4, 4, 20)
    glutSolidCube(1)
    glPopMatrix()

    # Left Leg
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    if not player_dead and not (game_over and player_life <= 0):
        glTranslatef(-4, 0, -15)
        glRotatef(-swing, 1, 0, 0)
        glScalef(4, 4, 70)
    else:
        glTranslatef(-4, 0, -8)
        glScalef(4, 4, 35)
    glutSolidCube(1)
    glPopMatrix()

    # Right Leg
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    if not player_dead and not (game_over and player_life <= 0):
        glTranslatef(4, 0, -15)
        glRotatef(swing, 1, 0, 0)
        glScalef(4, 4, 70)
    else:
        glTranslatef(4, 0, -8)
        glScalef(4, 4, 35)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()

# Draw a runner (reuse player shape, but different color)
def draw_runner(runner):
    glPushMatrix()
    glTranslatef(runner["pos"][0], runner["pos"][1], runner["pos"][2])
    if not runner["alive"]:
        glRotatef(90, 1, 0, 0)  # Fall flat if dead
        glScalef(0.6, 0.6, 0.6)  # Make dead runner smaller
    else:
        glRotatef(runner["angle"], 0, 0, 1)

    # Head (Sphere)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(0, 0, CHARACTER_HEIGHT+5)
    gluSphere(gluNewQuadric(), 10, 20, 20)
    glPopMatrix()

    # Hair (brown cap)
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glTranslatef(0, 0, CHARACTER_HEIGHT + 12)
    glScalef(1.1, 1.1, 0.5)
    gluSphere(gluNewQuadric(), 10, 20, 20)
    glPopMatrix()

    # Body (Cuboid)
    glColor3f(0.1, 0.6, 0.1)  # Darker green dress
    glPushMatrix()
    glTranslatef(0, 0, CHARACTER_HEIGHT / 2)
    glScalef(20, -18, CHARACTER_HEIGHT-20)
    glutSolidCube(1)
    glPopMatrix()

    # Limb swing animation
    swing = math.sin(animation_time * 7) * 25 if runner["moving"] else 0

    # Left Arm (down, swings forward/back like leg)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(-18, 0, CHARACTER_HEIGHT - 25)
    glRotatef(-swing, 1, 0, 0)
    glScalef(4, 4, 20)
    glutSolidCube(1)
    glPopMatrix()

    # Right Arm (down, swings forward/back like leg)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(18, 0, CHARACTER_HEIGHT - 25)
    glRotatef(swing, 1, 0, 0)
    glScalef(4, 4, 20)
    glutSolidCube(1)
    glPopMatrix()

    # Left Leg (Cuboid, with swing)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    if runner["alive"]:
        glTranslatef(-4, 0, -15)  # Move closer to center (was -7)
        glRotatef(-swing, 1, 0, 0)
        glScalef(4, 4, 70)        # Slightly shorter leg if needed
    else:
        glTranslatef(-4, 0, -8)
        glScalef(4, 4, 35)
    glutSolidCube(1)
    glPopMatrix()

    # Right Leg (Cuboid, with swing)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    if runner["alive"]:
        glTranslatef(4, 0, -15)   # Move closer to center (was 7)
        glRotatef(swing, 1, 0, 0)
        glScalef(4, 4, 70)
    else:
        glTranslatef(4, 0, -8)
        glScalef(4, 4, 35)
    glutSolidCube(1)
    glPopMatrix()

    # Draw number on the back
    if runner["alive"]:
        glColor3f(1, 1, 1)  # White text
        glPushMatrix()
        # Move to the back face of the body (negative Y direction)
        glTranslatef(0, -12, CHARACTER_HEIGHT / 2)
        glRotatef(90, 1, 0, 0)  # Stand up vertically (keep if this is what works for you)
        glScalef(0.09, 0.09, 0.09)  # Smaller size

        # Center the number horizontally
        number_str = str(runner["number"])
        text_width = len(number_str) * 60
        glTranslatef(-text_width / 2, 0, 0)

        # Use GLUT_STROKE_ROMAN for "boldest" available stroke font
        for ch in number_str:
            glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(ch))
        glPopMatrix()

    glPopMatrix()

# Draw a bullet
def draw_bullet(bullet):
    glPushMatrix()
    pos = bullet["pos"]
    glTranslatef(pos[0], pos[1], pos[2])
    if "dir" in bullet:
        glColor3f(1, 0, 0)  # Red for guard bullets
    else:
        glColor3f(1, 1, 0)  # Yellow for player bullets
    glutSolidCube(bullet_size)
    glPopMatrix()

# --- Darker golden ground color ---
def draw_field():
    # Draw a sky background (sky blue color)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glColor3f(0.53, 0.81, 0.98)  # Sky blue
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()

    # --- Draw clouds ---
    glColor3f(1, 1, 1)  # White color for clouds
    for cx, cy, sx, sy in [
        (200, 700, 80, 40),
        (250, 730, 50, 25),
        (300, 710, 60, 30),
        (700, 750, 90, 45),
        (750, 770, 60, 30),
        (800, 740, 50, 25),
        (500, 780, 70, 35),
        (550, 760, 40, 20)
    ]:
        glPushMatrix()
        glTranslatef(cx, cy, 0)
        glScalef(sx, sy, 1)
        glutSolidSphere(1, 20, 16)
        glPopMatrix()

    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glEnable(GL_DEPTH_TEST)

    # Draw a plain sand ground
    glColor3f(0.85, 0.74, 0.47)  # Brighter sand color
    glBegin(GL_QUADS)
    glVertex3f(-FIELD_LENGTH_X, -FIELD_LENGTH_Y, 0)
    glVertex3f(FIELD_LENGTH_X, -FIELD_LENGTH_Y, 0)
    glVertex3f(FIELD_LENGTH_X, FIELD_LENGTH_Y, 0)
    glVertex3f(-FIELD_LENGTH_X, FIELD_LENGTH_Y, 0)
    glEnd()

    # --- Wavy sandy pebbled ground overlay ---
    pebble_base_color = (0.88, 0.80, 0.55)
    random.seed(423)  # For consistent pebbles
    pebble_spacing = 48  # Fewer pebbles
    pebble_rows = int((2 * FIELD_LENGTH_X) // pebble_spacing)
    pebble_cols = int((2 * FIELD_LENGTH_Y) // pebble_spacing)
    for i in range(-pebble_rows//2, pebble_rows//2):
        for j in range(-pebble_cols//2, pebble_cols//2):
            px = i * pebble_spacing + random.uniform(-8, 8)
            py = j * pebble_spacing + random.uniform(-8, 8)
            # Wavy effect using sine and cosine
            pz = 1.0 + math.sin(i * 0.5 + j * 0.3) * 1.2 + math.cos(j * 0.4) * 0.8
            size = random.uniform(2, 4)  # Very small pebbles
            glColor3f(
                pebble_base_color[0] + random.uniform(-0.04, 0.04),
                pebble_base_color[1] + random.uniform(-0.04, 0.04),
                pebble_base_color[2] + random.uniform(-0.04, 0.04)
            )
            glPushMatrix()
            glTranslatef(px, py, pz)
            glScalef(size, size * random.uniform(0.7, 1.2), size * random.uniform(0.5, 0.8))
            glutSolidSphere(1, 10, 8)
            glPopMatrix()

    # Wall parameters
    wall_thickness = 5  # Thinner walls
    wall_color = (0.5, 0.5, 0.5)  # Light concrete gray

    # Draw solid, thick, colored walls (no windows)
    # Front wall (+Y)
    draw_brick_wall(
        -FIELD_LENGTH_X + wall_thickness, FIELD_LENGTH_Y, 
        FIELD_LENGTH_X - wall_thickness, FIELD_LENGTH_Y, 
        0, FIELD_HEIGHT, horizontal=True
    )
    # Back wall (-Y)
    draw_brick_wall(
        -FIELD_LENGTH_X + wall_thickness, -FIELD_LENGTH_Y, 
        FIELD_LENGTH_X - wall_thickness, -FIELD_LENGTH_Y, 
        0, FIELD_HEIGHT, horizontal=True
    )
    # Left wall (-X)
    draw_brick_wall(
        -FIELD_LENGTH_X, -FIELD_LENGTH_Y + wall_thickness, 
        -FIELD_LENGTH_X, FIELD_LENGTH_Y - wall_thickness, 
        0, FIELD_HEIGHT, horizontal=False
    )
    # Right wall (+X)
    draw_brick_wall(
        FIELD_LENGTH_X, -FIELD_LENGTH_Y + wall_thickness, 
        FIELD_LENGTH_X, FIELD_LENGTH_Y - wall_thickness, 
        0, FIELD_HEIGHT, horizontal=False
    )

    # Draw start line (near -FIELD_LENGTH_Y)
    glColor3f(0.1, 0.8, 0.1)  # Green for start
    glBegin(GL_QUADS)
    glVertex3f(-FIELD_LENGTH_X, -FIELD_LENGTH_Y + 90, 1)
    glVertex3f(FIELD_LENGTH_X, -FIELD_LENGTH_Y + 90, 1)
    glVertex3f(FIELD_LENGTH_X, -FIELD_LENGTH_Y + 110, 1)
    glVertex3f(-FIELD_LENGTH_X, -FIELD_LENGTH_Y + 110, 1)
    glEnd()

    # Draw finish line (near +FIELD_LENGTH_Y)
    glColor3f(0.9, 0.1, 0.1)  # Red for finish
    glBegin(GL_QUADS)
    glVertex3f(-FIELD_LENGTH_X, FINISH_LINE_Y - 10, 1)
    glVertex3f(FIELD_LENGTH_X, FINISH_LINE_Y - 10, 1)
    glVertex3f(FIELD_LENGTH_X, FINISH_LINE_Y + 10, 1)
    glVertex3f(-FIELD_LENGTH_X, FINISH_LINE_Y + 10, 1)
    glEnd()


    pillar_color = (0.35, 0.28, 0.18)  # Dark brown

    def draw_pillar(x, y):
        glColor3f(*pillar_color)
        glPushMatrix()
        glTranslatef(x, y, FIELD_HEIGHT / 2)
        glScalef(12, 12, FIELD_HEIGHT)
        glutSolidCube(1)
        glPopMatrix()

    # Draw four corner pillars
    draw_pillar(-FIELD_LENGTH_X, -FIELD_LENGTH_Y)
    draw_pillar(FIELD_LENGTH_X, -FIELD_LENGTH_Y)
    draw_pillar(-FIELD_LENGTH_X, FIELD_LENGTH_Y)
    draw_pillar(FIELD_LENGTH_X, FIELD_LENGTH_Y)

# Draw wall guards
def draw_wall_guards():
    guard_positions = []

    # Place guards on the top of the front wall (+Y)
    for i in range(-2, 3):
        guard_positions.append([i * 200, FIELD_LENGTH_Y, FIELD_HEIGHT])

    # Place guards on the top of the back wall (-Y)
    for i in range(-2, 3):
        guard_positions.append([i * 200, -FIELD_LENGTH_Y, FIELD_HEIGHT])

    # Place guards on the top of the left wall (-X)
    for i in range(-3, 4):
        guard_positions.append([-FIELD_LENGTH_X, i * 300, FIELD_HEIGHT])

    # Place guards on the top of the right wall (+X)
    for i in range(-3, 4):
        guard_positions.append([FIELD_LENGTH_X, i * 300, FIELD_HEIGHT])

    # Draw each guard facing the player
    for pos in guard_positions:
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        # Calculate angle to face the player
        dx = player_pos[0] - pos[0]
        dy = player_pos[1] - pos[1]
        angle = math.degrees(math.atan2(dy, dx))
        glRotatef(angle, 0, 0, 1)
        draw_enemy()  # <-- Actually draw the guard here!
        glPopMatrix()

# Draw an enemy (guard)
def draw_enemy():
    # Draws a guard (enemy) with a gun, similar to the player but with a red body
    glPushMatrix()
    # Body (Cuboid) - red for enemy
    glColor3f(0.8, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(0, 0, CHARACTER_HEIGHT / 2)
    glScalef(20, 15, CHARACTER_HEIGHT)
    glutSolidCube(1)
    glPopMatrix()

    # Head (Sphere)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(0, 0, CHARACTER_HEIGHT)
    gluSphere(gluNewQuadric(), 10, 20, 20)
    glPopMatrix()

    # Left Arm (Cylinder)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(-15, 0, CHARACTER_HEIGHT - 10)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 4, 4, 25, 10, 10)
    glPopMatrix()

    # Right Arm (Cylinder)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(15, 0, CHARACTER_HEIGHT - 10)
    glRotatef(-90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 4, 4, 25, 10, 10)
    glPopMatrix()

    # Left Leg (Cuboid)
    glColor3f(0.2, 0.2, 0.8)
    glPushMatrix()
    glTranslatef(-7, 0, 0)
    glScalef(7, 7, 30)
    glutSolidCube(1)
    glPopMatrix()

    # Right Leg (Cuboid)
    glColor3f(0.2, 0.2, 0.8)
    glPushMatrix()
    glTranslatef(7, 0, 0)
    glScalef(7, 7, 30)
    glutSolidCube(1)
    glPopMatrix()

    # Gun (attached to right arm, pointing forward)
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(27, 0, CHARACTER_HEIGHT - 10)
    glRotatef(-90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 3, 3, 45, 10, 10)
    glTranslatef(0, 0, 45)
    glColor3f(1, 0, 0)
    gluSphere(gluNewQuadric(), 2, 10, 10)
    glPopMatrix()

    glPopMatrix()

# Draw a big doll (like Squid Game) just after the finish line
def draw_doll():
    glPushMatrix()
    glTranslatef(0, FINISH_LINE_Y + 40, 0)
    glScalef(8, 8, 8)  # Big doll
    glRotatef(doll_angle, 0, 0, 1)  # Rotate around Z axis (vertical)

    # Body (orange dress)
    glColor3f(1.0, 0.6, 0.1)
    glPushMatrix()
    glTranslatef(0, 0, 18)
    glScalef(1.2, 0.7, 2.5)
    glutSolidCube(10)
    glPopMatrix()

    # Dress skirt (wider base)
    glColor3f(1.0, 0.5, 0.0)
    glPushMatrix()
    glTranslatef(0, 0, 7)
    glScalef(2.0, 1.2, 0.7)
    glutSolidCube(10)
    glPopMatrix()

    # Head (skin color)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(0, 0, 38)
    glutSolidSphere(7, 32, 32)
    glPopMatrix()

    # Cheeks (pink)
    glColor3f(1.0, 0.7, 0.8)
    glPushMatrix()
    glTranslatef(-2.5, 4, 41)
    glutSolidSphere(1, 10, 10)
    glTranslatef(5, 0, 0)
    glutSolidSphere(1, 10, 10)
    glPopMatrix()

    # Eyes (red) -- slightly smaller and centered in front of face
    glColor3f(1, 0, 0)  # Red color for eyes
    # Left eye
    glPushMatrix()
    glTranslatef(-2.2, 6.5, 38)  # X: left, Y: forward (in front of face), Z: center of head
    glutSolidSphere(1.8, 24, 24)   # Slightly smaller eyes
    glPopMatrix()
    # Right eye
    glPushMatrix()
    glTranslatef(2.2, 6.5, 38)    # X: right, Y: forward, Z: center of head
    glutSolidSphere(1.8, 24, 24)
    glPopMatrix()

    # Nose (small sphere, centered between eyes)
    glColor3f(1.0, 0.8, 0.6)
    glPushMatrix()
    glTranslatef(0, 1.2, 43.5)
    glutSolidSphere(0.9, 10, 10)
    glPopMatrix()

    # Ears (skin color, spheres on sides of head)
    glColor3f(*SKIN_COLOR)
    glPushMatrix()
    glTranslatef(-7, 0, 38)
    glutSolidSphere(1.3, 10, 10)
    glTranslatef(14, 0, 0)
    glutSolidSphere(1.3, 10, 10)
    glPopMatrix()

    # Mouth (red, small cube)
    glColor3f(0.8, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(0, -2.5, 41)
    glScalef(1.2, 0.3, 0.3)
    glutSolidCube(2)
    glPopMatrix()

    # Hair (brown cap)
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glTranslatef(0, 0, 44)
    glScalef(1.1, 1.1, 0.5)
    glutSolidSphere(7, 32, 32)
    glPopMatrix()

    # Arms (skin color, positioned like runners' arms but angled outward)
    glColor3f(*SKIN_COLOR)
    # Left arm (rotated 45 degrees to the left)
    glPushMatrix()
    glTranslatef(-10, 0, 31)  # Closer to torso
    glRotatef(30, 0, 0, 1)    # Slightly less outward
    glTranslatef(0, 0, -7.5)
    glScalef(4, 4, 15)
    glutSolidCube(1)
    glPopMatrix()
    # Right arm (rotated 45 degrees to the right)
    glPushMatrix()
    glTranslatef(10, 0, 31)   # Closer to torso
    glRotatef(-30, 0, 0, 1)   # Slightly less outward
    glTranslatef(0, 0, -7.5)
    glScalef(4, 4, 15)
    glutSolidCube(1)
    glPopMatrix()

    # Legs (brown, LONGER)
    glColor3f(0.5, 0.3, 0.1)
    # Left leg
    glPushMatrix()
    glTranslatef(-3, 0, 5)
    glScalef(0.7, 0.7, 3.5)
    glutSolidCube(5)
    glPopMatrix()
    # Right leg
    glPushMatrix()
    glTranslatef(3, 0, 5)
    glScalef(0.7, 0.7, 3.5)
    glutSolidCube(5)
    glPopMatrix()

    glPopMatrix()

# Update bullets position and check for collisions
def update_bullets():
    global bullets
    bullets_to_remove = []
    for i, bullet in enumerate(bullets):
        if "dir" in bullet:
            bullet["pos"][0] += bullet_speed * bullet["dir"][0]
            bullet["pos"][1] += bullet_speed * bullet["dir"][1]
            bullet["pos"][2] += bullet_speed * bullet["dir"][2]
        elif "angle" in bullet:
            angle_rad = math.radians(bullet["angle"])
            bullet["pos"][0] += bullet_speed * math.cos(angle_rad)
            bullet["pos"][1] += bullet_speed * math.sin(angle_rad)
        bullet["distance"] += bullet_speed
        x, y, z = bullet["pos"]
        if (abs(x) > FIELD_LENGTH_X + 200 or abs(y) > FIELD_LENGTH_Y + 200 or
            abs(z) > FIELD_HEIGHT * 2 or
            bullet["distance"] > FIELD_LENGTH_Y * 3):
            bullets_to_remove.append(i)
    for i in sorted(bullets_to_remove, reverse=True):
        if i < len(bullets):
            bullets.pop(i)

# Handle cheat mode rotation and automatic shooting
def update_cheat_mode():
    global player_angle, last_shot_time

# Update runners' positions and states
def update_runners():
    global runners

    now = time.time()
    for runner in runners:
        if not runner["alive"]:
            continue

        # RED LIGHT: If doll's angle is between 100 and 180, moving means death after 1 second
        if doll_looking and 100 <= doll_angle <= 180:
            if runner["moving"]:
                # Start timer if just started moving during red light
                if runner.get("red_light_move_time") is None:
                    runner["red_light_move_time"] = now
                # Shoot after 1 second of moving during red light
                if now - runner["red_light_move_time"] >= 1.0:
                    runner["alive"] = False
                    runner["moving"] = False
                    runner["red_light_move_time"] = None
                    spawn_guard_bullet_at_runner(runner)
                    elimination_messages.append((runner["number"], time.time()))  # Show elimination message
                else:
                    runner["pos"][1] += runner["speed"]
            else:
                runner["red_light_move_time"] = None  # Reset if not moving
        else:
            # GREEN LIGHT: Only move if doll_angle == 0
            runner["red_light_move_time"] = None  # Reset timer
            if doll_angle == 0 and runner["alive"]:
                runner["moving"] = True
                runner["pos"][1] += runner["speed"]
            else:
                runner["moving"] = False

# Update game state
def update_game():
    global countdown_active, countdown_start_time, game_start_time, doll_rotating, doll_looking, doll_angle, doll_facing_forward
    global phase, last_phase_switch, phase_duration, game_over
    global time_up, guards_shot_time, player_life
    global doll_last_switch, doll_rotating, doll_looking, doll_facing_forward
    global player_red_light_move_time, player_dead

    # Print the doll's eye angle every frame
    # print(f"Doll eye angle (degrees): {doll_angle}")

    if countdown_active:
        doll_angle = 0
        doll_looking = True
        doll_rotating = False
        for runner in runners:
            runner["moving"] = False
        if time.time() - countdown_start_time >= COUNTDOWN_TIME:
            countdown_active = False
            game_start_time = time.time()
            doll_looking = False
            doll_rotating = True
            doll_facing_forward = True   # <-- Fix: start rotating toward players
            doll_last_switch = time.time()
        return

    if game_over:
        return

    # --- DOLL ROTATION LOGIC ---
    now = time.time()

    if doll_rotating:
        # Rotate the doll smoothly
        elapsed = now - doll_last_switch
        if doll_facing_forward:
            doll_angle = min(180, elapsed / doll_rotate_duration * 180)
            if doll_angle >= 180:
                doll_rotating = False
                doll_looking = True
                doll_last_switch = now
                # --- PANIC LOGIC: Some runners panic and start running ---
                for runner in runners:
                    if runner["alive"]:
                        if random.random() < 0.18:  # 18% chance to panic
                            runner["moving"] = True
                            runner["red_light_move_time"] = None  # Will be set in update_runners
                        else:
                            runner["moving"] = False
        else:
            doll_angle = max(0, 180 - elapsed / doll_rotate_duration * 180)
            if doll_angle <= 0:
                doll_rotating = False
                doll_looking = False
                doll_last_switch = now
    elif doll_looking:
        # Stay looking forward for a while, then rotate back
        if now - doll_last_switch > doll_look_duration:
            doll_rotating = True
            doll_facing_forward = False
            doll_last_switch = now
    elif not doll_rotating and not doll_looking:
        # Stay facing backward for a while, then rotate forward
        if now - doll_last_switch > doll_back_duration:
            doll_rotating = True
            doll_facing_forward = True
            doll_last_switch = now

    # Timer check
    if not time_up and game_start_time is not None:
        elapsed = time.time() - game_start_time
        if elapsed > GAME_TIME_LIMIT:
            time_up = True
            guards_shot_time = time.time()  # Start shooting
            eliminate_remaining_runners()    # Eliminate all runners who didn't finish
            if not player_dead and not game_over:
                player_dead = True
                shoot_from_guards_at_player()

    # Check if player reached finish line
    if player_pos[1] >= FINISH_LINE_Y:
        game_over = True

    update_bullets()
    update_runners()
    if cheat_mode:
        update_cheat_mode()

    # --- PLAYER RED LIGHT SHOOT LOGIC ---
    now = time.time()
    if doll_looking and 100 <= doll_angle <= 180 and player_moving and not player_dead:
        if player_red_light_move_time is Nowwne:
            player_red_light_move_time = now
        if now - player_red_light_move_time >= 1.0:
            player_dead = True
            player_red_light_move_time = None
            shoot_from_guards_at_player()
    else:
        player_red_light_move_time = None

    update_bullets()
    update_runners()

# Reset game state
def reset_game():
    global game_over, player_life, game_score, bullets_missed
    global player_pos, player_angle, bullets, cheat_mode, auto_vision, last_shot_time
    global game_start_time, time_up, camera_follow_player, camera_angle
    global countdown_start_time, countdown_active

    game_over = False
    player_life = 200
    game_score = 0
    bullets_missed = 0
    player_pos = [0.0, -FIELD_LENGTH_Y + 100, 0.0]
    player_angle = 90  # Face toward finish line
    camera_angle = 90  # Camera behind player
    bullets = []
    cheat_mode = False
    auto_vision = False
    last_shot_time = time.time()
    init_runners()
    init_guard_states()
    game_start_time = None  # Will be set after countdown
    time_up = False
    camera_follow_player = True
    countdown_start_time = time.time()
    countdown_active = True

def shoot_from_guards_at_player():
    global bullets, game_over

    if game_over:
        return

    guard_positions = []
    for i in range(-2, 3):
        guard_positions.append([i * 200, FIELD_LENGTH_Y, FIELD_HEIGHT])
        guard_positions.append([i * 200, -FIELD_LENGTH_Y, FIELD_HEIGHT])
    for i in range(-3, 4):
        guard_positions.append([-FIELD_LENGTH_X, i * 300, FIELD_HEIGHT])
        guard_positions.append([FIELD_LENGTH_X, i * 300, FIELD_HEIGHT])

    for pos in guard_positions:
        dx = player_pos[0] - pos[0]
        dy = player_pos[1] - pos[1]
        dz = (player_pos[2] + CHARACTER_HEIGHT / 2) - pos[2]
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length == 0:
            continue  # Avoid division by zero
        dir_x = dx / length
        dir_y = dy / length
        dir_z = dz / length
        bullets.append({
            "pos": [pos[0], pos[1], pos[2]],
            "dir": [dir_x, dir_y, dir_z],
            "distance": 0
        })

def spawn_guard_bullet_at_runner(runner):
    guard_positions = []
    for i in range(-2, 3):
        guard_positions.append([i * 200, FIELD_LENGTH_Y, FIELD_HEIGHT])
        guard_positions.append([i * 200, -FIELD_LENGTH_Y, FIELD_HEIGHT])
    for i in range(-3, 4):
        guard_positions.append([-FIELD_LENGTH_X, i * 300, FIELD_HEIGHT])
        guard_positions.append([FIELD_LENGTH_X, i * 300, FIELD_HEIGHT])

    rx, ry, rz = runner["pos"]
    nearest_guard = min(guard_positions, key=lambda pos: (pos[0]-rx)**2 + (pos[1]-ry)**2 + (pos[2]-rz)**2)
    dx = rx - nearest_guard[0]
    dy = ry - nearest_guard[1]
    dz = (rz + CHARACTER_HEIGHT / 2) - nearest_guard[2]
    length = math.sqrt(dx*dx + dy*dy + dz*dz)
    if length == 0:
        return
    dir_x = dx / length
    dir_y = dy / length
    dir_z = dz / length
    bullets.append({
        "pos": [nearest_guard[0], nearest_guard[1], nearest_guard[2]],
        "dir": [dir_x, dir_y, dir_z],
        "distance": 0
    })

def eliminate_remaining_runners():
    global runners, elimination_messages
    for runner in runners:
        if runner["alive"] and runner["pos"][1] < FINISH_LINE_Y:
            runner["alive"] = False
            elimination_messages.append((runner["number"], time.time()))

def keyboardListener(key, x, y):
    global player_pos, player_angle, cheat_mode, auto_vision, game_over, camera_follow_player, player_dead, player_moving
    global paused

    # Pause/unpause with 'p'
    if key == b'p':
        paused = not paused
        glutPostRedisplay()
        return

    if paused:
        return

    # Press 'r' to reset/restart the game if dead or game over
    if key == b'r' and (player_dead or game_over):
        reset_game()
        player_dead = False
        return

    # Only allow movement if not dead or game over
    if player_dead or game_over:
        return

    move_distance = player_speed
    player_moving = False  # Reset at the start

    # Only get shot if doll is looking AND doll_angle is near 90 degrees
    if doll_looking and 80 <= doll_angle <= 100 and key in [b'w', b'a', b's', b'd']:
        player_dead = True
        # shoot_from_guards_at_player()
        return

    # Move forward (W key)
    if key == b'w':
        angle_rad = math.radians(player_angle)
        dx = move_distance * math.cos(angle_rad)
        dy = move_distance * math.sin(angle_rad)
        new_x = player_pos[0] + dx
        new_y = player_pos[1] + dy
        
        # Check boundaries before updating
        if abs(new_x) < FIELD_LENGTH_X - 50 and abs(new_y) < FIELD_LENGTH_Y - 50:
            player_pos[0] = new_x
            player_pos[1] = new_y
        player_moving = True

    # Move backward (S key)
    elif key == b's':
        angle_rad = math.radians(player_angle)
        dx = move_distance * math.cos(angle_rad)
        dy = move_distance * math.sin(angle_rad)
        new_x = player_pos[0] - dx
        new_y = player_pos[1] - dy
        
        # Check boundaries before updating
        if abs(new_x) < FIELD_LENGTH_X - 50 and abs(new_y) < FIELD_LENGTH_Y - 50:
            player_pos[0] = new_x
            player_pos[1] = new_y
        player_moving = True

    # Rotate left (A key)
    elif key == b'a':
        player_angle = (player_angle - rotation_speed) % 360

    # Rotate right (D key)
    elif key == b'd':
        player_angle = (player_angle + rotation_speed) % 360

    # Toggle cheat mode (C key)
    elif key == b'c':
        cheat_mode = not cheat_mode
    # Toggle auto vision in cheat mode (V key)
    elif key == b'v' and cheat_mode:
        auto_vision = not auto_vision
    if key == b'v':
        camera_follow_player = not camera_follow_player

    # Guards fire at player (G key)
    if key == b'g':
        shoot_from_guards_at_player()
    
    glutPostRedisplay()  # Request a screen update

def keyboardUpListener(key, x, y):
    global player_moving
    if key in [b'w', b's']:
        player_moving = False

def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for adjusting the camera angle and height.
    """
    global camera_angle, camera_height
    
    # Move camera up (UP arrow key)
    if key == GLUT_KEY_UP:
        camera_height = min(camera_height + 20, 1000)  # Limit maximum height
    
    # Move camera down (DOWN arrow key)
    if key == GLUT_KEY_DOWN:
        camera_height = max(camera_height - 20, 100)  # Limit minimum height
    
    # Rotate camera left (LEFT arrow key)
    if key == GLUT_KEY_LEFT:
        camera_angle = (camera_angle - 5) % 360
    
    # Rotate camera right (RIGHT arrow key)
    if key == GLUT_KEY_RIGHT:
        camera_angle = (camera_angle + 5) % 360

def mouseListener(button, state, x, y):
    """
    Handles mouse inputs for firing bullets (left click) and toggling camera mode (right click).
    """
    global camera_mode
    
    # Right mouse button toggles camera tracking mode
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        if camera_mode == "third_person":
            camera_mode = "first_person"
        else:
            camera_mode = "third_person"

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 5000)  # Far plane is now 5000 units away
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camera_mode == "first_person":
        eye_height = player_pos[2] + gun_height + 20
        angle_rad = math.radians(player_angle)
        look_x = player_pos[0] + 100 * math.cos(angle_rad)
        look_y = player_pos[1] + 100 * math.sin(angle_rad)
        gluLookAt(
            player_pos[0], player_pos[1], eye_height,
            look_x, look_y, eye_height,
            0, 0, 1
        )
    else:
        if camera_follow_player:
            # Camera always behind the player, close distance
            dist = 80
            angle_rad = math.radians(player_angle)
            cam_x = player_pos[0] - dist * math.cos(angle_rad)
            cam_y = player_pos[1] - dist * math.sin(angle_rad)
            cam_z = player_pos[2] + gun_height + 40  # Slightly above player
            target_x = player_pos[0]
            target_y = player_pos[1]
            target_z = player_pos[2] + gun_height
        else:
            angle_rad = math.radians(camera_angle)
            dist = 200
            cam_x = dist * math.cos(angle_rad)
            cam_y = dist * math.sin(angle_rad)
            cam_z = camera_height
            target_x = 0
            target_y = 0
            target_z = 0
        gluLookAt(
            cam_x, cam_y, cam_z,
            target_x, target_y, target_z,
            0, 0, 1
        )

def idle():
    global animation_time
    if not paused:
        animation_time += 0.1  # Adjust speed as needed
        update_game()
    glutPostRedisplay()

def showScreen():
    """
    Display function to render the game scene:
    - Clears the screen and sets up the camera
    - Draws the grid, player, runners, bullets, guards, and game information
    """
    # Clear color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, 1000, 800)  # Set viewport size

    setupCamera()  # Configure camera perspective

    # Draw the field and all objects
    draw_field()
    draw_doll()
    draw_wall_guards()
    draw_player()
    for runner in runners:
        draw_runner(runner)

    # Draw all active bullets
    for bullet in bullets:
        draw_bullet(bullet)

    # Display game information
    draw_text(10, 770, f"Life: {player_life}")
    draw_text(10, 740, f"Score: {game_score}")
    draw_text(10, 710, f"Missed Shots: {bullets_missed/10}")

    # Display timer at top center
    if countdown_active:
        draw_text(450, 770, f"Time: 0/{GAME_TIME_LIMIT}", GLUT_BITMAP_TIMES_ROMAN_24, color=(1, 0, 0))
    elif game_start_time is not None:
        elapsed = int(time.time() - game_start_time)
        draw_text(450, 770, f"Time: {elapsed}/{GAME_TIME_LIMIT}", GLUT_BITMAP_TIMES_ROMAN_24, color=(1, 0, 0))

    # Display countdown if active
    if countdown_active:
        seconds_left = int(COUNTDOWN_TIME - (time.time() - countdown_start_time)) + 1
        draw_text(450, 400, f"Starting in {seconds_left}...", GLUT_BITMAP_TIMES_ROMAN_24)

    # Display "TIME'S UP" message if time is up but game is not over
    if time_up and not game_over:
        draw_text(400, 370, "TIME'S UP! Guards are shooting!")

    # Display game over messages
    if game_over:
        draw_text(400, 400, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24)
        if player_life <= 0:
            draw_text(350, 370, "You died! Guards shot you.")
        elif player_pos[1] >= FINISH_LINE_Y:
            draw_text(350, 370, "You Win! You reached the finish line.")

    # Show elimination messages for 2 seconds
    current_time = time.time()
    y_base = 350
    y_step = 32  # Space between messages
    visible_msgs = [msg for msg in elimination_messages if current_time - msg[1] < 2.0]
    for idx, (number, t) in enumerate(visible_msgs):
        draw_text(350, y_base - idx * y_step, f"Player {number} eliminated", font=GLUT_BITMAP_TIMES_ROMAN_24, color=(1, 0, 0))
    for msg in elimination_messages[:]:
        if current_time - msg[1] >= 2.0:
            elimination_messages.remove(msg)

    if paused:
        draw_text(420, 400, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24, color=(1, 1, 0))

    glutSwapBuffers()

def draw_brick_wall(x1, y1, x2, y2, z_bottom, z_top, horizontal=True):
    brick_color = (0.7, 0.1, 0.1)  # Red brick
    mortar_color = (0.85, 0.7, 0.6)  # Light mortar
    brick_height = 18
    brick_length = 48
    mortar_thickness = 2

    # Calculate wall dimensions
    if horizontal:
        wall_length = abs(x2 - x1)
        wall_height = abs(z_top - z_bottom)
        bricks_per_row = int(wall_length // brick_length) + 1
        rows = int(wall_height // brick_height) + 1
        for row in range(rows):
            y = y1
            z = z_bottom + row * brick_height
            offset = (brick_length // 2) if row % 2 else 0
            for col in range(bricks_per_row):
                x = x1 + col * brick_length - offset
                # Draw brick
                glColor3f(*brick_color)
                glBegin(GL_QUADS)
                glVertex3f(x + mortar_thickness, y, z + mortar_thickness)
                glVertex3f(x + brick_length - mortar_thickness, y, z + mortar_thickness)
                glVertex3f(x + brick_length - mortar_thickness, y, z + brick_height - mortar_thickness)
                glVertex3f(x + mortar_thickness, y, z + brick_height - mortar_thickness)
                glEnd()
    else:
        wall_length = abs(y2 - y1)
        wall_height = abs(z_top - z_bottom)
        bricks_per_row = int(wall_length // brick_length) + 1
        rows = int(wall_height // brick_height) + 1
        for row in range(rows):
            x = x1
            z = z_bottom + row * brick_height
            offset = (brick_length // 2) if row % 2 else 0
            for col in range(bricks_per_row):
                y = y1 + col * brick_length - offset
                # Draw brick
                glColor3f(*brick_color)
                glBegin(GL_QUADS)
                glVertex3f(x, y + mortar_thickness, z + mortar_thickness)
                glVertex3f(x, y + brick_length - mortar_thickness, z + mortar_thickness)
                glVertex3f(x, y + brick_length - mortar_thickness, z + brick_height - mortar_thickness)
                glVertex3f(x, y + mortar_thickness, z + brick_height - mortar_thickness)
                glEnd()

if __name__ == "__main__":
    # Initialize GLUT and start the main loop
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GL_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Red Light Green Light Game")
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.0, 0.0, 0.0, 1.0)

    reset_game()

    glutDisplayFunc(showScreen)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)  # <-- Add this line
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)

    glutMainLoop()




















# Camera setup function (called every frame)
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 5000)  # Far plane is now 5000 units away
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()  

    if camera_mode == "first_person": 
        eye_height = player_pos[2]  + 20
        angle_rad = math.radians(player_angle) 
        look_x = player_pos[0] + 100 * math.cos(angle_rad)
        look_y = player_pos[1] + 100 * math.sin(angle_rad)
        gluLookAt(
            player_pos[0], player_pos[1], eye_height,
            look_x, look_y, eye_height,
            0, 0, 1
        )
        
    else:
        if camera_follow_player:
            # Camera always behind the player, close distance
            dist = 80
            angle_rad = math.radians(player_angle)
            cam_x = player_pos[0] - dist * math.cos(angle_rad)
            cam_y = player_pos[1] - dist * math.sin(angle_rad)
            cam_z = player_pos[2] + 40  # Slightly above player
            target_x = player_pos[0]
            target_y = player_pos[1]
            target_z = player_pos[2] + gun_height
        else:
            angle_rad = math.radians(camera_angle)
            dist = 200
            cam_x = dist * math.cos(angle_rad)
            cam_y = dist * math.sin(angle_rad)
            cam_z = camera_height
            target_x = 0 
            target_y = 0
            target_z = 0
        gluLookAt(
            cam_x, cam_y, cam_z,
            target_x, target_y, target_z,
            0, 0, 1
        )


##Pausing the game

paused = False


def keyboardListener(key, x, y):
    global paused
    # Pause/unpause with 'p'
    if key == b'p':
        paused = not paused
        glutPostRedisplay()
        return

    if paused:
        return
    # ...rest of your code...

def idle():
    global animation_time
    if not paused:
        animation_time += 0.1  # Adjust speed as needed
        update_game()
    glutPostRedisplay()

def showScreen():

    if paused:
        draw_text(420, 400, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24, color=(1, 1, 0))




