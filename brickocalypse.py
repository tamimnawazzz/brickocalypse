from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import * #for utilities like gluPerspective() and gluSphere()
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math
import random
import time

#____________________cam related variables____________________
camera_pos = (0, 300, 200) # start 500 units away along  +Y,+Z,
# x = 0 → camera is centered horizontally ___
# y = 500 → camera is 500 units towards me
# z = 500 → camera is 500 units "up" __I__

screen_width = 1200
screen_height = 700
fovY = 120  #Field Of View, in degrees.
GRID_LENGTH = 2000  # full length of grid lines along each axis (1000 in neg,0,100 in pos)
cells = 15
cell_size = GRID_LENGTH*2 / cells #one side / a

#______________________main_char__________________
scale_factor = 1
player_x = 0
player_y = 0
player_z = 0
move_speed = 40
p_multiplier = 20
player_angle = 0
life = 5
score = 0

fpp = False
game_over = False
cam_rotate = True
rotation_speed = 0.5

#___________________power spheres_____________
powerup_li = [] # scattered powerups
last_powerup_time = 0
player_boost_speed = False
boost_end_time = 0


#_______________enemy__________________
enemy_scale_factor = 1
enemy_count = 5
enemy_li = []
enemy_speed = 0.3
e_multiplier = 0.05
enemy_nerf = False
enemy_slow_time = 0

#____________________bullet_________________
bullet_li = []
bullet_speed = 5
max_bullets = 30
last_shot_time = 0

#___________________Tower___________________
tower_height = 0
target_height = 12  # win condition

#___________________bricks_______________
brick_li = []   # scattered tower pieces


#___________________obstacles__________________
obstacle_li = []   # list of obstacles (trees & rocks)


#____________________day/night________________
day_night = "day"
last_day_switch = time.time()



def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18): #draws 2D text on the screen

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    # Set up an orthographic projection that matches window 
    # kottuk jaygay akbo, canvas 
    # Sets coordinates so (0,0) is center of the window
    gluOrtho2D(-screen_width/2, screen_width/2, -screen_height/2, screen_height/2) # left, right, bottom, top
    #changing to 2d to draw text

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(1,1,1)
    #position from where text will start showing
    glRasterPos2f(x,y)
    
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    #Restore projection and modelview matrices (back to 3D)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def make_obstacles(num_trees, num_rocks):

    global obstacle_li
    obstacle_li = []

    # initialize trees
    for i in range(num_trees):
        while True:
            x = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
            y = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
            if abs(x) < 200 and abs(y) < 200:
                continue
            # check no overlap
            ok = True
            for o in obstacle_li:
                if math.hypot(x - o["x"], y - o["y"]) < 120:
                    ok = False
                    break
            if ok:
                break
        obstacle_li.append({
            "type": "tree",
            "x": x,
            "y": y,
            "z": 0,
            "trunk_height": random.randint(80, 150),  # taller trees
            "radius": random.randint(50, 80)
        })

    # initialize rocks
    for i in range(num_rocks):
        while True:
            x = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
            y = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
            if abs(x) < 150 and abs(y) < 150:
                continue
            ok = True
            for o in obstacle_li:
                if math.hypot(x - o["x"], y - o["y"]) < 120:
                    ok = False
                    break
            if ok:
                break
        obstacle_li.append({
            "type": "rock",
            "x": x,
            "y": y,
            "z": 0,
            "size": random.randint(40, 120),
            "radius": random.randint(40, 100)
        })

