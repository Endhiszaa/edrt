import math
import threading
import time

from arena import dist_point_segment


class DroneAPI:
    RATE_HZ = 50.0
    MAX_SPEED = 3.0      #m/s horizontal
    MAX_VZ = 1.5         #m/s vertical
    MAX_YAW_RATE = 90.0  #deg/s
    POS_GAIN = 1.0       
    RADIUS = 0.3         #radius drone (m)

    def __init__(self, x=0.0, y=0.0, heading=90.0, walls=None):
        self.walls = walls or []
        self.crashed = False
        self.x = x
        self.y = y
        self.z = 0.0
        self.heading = heading
        self.armed = False
        self.mode = "GUIDED"
        self.trail = [(x, y)]

        self._cmd = ("vel", 0.0, 0.0, 0.0, 0.0)
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._sim_loop, daemon=True)
        self._thread.start()

    #sim
    def _sim_loop(self):
        dt = 1.0 / self.RATE_HZ
        while self._running:
            with self._lock:
                self._step(dt)
            time.sleep(dt)

    def _step(self, dt):
        if not self.armed:
            return

        if self.mode == "LAND":
            vx_l, vy_l, vz, yaw_rate = 0.0, 0.0, -0.7, 0.0
        elif self._cmd[0] == "vel":
            _, bvx, bvy, vz, yaw_rate = self._cmd
            vx_l, vy_l = self.body2local(bvx, bvy)
        else:
            _, tx, ty, tz, th = self._cmd
            vx_l = self.POS_GAIN * (tx - self.x)
            vy_l = self.POS_GAIN * (ty - self.y)
            vz = self.POS_GAIN * (tz - self.z)
            yaw_rate = 2.0 * self._wrap(th - self.heading)

        #clamp 
        speed = math.hypot(vx_l, vy_l)
        if speed > self.MAX_SPEED:
            vx_l *= self.MAX_SPEED / speed
            vy_l *= self.MAX_SPEED / speed
        vz = max(-self.MAX_VZ, min(self.MAX_VZ, vz))
        yaw_rate = max(-self.MAX_YAW_RATE, min(self.MAX_YAW_RATE, yaw_rate))

        #drone ga gerak di lantai
        if self.z <= 0.0 and vz <= 0.0:
            vx_l = vy_l = 0.0

        self.x += vx_l * dt
        self.y += vy_l * dt
        self.z = max(0.0, self.z + vz * dt)
        self.heading = self._wrap(self.heading + yaw_rate * dt)
        self.trail.append((self.x, self.y))

        if any(dist_point_segment(self.x, self.y, w) < self.RADIUS for w in self.walls):
            self.crashed = True
            self.armed = False
            self.z = 0.0
            print(f"[DroneAPI] CRASHED into a wall at ({self.x:.2f}, {self.y:.2f})")
            return

        if self.mode == "LAND" and self.z <= 0.0:
            self.armed = False
            print("[DroneAPI] Landed and disarmed")

    @staticmethod
    def _wrap(deg):
        return (deg + 180.0) % 360.0 - 180.0

    def body2local(self, bx, by):
        """Rotate a body-frame (forward, left) vector into the local (East, North) frame."""
        h = math.radians(self.heading)
        return (bx * math.cos(h) - by * math.sin(h),
                bx * math.sin(h) + by * math.cos(h))

    #state
    def get_pose(self):
        with self._lock:
            return {"x": self.x, "y": self.y, "z": self.z, "heading": self.heading}

    def set_mode(self, mode):
        with self._lock:
            self.mode = mode
        print(f"[DroneAPI] Mode -> {mode}")

    def wait4start(self):
        print("[DroneAPI] Mode is GUIDED, starting")

    def arm(self):
        with self._lock:
            self.armed = True
        print("[DroneAPI] Armed")
        return True

    def disarm(self):
        with self._lock:
            self.armed = False
        print("[DroneAPI] Disarmed")

    #movement
    def takeoff(self, alt=2.0, tol=0.1):
         if not self.armed:
            self.arm()
        with self._lock:
            self.mode = "GUIDED"
            self._cmd = ("pos", self.x, self.y, alt, self.heading)
        print(f"[DroneAPI] Taking off to {alt:.1f} m")
        while abs(self.get_pose()["z"] - alt) > tol:
            time.sleep(0.05)
        print("[DroneAPI] Takeoff complete")
        return True

    def land(self, block=True):
        self.set_mode("LAND")
        while block and self.armed:
            time.sleep(0.05)

    def move(self, x, y, z, heading=None):
        with self._lock:
            h = self.heading if heading is None else heading
            self._cmd = ("pos", x, y, z, h)

    def move_vel(self, velx=0.0, vely=0.0, velz=0.0):
        with self._lock:
            self._cmd = ("vel", velx, vely, velz, 0.0)

    def move_vel_yaw(self, velx=0.0, vely=0.0, velz=0.0, yaw_rate=0.0):
        with self._lock:
            self._cmd = ("vel", velx, vely, velz, yaw_rate)

    def move_yaw(self, deg, duration=None, tol=1.0):
        pose = self.get_pose()
        target = self._wrap(pose["heading"] + deg)
        with self._lock:
            self._cmd = ("pos", pose["x"], pose["y"], pose["z"], target)
        t0 = time.time()
        while abs(self._wrap(target - self.get_pose()["heading"])) > tol:
            if duration is not None and time.time() - t0 > duration:
                break
            time.sleep(0.05)

    def hover(self):
        p = self.get_pose()
        self.move(p["x"], p["y"], p["z"], p["heading"])

    def shutdown(self):
        self._running = False
