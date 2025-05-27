import RPi.GPIO as GPIO
from gpiozero import DistanceSensor
import time
import json
import sys

# === Configuration ===
BASE_DUTY_CYCLE = 50
DISTANCE_STOP_CM = 25           # Increased stop distance for safety
SLOWDOWN_START_CM = 60          # Start slowing down before stop distance
MIN_DUTY_CYCLE = 30             # Minimum speed when slowing down
MAX_RUNTIME = 15                # Failsafe timeout in seconds

# PID parameters — tune these for your robot
Kp = 2.0
Ki = 0.1
Kd = 0.05

# === Pin Definitions ===
Motor1_PWM = 18
Motor1_IN1 = 17
Motor1_IN2 = 22
Motor2_PWM = 19
Motor2_IN1 = 24
Motor2_IN2 = 4
sensor_left = 16
sensor_right = 23

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# === Setup ===
GPIO.setup([Motor1_IN1, Motor1_IN2, Motor1_PWM, Motor2_IN1, Motor2_IN2, Motor2_PWM], GPIO.OUT)
GPIO.setup(sensor_left, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(sensor_right, GPIO.IN, pull_up_down=GPIO.PUD_UP)

PWM_1 = GPIO.PWM(Motor1_PWM, 90)
PWM_2 = GPIO.PWM(Motor2_PWM, 90)
PWM_1.start(0)
PWM_2.start(0)

sensor = DistanceSensor(echo=27, trigger=25)

left_encoder_count = 0
right_encoder_count = 0

pid_integral = 0
pid_last_error = 0

def left_callback(channel):
    global left_encoder_count
    left_encoder_count += 1

def right_callback(channel):
    global right_encoder_count
    right_encoder_count += 1

GPIO.add_event_detect(sensor_left, GPIO.FALLING, callback=left_callback, bouncetime=2)
GPIO.add_event_detect(sensor_right, GPIO.FALLING, callback=right_callback, bouncetime=2)

def M1_forward():
    GPIO.output(Motor1_IN1, GPIO.HIGH)
    GPIO.output(Motor1_IN2, GPIO.LOW)

def M2_forward():
    GPIO.output(Motor2_IN1, GPIO.HIGH)
    GPIO.output(Motor2_IN2, GPIO.LOW)

def M1_backward():
    GPIO.output(Motor1_IN1, GPIO.LOW)
    GPIO.output(Motor1_IN2, GPIO.HIGH)
    
def M2_backward():
    GPIO.output(Motor2_IN1, GPIO.LOW)
    GPIO.output(Motor2_IN2, GPIO.HIGH)

def stop_motors():
    GPIO.output(Motor1_IN1, GPIO.LOW)
    GPIO.output(Motor1_IN2, GPIO.LOW)
    GPIO.output(Motor2_IN1, GPIO.LOW)
    GPIO.output(Motor2_IN2, GPIO.LOW)

def brake(duration=0.1):
    M1_backward()
    M2_backward()
    PWM_1.ChangeDutyCycle(BASE_DUTY_CYCLE)
    PWM_2.ChangeDutyCycle(BASE_DUTY_CYCLE)
    time.sleep(duration)
    stop_motors()

def pid_control(error, dt):
    global pid_integral, pid_last_error
    pid_integral += error * dt
    derivative = (error - pid_last_error) / dt if dt > 0 else 0
    output = Kp * error + Ki * pid_integral + Kd * derivative
    pid_last_error = error
    return output

try:
    # Start moving forward
    M1_forward()
    M2_forward()
    PWM_1.ChangeDutyCycle(BASE_DUTY_CYCLE)
    PWM_2.ChangeDutyCycle(BASE_DUTY_CYCLE)

    start_time = time.time()
    last_left = left_encoder_count
    last_right = right_encoder_count

    while time.time() - start_time < MAX_RUNTIME:
        distance_cm = sensor.distance * 100

        # Sensor failure or out-of-range check
        if distance_cm == 0.0 or distance_cm > 500:
            print("Sensor error or out of range. Stopping.",file=sys.stderr)
            brake()
            break

        # Emergency reverse if too close
        if distance_cm < 5:
            print("Too close to object. Reversing slightly.",file=sys.stderr)
            M1_backward()
            M2_backward()
            PWM_1.ChangeDutyCycle(BASE_DUTY_CYCLE)
            PWM_2.ChangeDutyCycle(BASE_DUTY_CYCLE)
            time.sleep(0.3)
            stop_motors()
            break

        if distance_cm <= DISTANCE_STOP_CM:
            print("Stop threshold reached.",file=sys.stderr)
            break

        # Calculate slowdown speed
        if distance_cm < SLOWDOWN_START_CM:
            slowdown_range = SLOWDOWN_START_CM - DISTANCE_STOP_CM
            distance_to_stop = distance_cm - DISTANCE_STOP_CM
            base_speed = MIN_DUTY_CYCLE + ((distance_to_stop / slowdown_range) * (BASE_DUTY_CYCLE - MIN_DUTY_CYCLE))
            base_speed = max(MIN_DUTY_CYCLE, min(base_speed, BASE_DUTY_CYCLE))
        else:
            base_speed = BASE_DUTY_CYCLE

        # PID control to balance left/right motor speeds
        error = left_encoder_count - right_encoder_count
        current_time = time.time()
        dt = current_time - pid_control.last_time if hasattr(pid_control, 'last_time') else 0.01
        pid_control.last_time = current_time

        pid_output = pid_control(error, dt)

        left_speed = base_speed - pid_output
        right_speed = base_speed + pid_output

        left_speed = max(MIN_DUTY_CYCLE, min(BASE_DUTY_CYCLE, left_speed))
        right_speed = max(MIN_DUTY_CYCLE, min(BASE_DUTY_CYCLE, right_speed))

        PWM_1.ChangeDutyCycle(left_speed)
        PWM_2.ChangeDutyCycle(right_speed)

        # Detect stalled movement
        if left_encoder_count == last_left and right_encoder_count == last_right:
            print("No movement detected. Stopping.",file=sys.stderr)
            brake()
            break

        last_left = left_encoder_count
        last_right = right_encoder_count

        time.sleep(0.1)

    brake()
    time.sleep(0.3)

except KeyboardInterrupt:
    pass

finally:
    # Always print JSON output at the end
    final_distance = sensor.distance * 100
    print(json.dumps({
        "distance": round(final_distance, 1),
        "left": left_encoder_count,
        "right": right_encoder_count
    }))

    PWM_1.stop()
    PWM_2.stop()
    GPIO.cleanup()