def draw_obstacles():
    # Trees have - scaled cube for logs + stacked spheres for leaves
    # Rocks have - silver spheres
    for o in obstacle_li:
        glPushMatrix()
        glTranslatef(o["x"], o["y"], o["z"])
        if o["type"] == "tree":
            # log (brown)
            glColor3f(0.35, 0.20, 0.05)
            glPushMatrix()
            # trunk centered at base, raise by trunk_height/2
            th = o["trunk_height"]*1.5
            glTranslatef(0, 0, th/2)
            glScalef(40, 40, th)   # thick tall trunk
            glutSolidCube(1)       # scaled cube becomes trunk
            glPopMatrix()

            # leaves - 2 or 3 green spheres stacked
            glColor3f(0.02, 0.15, 0.02)  # leaf color
            leaf_count = 4
            for i in range(leaf_count):
                glPushMatrix()
                # places spheres above trunk
                zpos = th + i*25
                glTranslatef(0, 0, zpos)
                # stacking spheres - radius derived from obstacle radius
                sphere_r = o["radius"] * (0.6 + 0.2*i)
                gluSphere(gluNewQuadric(), sphere_r, 16, 12)
                glPopMatrix()
        else:  # rock
            glColor3f(0.5, 0.5, 0.5) # silver-ish
            glPushMatrix()
            # rock sits on ground, raise a bit by approx size
            size = o["size"]
            glTranslatef(0, 0, size/2)
            # two sphere rocks
            gluSphere(gluNewQuadric(), size, 12, 10)
            glTranslatef(size*0.2, -size*0.1, 0)
            gluSphere(gluNewQuadric(), size*0.7, 12, 10)
            glPopMatrix()
        glPopMatrix()

def is_colliding_with_obstacles(x, y, radius=30):
 
    # collision check against all obstacles using radius
    # x,y -> point to check; radius -> clearance radius around point.
 
    for o in obstacle_li:
        dx = x - o["x"]
        dy = y - o["y"]
        dist = math.hypot(dx, dy) #eucledian
        if dist < (radius + o["radius"]):
            return True
    return False

