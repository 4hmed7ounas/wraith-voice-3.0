from flask import Flask, request, jsonify
from gpiozero import PWMOutputDevice, OutputDevice, Button, DistanceSensor, AngularServo
from time import sleep, time
import threading
import fcntl, struct, socket, sys, signal

app = Flask(__name__)

# ——— Motor A Control Pins (BTS7960) ———
RPWM_A = PWMOutputDevice(18)
LPWM_A = PWMOutputDevice(23)
REN_A = OutputDevice(24)
LEN_A = OutputDevice(25)

# ——— Motor B Control Pins (BTS7960) ———
RPWM_B = PWMOutputDevice(22)
LPWM_B = PWMOutputDevice(27)
REN_B = OutputDevice(5)
LEN_B = OutputDevice(6)

# ——— Encoder Pins ———
ENC_A_A = Button(17, bounce_time=0.005)
ENC_A_B = Button(4)
ENC_B_A = Button(19, bounce_time=0.005)
ENC_B_B = Button(13)

# ——— Distance Sensor & Servo (for auto mode) ———
sensor = DistanceSensor(echo=21, trigger=20)
servo = AngularServo(12, min_angle=-85, max_angle=85,
                     min_pulse_width=0.0005, max_pulse_width=0.0025)

# ——— Specs & Globals ———
PULSES_PER_REV = 500
WHEEL_CIRCUMFERENCE_CM = 20.42

tick_count_A = tick_count_B = 0
direction_A = direction_B = 1
lock_A = threading.Lock()
lock_B = threading.Lock()

current_speed = 0.3
obstacle_threshold = 20  # cm
auto_mode = False
auto_thread = None

# ——— Encoder Callbacks ———
def on_encoder_tick_A():
    global tick_count_A, direction_A
    direction_A = 1 if ENC_A_B.value == 0 else -1
    with lock_A:
        tick_count_A += direction_A

def on_encoder_tick_B():
    global tick_count_B, direction_B
    direction_B = 1 if ENC_B_B.value == 0 else -1
    with lock_B:
        tick_count_B += direction_B

ENC_A_A.when_pressed = on_encoder_tick_A
ENC_B_A.when_pressed = on_encoder_tick_B

# ——— Motor primitives ———
def set_motor_A(speed):
    speed = max(min(speed, 1.0), -1.0)
    if speed > 0:
        LPWM_A.value = 0; RPWM_A.value = speed
    elif speed < 0:
        RPWM_A.value = 0; LPWM_A.value = abs(speed)
    else:
        RPWM_A.value = LPWM_A.value = 0

def set_motor_B(speed):
    speed = max(min(speed, 1.0), -1.0)
    if speed > 0:
        LPWM_B.value = 0; RPWM_B.value = speed
    elif speed < 0:
        RPWM_B.value = 0; LPWM_B.value = abs(speed)
    else:
        RPWM_B.value = LPWM_B.value = 0

def enable_motors():
    REN_A.on(); LEN_A.on()
    REN_B.on(); LEN_B.on()

def disable_motors():
    RPWM_A.value = LPWM_A.value = 0
    REN_A.off(); LEN_A.off()
    RPWM_B.value = LPWM_B.value = 0
    REN_B.off(); LEN_B.off()

# ——— Movement funcs matching old API ———
def move_forward(speed): set_motor_A(speed); set_motor_B(speed)
def move_backward(speed): set_motor_A(-speed); set_motor_B(-speed)
def move_left(speed): set_motor_A(-speed); set_motor_B(speed)
def move_right(speed): set_motor_A(speed); set_motor_B(-speed)
def stop_motors(): set_motor_A(0); set_motor_B(0)

def increase_speed():
    global current_speed
    current_speed = min(current_speed + 0.1, 1.0)
    return current_speed

def decrease_speed():
    global current_speed
    current_speed = max(current_speed - 0.1, 0.0)
    return current_speed

# ——— Smooth Servo Sweep ———
def sweep_servo(target, step=5, delay=0.03):
    target = max(-85, min(85, target))
    cur = int(servo.angle or 0)
    rng = range(cur, target+1, step) if target>cur else range(cur, target-1, -step)
    for a in rng:
        servo.angle = max(-85, min(85, a))
        sleep(delay)

# ——— Auto Mode Logic ———
def auto_mode_function():
    global auto_mode
    enable_motors()
    while auto_mode:
        try:
            sweep_servo(0)
            front = sensor.distance * 100
            if front < obstacle_threshold:
                stop_motors()
                # scan right
                sweep_servo(85); right = sensor.distance*100
                # scan left
                sweep_servo(-85); left = sensor.distance*100
                sweep_servo(0)
                move_backward(current_speed); sleep(0.5); stop_motors()
                if right > left: move_right(current_speed)
                else:             move_left(current_speed)
                sleep(0.6); stop_motors()
            else:
                move_forward(current_speed)
            sleep(0.1)
        except Exception:
            stop_motors()
    disable_motors()

# ——— IP helper ———
def get_ip_address(ifname='wlan0'):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = fcntl.ioctl(
        s.fileno(), 0x8915,
        struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24]
    return socket.inet_ntoa(ip)

# ——— Flask Routes ———
@app.route('/', methods=['GET'])
def index(): return 'AutoCar API Online\n'

@app.route('/get_ip', methods=['GET'])
def get_ip(): return jsonify({'ip': get_ip_address()})

@app.route('/get_distance', methods=['GET'])
def get_distance(): return jsonify({'distance': round(sensor.distance*100,2)})

@app.route('/control', methods=['POST'])
def control():
    global auto_mode, auto_thread
    cmd = request.data.decode().strip()
    # auto
    if cmd == 'auto_start':
        if not auto_mode:
            auto_mode = True
            auto_thread = threading.Thread(target=auto_mode_function, daemon=True)
            auto_thread.start()
            return 'Auto mode started\n'
        return 'Already in auto mode\n'
    if cmd == 'auto_stop':
        if auto_mode:
            auto_mode = False
            auto_thread.join()
            return 'Auto mode stopped\n'
        return 'Auto mode not active\n'
    # manual
    actions = {
        'forward_start': lambda: move_forward(current_speed),
        'forward_stop': stop_motors,
        'backward_start': lambda: move_backward(current_speed),
        'backward_stop': stop_motors,
        'left_start': lambda: move_left(current_speed),
        'left_stop': stop_motors,
        'right_start': lambda: move_right(current_speed),
        'right_stop': stop_motors,
        'speed+': increase_speed,
        'speed-': decrease_speed
    }
    if cmd in actions:
        actions[cmd]()
        return f'{cmd} executed\n'
    return 'Unknown command\n', 400

# ——— Graceful shutdown ———
def cleanup(sig, frame):
    global auto_mode
    auto_mode = False
    disable_motors()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ——— Main ———
if __name__ == '__main__':
    enable_motors()
    app.run(host='0.0.0.0', port=5000)
