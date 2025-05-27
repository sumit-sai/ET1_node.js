import RPi.GPIO as GPIO
import time
import random
import json

# === Configuration ===
BASE_DUTY_CYCLE = 50
ENCODER_COUNTS_PER_CM = 1   # <-- Adjust based on your encoder and wheel size
BACKWARD_DISTANCE_CM = 20
SLOWDOWN_ADJUSTMENT = 5

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

left_encoder_count = 0
right_encoder_count = 0

def left_callback(channel):
    global left_encoder_count
    left_encoder_count += 1

def right_callback(channel):
    global right_encoder_count
    right_encoder_count += 1

GPIO.add_event_detect(sensor_left, GPIO.FALLING, callback=left_callback, bouncetime=2)
GPIO.add_event_detect(sensor_right, GPIO.FALLING, callback=right_callback, bouncetime=2)

def M1_backward():
    GPIO.output(Motor1_IN1, GPIO.LOW)
    GPIO.output(Motor1_IN2, GPIO.HIGH)

def M2_backward():
    GPIO.output(Motor2_IN1, GPIO.LOW)
    GPIO.output(Motor2_IN2, GPIO.HIGH)

def M1_forward():
    GPIO.output(Motor1_IN1, GPIO.HIGH)
    GPIO.output(Motor1_IN2, GPIO.LOW)

def M2_forward():
    GPIO.output(Motor2_IN1, GPIO.HIGH)
    GPIO.output(Motor2_IN2, GPIO.LOW)

def stop_motors():
    GPIO.output(Motor1_IN1, GPIO.LOW)
    GPIO.output(Motor1_IN2, GPIO.LOW)
    GPIO.output(Motor2_IN1, GPIO.LOW)
    GPIO.output(Motor2_IN2, GPIO.LOW)

def brake():
    stop_motors()
    time.sleep(0.2)

def turn_random_angle():
    angle = random.randint(30, 180)
    turn_time = angle / 90.0 * 0.5  # Assume 0.5s for 90° turn, adjust as needed

    # Turn in place (left motor forward, right motor backward)
    M1_forward()
    M2_backward()
    PWM_1.ChangeDutyCycle(BASE_DUTY_CYCLE)
    PWM_2.ChangeDutyCycle(BASE_DUTY_CYCLE)

    time.sleep(turn_time)
    stop_motors()
    return angle

try:
    # === Move Backward ===
    M1_backward()
    M2_backward()
    PWM_1.ChangeDutyCycle(BASE_DUTY_CYCLE)
    PWM_2.ChangeDutyCycle(BASE_DUTY_CYCLE)

    while (left_encoder_count + right_encoder_count) / 2 < BACKWARD_DISTANCE_CM * ENCODER_COUNTS_PER_CM:
        if left_encoder_count > right_encoder_count:
            PWM_1.ChangeDutyCycle(BASE_DUTY_CYCLE - SLOWDOWN_ADJUSTMENT)
            PWM_2.ChangeDutyCycle(BASE_DUTY_CYCLE)
        elif right_encoder_count > left_encoder_count:
            PWM_2.ChangeDutyCycle(BASE_DUTY_CYCLE - SLOWDOWN_ADJUSTMENT)
            PWM_1.ChangeDutyCycle(BASE_DUTY_CYCLE)
        else:
            PWM_1.ChangeDutyCycle(BASE_DUTY_CYCLE)
            PWM_2.ChangeDutyCycle(BASE_DUTY_CYCLE)
        time.sleep(0.01)

    brake()

    

    # === Output result ===
    
    print(json.dumps({
        "status": "done",
        "left": left_encoder_count,
        "right": right_encoder_count,
            
    }))
    
    # === Turn Random Angle ===
    angle = turn_random_angle()

except KeyboardInterrupt:
    pass

finally:
    PWM_1.stop()
    PWM_2.stop()
    GPIO.cleanup()
