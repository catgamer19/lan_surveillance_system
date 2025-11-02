from flask import Flask, render_template, Response, request, redirect, session
from flask_socketio import SocketIO, emit
import cv2, threading, time, pygame, pyttsx3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'MR-A-TACTICAL-KEY-2024'
socketio = SocketIO(app)

# Config
PASSWORD = "11115"
COUNTDOWN_TIME = 10
MOTION_THRESHOLD = 3000
ALARM_COOLDOWN = 30

# State
camera = None
countdown_active = False
alarm_defused = False
last_trigger = 0
detection_armed = False

# Audio
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)
pygame.mixer.init()

def play_alarm():
    try:
        pygame.mixer.music.load('static/sounds/alarm.wav')
        pygame.mixer.music.play(-1)
    except:
        pass

def speak_defused():
    try:
        tts_engine.say("Alarm defused. System secured.")
        tts_engine.runAndWait()
    except:
        pass

def run_countdown():
    global countdown_active, alarm_defused
    socketio.emit('countdown', {'seconds': COUNTDOWN_TIME})
    try:
        tts_engine.say("Motion detected. Enter password before alarm.")
        tts_engine.runAndWait()
    except:
        pass

    for i in range(COUNTDOWN_TIME, 0, -1):
        if alarm_defused:
            socketio.emit('alarm_defused', {'status': 'DEFUSED'})
            countdown_active = False
            return
        socketio.emit('countdown', {'seconds': i})
        try:
            tts_engine.say(str(i))
            tts_engine.runAndWait()
        except:
            pass
        time.sleep(1)

    if not alarm_defused:
        try:
            tts_engine.say("ALARM ACTIVATED!")
            tts_engine.runAndWait()
        except:
            pass
        threading.Thread(target=play_alarm, daemon=True).start()
        socketio.emit('alarm_triggered', {'status': 'ACTIVE'})
    countdown_active = False
    alarm_defused = False

class MotionDetector:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.prev_frame = None

    def detect_motion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if self.prev_frame is None:
            self.prev_frame = gray
            return False, frame
        delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        motion = False
        for c in contours:
            if cv2.contourArea(c) > MOTION_THRESHOLD:
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                motion = True
        self.prev_frame = gray
        return motion, frame

    def start_countdown(self):
        global countdown_active, last_trigger
        now = time.time()
        if not countdown_active and (now - last_trigger > ALARM_COOLDOWN):
            countdown_active = True
            last_trigger = now
            threading.Thread(target=run_countdown, daemon=True).start()

    def get_frame(self):
        success, frame = self.cap.read()
        if success:
            motion, processed = self.detect_motion(frame)
            if motion and detection_armed and not alarm_defused:
                self.start_countdown()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cv2.putText(processed, timestamp, (10, processed.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', processed)
            return buffer.tobytes()
        return None

@app.route('/')
def index():
    if 'authenticated' not in session:
        return redirect('/security')
    return render_template('dashboard.html')

@app.route('/security', methods=['GET', 'POST'])
def security():
    global alarm_defused, detection_armed
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD:
            alarm_defused = True
            detection_armed = False
            threading.Thread(target=speak_defused, daemon=True).start()
            try:
                pygame.mixer.music.stop()
            except:
                pass
            socketio.emit('alarm_defused', {'status': 'DEFUSED'})
            session['authenticated'] = True
            return redirect('/')
        else:
            return render_template('login.html', error="ACCESS DENIED")
    return render_template('login.html')

@app.route('/start_detection', methods=['POST'])
def start_detection():
    global detection_armed, alarm_defused, countdown_active
    detection_armed = True
    alarm_defused = False
    countdown_active = False
    socketio.emit('detection_started', {'status': 'armed'})
    return redirect('/')

@app.route('/manual_alarm', methods=['POST'])
def manual_alarm():
    threading.Thread(target=play_alarm, daemon=True).start()
    socketio.emit('alarm_triggered', {'source': 'manual'})
    return redirect('/')

@app.route('/stop_alarm', methods=['POST'])
def stop_alarm():
    global alarm_defused, detection_armed
    alarm_defused = True
    detection_armed = False
    try:
        pygame.mixer.music.stop()
    except:
        pass
    socketio.emit('alarm_defused', {'status': 'MANUAL STOP'})
    return redirect('/')

@app.route('/raw_feed')
def raw_feed():
    def generate_raw():
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        while True:
            success, frame = cap.read()
            if not success:
                break
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return Response(generate_raw(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed')
def video_feed():
    if 'authenticated' not in session:
        return redirect('/security')
    def generate():
        global camera
        if camera is None:
            camera = MotionDetector()
        while True:
            frame = camera.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5050)