def main_char():
    global player_x, player_y, player_z, player_angle, scale_factor,fpp
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z)
    if game_over:
        glRotatef(-90, 1, 0, 0)


    glRotatef(180, 0, 0, 1)
    glRotatef(player_angle, 0, 0, 1)

    #_____Legs_____
    glColor3f(0.25, 0.0, 0.25)    #purple pants
    #left
    glPushMatrix()
    glTranslatef(-15*scale_factor, 0, 35*scale_factor)
    glScalef(1*scale_factor, 1*scale_factor, 2*scale_factor)
    glutSolidCube(20)
    glPopMatrix()
    #right
    glPushMatrix()
    glTranslatef(15*scale_factor, 0, 35*scale_factor)
    glScalef(1*scale_factor, 1*scale_factor, 2*scale_factor)
    glutSolidCube(20)
    glPopMatrix()

    #_____Body_____
    glColor3f(0.0, 1.0, 1.0)    #cyan tee
    glPushMatrix()
    glTranslatef(0, 0, 90*scale_factor)
    glScalef(1.5*scale_factor, 0.75*scale_factor, 2*scale_factor)
    glutSolidCube(35)
    glPopMatrix()

    #_____Arms_____
    glColor3f(0.82, 0.70, 0.55)    #cream skin color
    #left
    glPushMatrix()
    glTranslatef(-25*scale_factor, 15*scale_factor, 105*scale_factor)  # relative to body
    glRotatef(-50, 1, 0, 0)  # slight downward bend toward gun
    glScalef(1*scale_factor, 1*scale_factor, 2*scale_factor)
    glutSolidCube(20)
    glPopMatrix()
    #right
    glPushMatrix()
    glTranslatef(25*scale_factor, 15*scale_factor, 105*scale_factor)  # relative to body
    glRotatef(-50, 1, 0, 0)  # slight downward bend toward gun
    glScalef(1*scale_factor, 1*scale_factor, 2*scale_factor)
    glutSolidCube(20)
    glPopMatrix()
    #___dart gun___
    glColor3f(0.3, 0.3, 0.35)
    glPushMatrix()
    glTranslatef(0, 80*scale_factor, 125*scale_factor)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 5*scale_factor, 5*scale_factor, 60*scale_factor, 10, 10)
    glPopMatrix()


    if fpp:
        #___head___
        glColor3f(0.0, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(0, 0, 120*scale_factor) #over body
        gluSphere(gluNewQuadric(), 12, 12, 12)
        glPopMatrix()
    else:
        #_____Head_____
        glColor3f(0.82, 0.70, 0.55)   #cream skin color
        glPushMatrix()
        head_z_position = (100*scale_factor) + (40*2*scale_factor)/2
        glTranslatef(0, 0, head_z_position)
        glScalef(scale_factor, scale_factor, scale_factor)
        glutSolidCube(30)
        glPopMatrix()

    glPopMatrix()


def make_bricks():
    global brick_li
    brick_li = [] #clear
    brick_count = 3
    for i in range(brick_count):
        while True:
            x = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
            y = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
            #so brick doesnt go into obj
            if not is_colliding_with_obstacles(x, y, radius=30) and not (abs(x)<150 and abs(y)<150):
                break
        brick_li.append({"x": x, "y": y, "z": 0, "collected": False})

def draw_bricks():
    global brick_li
    count = 0
    for b in brick_li:
        if not b["collected"]:
            glColor3f(1.0, 0.5, 0.0)  # orange
            glPushMatrix()
            glTranslatef(b["x"], b["y"], b["z"]+20)
            glScalef(1.75, 3, 1)
            glutSolidCube(50)
            glPopMatrix()
            count+=1

#placing bricks  
def check_brick_collection():
    global brick_li, tower_height
    for b in brick_li:
        if not b["collected"]:
            dist = math.sqrt((player_x-b["x"])**2+(player_y-b["y"])**2)
            if dist < 40:
                b["collected"] = True
                # player then must return to center block to stack bricks
    #minimun tower boundary        
    if player_x**2 + player_y**2 < 80**2:  #tower center with minimun offset
        for b in brick_li:
            if b["collected"]:
                tower_height += 1
                #bricks spawn at random without colliding with obj
                while True:
                    x = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
                    y = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
                    if is_colliding_with_obstacles(x, y, radius=80) == False:
                        if (abs(x)<200 and abs(y)<200) == False: # if not too close to the center tower
                            break
                #pass the values
                b["x"] = x
                b["y"] = y
                b["collected"] = False

def make_enemy():
    global enemy_li, tower_height
    enemy_li=[]
    for i in range(enemy_count):
        # choose type depending on tower_height
        if tower_height >= 8:
            t = random.choice(["normal", "fast", "tank"])
        elif tower_height >= 4:
            t = random.choice(["normal", "fast"])
        else:
            t = "normal"
        while True:
            x = random.randint(-GRID_LENGTH, GRID_LENGTH)
            y = random.randint(-GRID_LENGTH, GRID_LENGTH)
            if is_colliding_with_obstacles(x, y, radius=80) == False:
                if (abs(x) < 200 and abs(y) < 200) == False: # if not too close to the center tower
                    break
        enemy_li.append({"x": x, "y": y, "z":0, "alive":True, "type":t})

def draw_enemy():
    global enemy_scale_factor, enemy_li,game_over
    for enemy in enemy_li:
        if enemy["alive"] == False:
            continue

        #enemy size change
        base_scale = enemy_scale_factor * (1+ 0.2*math.sin(time.time()*2.5 ))
        glPushMatrix()
        glTranslatef(enemy["x"], enemy["y"], enemy["z"])

        #color and shape depending on type
        if enemy["type"] == "tank":
            glColor3f(0.2, 0.0, 0.0)  # dark red
            body_scale_x = 2.5  # wide
            body_scale_y = 2
            body_scale_z = 1.0  # normal height
        elif enemy["type"] == "fast":
            glColor3f(1.0, 0.5, 0.0)  # orange
            body_scale_x = 1.0
            body_scale_y = 1.0
            body_scale_z = 2  # taller
        else:  # normal
            glColor3f(1.0, 0.0, 0.0)  # red
            body_scale_x = 1.0
            body_scale_y = 1.0
            body_scale_z = 1.0
   
        #initializing quadric - not needed here but used as a safe case
        quad = gluNewQuadric()

        # Body
        glPushMatrix()
        glTranslatef(0, 300, 50*base_scale)
        glScalef(body_scale_x, body_scale_y, body_scale_z)
        gluSphere(quad, 50*base_scale, 20, 20)
        glPopMatrix()

        # Head
        glColor3f(0.0, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(0, 280, 120*base_scale)
        gluSphere(quad, 15*base_scale, 20, 20)
        glPopMatrix()

        #deleting quadric
        gluDeleteQuadric(quad)

        glPopMatrix()

def draw_tower():
    global tower_height
    glColor3f(0.8, 0.3, 0.1)
    for i in range(tower_height):
        if i % 2 == 0:
            glColor3f(0.36, 0.20, 0.09)  # darker brown
        else:
            glColor3f(0.55, 0.27, 0.07)  # dark brown
        glPushMatrix()
        glTranslatef(0,0,i*50)
        glutSolidCube(200)
        glPopMatrix()

def make_powerup():
    global powerup_li, last_powerup_time
    now = time.time()
    if now - last_powerup_time > 10:
        last_powerup_time = now
        p = random.choice(["speed","ammo","slow"])
        powerup_li.append({"x":random.randint(-GRID_LENGTH,GRID_LENGTH),
                           "y":random.randint(-GRID_LENGTH,GRID_LENGTH),
                           "z":0,"type":p})
def draw_powerups():
    global powerup_li
    for p in powerup_li:
        if p["type"]=="speed":
            glColor3f(1,1,0) #yellow
        if p["type"]=="ammo":
            glColor3f(0,0,1) #blue
        if p["type"]=="slow":
            glColor3f(1,0,0) #red
        glPushMatrix()
        glTranslatef(p["x"],p["y"],p["z"]+40)
        gluSphere(gluNewQuadric(), 25, 20, 20) #func,radius,slices,stacks
        glPopMatrix()

def check_powerup_collection():
    global powerup_li, player_boost_speed, boost_end_time,enemy_speed,enemy_slow_time,bullet_li,move_speed,p_multiplier,e_multiplier,enemy_nerf
    for p in powerup_li.copy():
        dist = math.sqrt((player_x-p["x"])**2+(player_y-p["y"])**2) #alt way of calculating eucledian without using hypot

        #collision
        if dist<40:
            if p["type"]=="speed":
                player_boost_speed = True
                move_speed += p_multiplier
                boost_end_time = time.time()+10
                print("Player speed boosted for 10s")
            if p["type"]=="ammo":
                bullet_li = []
                print("Ammo refilled")
            if p["type"]=="slow":
                enemy_nerf = True
                enemy_speed = e_multiplier
                enemy_slow_time = time.time()+10
                print("Enemies slowed for 10s")
            powerup_li.remove(p)

def draw_bullets():
    global bullet_li
    glColor3f(1, 1, 0)  #yellow bullets
    for bullet in bullet_li:
        glPushMatrix()
        glTranslatef(bullet["x"], bullet["y"], bullet["z"])
        glutSolidCube(10)
        glPopMatrix()

def draw_shapes():
    global fpp
    # +x is left, -x is right
    # +y is is towards me, -y is away from me
    # +z is up, -z is down

    main_char()
    draw_enemy()
    draw_bullets()
    draw_obstacles()
    draw_bricks()
    draw_powerups()
    draw_tower()

def shoot_bullet():
    global bullet_li,game_over

    if len(bullet_li) >= max_bullets:
        return
    
    #bullet direction based on player angle, basically angular vector direction
    dx = math.sin(math.radians(player_angle)) #as + is left,flip
    dy = -math.cos(math.radians(player_angle)) #as +y is down,flip
    dz = 0
    
    #Start dart at player's mouth position
    bullet_li.append({"x":player_x, "y":player_y, "z":player_z + 125*scale_factor, "dx":dx, "dy":dy, "dz":dz, "distance":0})

    if len(bullet_li) >= max_bullets:
        game_over = True

def animate():
    global bullet_li, enemy_li,enemy_nerf, score, life, enemy_speed, game_over,player_boost_speed, boost_end_time, bullet_speed,tower_height,move_speed,enemy_slow_time
    if game_over:
        return

    #bullet movement
    for bullet_dict in bullet_li.copy():
        bullet_dict["x"] += bullet_dict["dx"]*bullet_speed
        bullet_dict["y"] += bullet_dict["dy"]*bullet_speed
        bullet_dict["z"] += bullet_dict["dz"]*bullet_speed
        bullet_dict["distance"] += bullet_speed
        
        
        #bullet collision check
        for enemy in enemy_li:
            if enemy["alive"] == False and game_over == True:
                continue
            distance = math.sqrt((bullet_dict["x"]-enemy["x"])**2 + (bullet_dict["y"]-(enemy["y"]+300))**2 +(bullet_dict["z"]-(enemy["z"]+50))**2)
            
            if distance < 100:  #collision radius
                if bullet_dict in bullet_li:
                    bullet_li.remove(bullet_dict)
                score += 1
                enemy["alive"] = False #kill
                #respawn
                while True:
                    enemy["x"] = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
                    enemy["y"] = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
                    enemy["z"] = 0
                    if is_colliding_with_obstacles(enemy["x"], enemy["y"], radius=80) == False:
                        if (abs(enemy["x"]) < 200 and abs(enemy["y"]) < 200) == False:
                            break
                #upgrade - set alive true
                enemy["alive"] = True
                
                # enemy type based on current tower height
                if tower_height >= 8:
                    enemy["type"] = random.choice(["normal", "fast", "tank"])
                elif tower_height >= 4:
                    enemy["type"] = random.choice(["normal", "fast"])
                else:
                    enemy["type"] = "normal"
                break
    #boost timer
    if player_boost_speed and time.time()>boost_end_time:
        player_boost_speed=False
        move_speed = 40
        print("Player Speed boost ended")
    if enemy_nerf and time.time()>enemy_slow_time:
        enemy_nerf = False
        enemy_speed=0.3
        print("Enemy Slow effect ended")

    #move enemies toward player
    for enemy in enemy_li:
        if enemy["alive"] == False:
            continue
        #enemy at center so
        enemy_center_x = enemy["x"]
        enemy_center_y = enemy["y"] + 300
        enemy_center_z = enemy["z"] + 50*enemy_scale_factor
        #player center-enemy center
        dx = player_x - enemy_center_x
        dy = player_y - enemy_center_y
        dz = player_z - enemy_center_z
        #eucledian dist
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)

        spd = enemy_speed
        if enemy["type"]=="fast":
            spd *= 2.5
        if enemy["type"]=="tank":
            spd *= 0.5
        enemy["x"] += (dx/dist) * spd
        enemy["y"] += (dy/dist) * spd
            

        #enemy-player collision check
        if dist < 150: #hit
            life -= 1
            if life <= 0:
                game_over = True
            enemy["alive"] = False
            #respawn if hit
            enemy["x"] = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
            enemy["y"] = random.randint(-GRID_LENGTH+100, GRID_LENGTH-100)
            enemy["z"] = 0

            #upgrade
            if tower_height >= 8:
                enemy["type"] = random.choice(["normal", "fast", "tank"])
            elif tower_height >= 4:
                enemy["type"] = random.choice(["normal", "fast"])
            else:
                enemy["type"] = "normal"

        #will add enemy being drawn to the tower if game doesn't get to hard already
        #halka tweak lagbe, but same/easier as the tower is static

        # enemy-tower collision
        if abs(enemy_center_x) < 50 and abs(enemy_center_y) < 50:
            if enemy["type"] == "tank":
                tower_height = max(0, tower_height - 4)
            else:
                tower_height = max(0, tower_height - 1)

            enemy["alive"] = False
            if tower_height < 0:
                game_over = True
    if tower_height >= target_height:
        game_over = True
        print("You Won! Tower Completed.")


def keyboardListener(key, x, y):
    global player_x, player_y, player_z, player_angle, GRID_LENGTH, life, score, bullet_li, game_over, cam_rotate
    global tower_height,brick_li,powerup_li,move_speed
    
    if key == b'w' and game_over == False:  # forward
        new_x = player_x + move_speed*math.sin(math.radians(player_angle))
        new_y = player_y - move_speed*math.cos(math.radians(player_angle))
        #obj collision check
        if not is_colliding_with_obstacles(new_x, new_y, radius=30):
            player_x = new_x
            player_y = new_y

    elif key == b's' and game_over == False:  # backward
        new_x = player_x - move_speed*math.sin(math.radians(player_angle))
        new_y = player_y + move_speed*math.cos(math.radians(player_angle))
        #obj collision check
        if not is_colliding_with_obstacles(new_x, new_y, radius=10):
            player_x = new_x
            player_y = new_y

    elif key == b'a' and game_over == False:  #rotate left
        player_angle += 10
        if player_angle >= 360:
            player_angle -= 360 #resets to 0

    elif key == b'd' and game_over == False:  #rotate right
        player_angle -= 10
        if player_angle < 0:
            player_angle += 360 #same

    if key == b'r':  #restart
        life = 5
        score = 0
        bullet_li = []
        game_over = False
        make_enemy()   #respawn
        tower_height = 0
        brick_li = []
        powerup_li = []
        make_bricks()
        player_x, player_y, player_z, player_angle = 0, 0, 0, 0

    #keep player within boundary (based on feet movements)
    if player_x < -GRID_LENGTH:
        player_x = -GRID_LENGTH
    if player_x > GRID_LENGTH:
        player_x = GRID_LENGTH
    if player_y < -GRID_LENGTH:
        player_y = -GRID_LENGTH
    if player_y > GRID_LENGTH:
        player_y = GRID_LENGTH

    glutPostRedisplay()



def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for adjusting the camera angle and height.
    """
    global camera_pos
    cam_x, cam_y, cam_z = camera_pos

    # Arrow keys move the camera
    if key == GLUT_KEY_UP:
        cam_y -= 10
    elif key == GLUT_KEY_DOWN:
        cam_y += 10
    elif key == GLUT_KEY_LEFT:
        cam_x += 10
    elif key == GLUT_KEY_RIGHT:
        cam_x -= 10

    camera_pos = (cam_x, cam_y, cam_z)
    glutPostRedisplay()

def mouseListener(button, state, x, y):
    global fpp
    """
    Handles mouse inputs for firing bullets (left click) and toggling camera mode (right click).
    """
    # # Left mouse button fires a bullet
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and game_over == False:
        shoot_bullet()

    # # Right mouse button toggles camera tracking mode
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        fpp = not fpp


def setupCamera():
    global screen_width, screen_height, fpp, scale_factor, player_angle,fovY, camera_pos
    """
    Configures the camera's projection and view settings.
    Uses a perspective projection and positions the camera to look at the target.
    """
    glMatrixMode(GL_PROJECTION)  # Switch to projection matrix mode
    glLoadIdentity()  # Reset the projection matrix
    # Set up a perspective projection (field of view, aspect ratio, near clip, far clip)
    aspect_ratio = screen_width/screen_height
    if day_night == "day":
        far_plane = 2500
    else:
        far_plane = 600
        fovY = 80
    if fpp:
        gluPerspective(fovY, aspect_ratio, 0.1, far_plane)
    else:
        gluPerspective(fovY, aspect_ratio, 0.1, far_plane) #fov, ratio, closest obj, farthest obj
    glMatrixMode(GL_MODELVIEW)  # Switch to model-view matrix mode
    glLoadIdentity()  # Reset the model-view matrix

    # Extract camera position and look-at target
    if fpp:
        cam_pos_x = player_x
        cam_pos_y = player_y+10 #behind
        cam_pos_z = player_z + 150*scale_factor #top

        look_at_x = player_x + math.sin(math.radians(player_angle)) * 100
        look_at_y = player_y - math.cos(math.radians(player_angle)) * 100
        look_at_z = player_z + 150*scale_factor

    else:
        cam_pos_x, cam_pos_y, cam_pos_z = camera_pos
        dist = 150  # how far behind
        height = 170  # how high above

        cam_pos_x += player_x - math.sin(math.radians(player_angle)) * dist
        cam_pos_y += player_y + math.cos(math.radians(player_angle)) * dist
        cam_pos_z += player_z + height

        # look at the player
        look_at_x = player_x
        look_at_y = player_y
        look_at_z = player_z + 100  # center on player body

    gluLookAt(cam_pos_x, cam_pos_y, cam_pos_z,
            look_at_x, look_at_y, look_at_z,
            0, 0, 1)


def idle(): #runs continuously
    animate()
    make_powerup()            # spawn powerups over time
    check_powerup_collection()
    check_brick_collection()
    glutPostRedisplay()
    glutPostRedisplay()


def showScreen():
    global life, score,cell_size,cells
    """
    Display function to render the game scene:
    - Clears the screen and sets up the camera.
    - Draws everything of the screen
    """
    global day_night, last_day_switch
    now=time.time()
    if now-last_day_switch>30: #30s
        if day_night == "day":
            day_night = "night"
        else:
            day_night = "day"
        last_day_switch=now #reset

    if day_night=="day":
        glClearColor(0.529, 0.808, 0.922, 1) # bright sky
    else:
        glClearColor(0,0,0.2,1) # dark night
        glViewport(0, 0, screen_width, screen_height)


    # Clear color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
 
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, screen_width, screen_height)  # Set viewport size

    setupCamera()  # Configure camera perspective

    barrier_height = 200
    #top barrier --> -Y
    glBegin(GL_QUADS)
    glColor3f(0,0,0)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, barrier_height)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, barrier_height)
    glEnd()

    #bot barrier --> +Y
    glBegin(GL_QUADS)

    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)          # bottom-left
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)           # bottom-right
    glVertex3f(GRID_LENGTH, GRID_LENGTH, barrier_height) # top-right
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, barrier_height) # top-left
    glEnd()

    #left barrier --> +X
    glBegin(GL_QUADS)
 
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, barrier_height)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, barrier_height)
    glEnd()

    #right barrier --> -X
    glBegin(GL_QUADS)
   
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, barrier_height)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, barrier_height)
    glEnd()

    # Draw the grid (game floor)
    glBegin(GL_QUADS)
    for row in range(cells):
        for column in range(cells):

            #building block
            center_row = cells // 2
            center_col = cells // 2
            if row == center_row and column == center_col:
                glColor3f(0.5, 0.0, 0.0)  # dark maroon
            #color alternate
            else:
                if (row + column) % 2 != 0:
                    glColor3f(0.0, 0.39, 0.0)
                if (row + column) % 2 == 0:
                    glColor3f(0.0, 0.27, 0.0)

            #satrts from (-GRID_LENGTH, -GRID_LENGTH) - top-right corner (-x,-y,0)
            x0 = -GRID_LENGTH + row*cell_size
            y0 = -GRID_LENGTH + column*cell_size

            #bot-left corner of each cell (x,y,0)
            x1 = x0 + cell_size
            y1 = y0 + cell_size

            #draw one quad (z plane)
            #drawing starts from top right --> top left
            #starts with purple then white .....
            glVertex3f(x1, y1, 0) #bot-left
            glVertex3f(x0, y1, 0) #bot-right
            glVertex3f(x0, y0, 0) #top-right
            glVertex3f(x1, y0, 0) #top-left
    glEnd()
    #20 px right, 200 px down from top-left
    draw_text(-screen_width/2 + 20, screen_height/2- 200, f"Player Life Remaining: {life}")
    #20 px right, 180 px down from top-left
    draw_text(-screen_width/2 + 20, screen_height/2- 180, f"Bullets Left: {max_bullets - len(bullet_li)}")
    #20 px right, 160 px down from top-left
    draw_text(-screen_width/2 + 20, screen_height/2- 160, f"Tower Height: {tower_height}")
    draw_shapes()

    glutSwapBuffers()
    

# Main function to set up OpenGL window and loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1200,700)  # Window size
    glutInitWindowPosition(0,0)  # Window position top left
    wind = glutCreateWindow(b"Brickocalypse")  # Create the window

    glEnable(GL_DEPTH_TEST)

    glutDisplayFunc(showScreen)  # Register display function
    glutKeyboardFunc(keyboardListener)  # Register keyboard listener
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)  # Register the idle function to move the bullet automatically
    make_obstacles(50,30)
    make_bricks()
    make_enemy() #instant spawn
    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
