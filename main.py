# Web streaming example
# Source code from the official PiCamera package
# http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming

import io
import os
import picamera
import logging
import socketserver
import RPi.GPIO as GPIO
from html import unescape
from threading import Condition
from http import server
from datetime import datetime

HORAINI=9
HORAFIM=13
XSENHA='alohomora'

PAGE="""\
<html>
<head>
<meta charset="UTF-8">
<title>Bonsai Lindão</title>
</head>
<body>
<center><h1>Bonsai Lindão</h1></center>
<center><img src="streammalucocabecao.mjpg" width="640" height="480"></center>
           <form action="/" method="POST">
               Irrigar :
               <p><input type="password" name="senha" value=""></p>
               <p><input type="submit" name="submit" value="On"></p>
               <p><input type="submit" name="submit" value="Off"></p>
           </form>
</body>
</html>
"""

OUTTIME="""\
<html>
<head>
<meta charset="UTF-8">
<title>Bonsai Lindão</title>
</head>
<body>
<center><h1>Volte no horario combinado...</h1></center>
<center><img src="streammalucocabecao.mjpg" width="640" height="480"></center>
</body>
</html>
"""

def setupGPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(18, GPIO.OUT)
    GPIO.setup(23, GPIO.OUT)
    GPIO.setup(24, GPIO.OUT)
    GPIO.output(18, GPIO.LOW)
    GPIO.output(23, GPIO.HIGH)
    GPIO.output(24, GPIO.HIGH)

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()


    def do_POST(self):
        dt = datetime.now()
        intDt = int(dt.strftime("%H"))
        if intDt >= HORAINI and intDt <= HORAFIM:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode("utf-8")

            senha = post_data.split("=")[1]
            senha = senha.replace('&submit','').replace('%40','@').replace('%21','!')
            stateRelay = post_data.split("=")[2]

            setupGPIO()
            if stateRelay == 'On':
                if senha == XSENHA:
                    GPIO.output(18, GPIO.HIGH)
                    GPIO.output(23, GPIO.LOW)
                    GPIO.output(24, GPIO.LOW)
                else:
                    self.send_error(403)
                    self.end_headers()

            elif stateRelay == 'Off':
                GPIO.output(18, GPIO.LOW)
                GPIO.output(23, GPIO.HIGH)
                GPIO.output(24, GPIO.HIGH)

            print('Pin23 is ',GPIO.input(23))
            print('Pin24 is ',GPIO.input(24))
            print('Pin18 is ',GPIO.input(18))
            self._redirect('/iniciocrazyinnn')  # Redirect back to the root url
        self.send_error(404)
        self.end_headers()

    def do_GET(self):
        if self.path == '/iniciocrazyinnn':
            self.send_response(301)
            self.send_header('Location', '/inicioindexxpto.html')
            self.end_headers()
        elif self.path == '/inicioindexxpto.html':
            dt = datetime.now()
            intDt = int(dt.strftime("%H"))
            if intDt >= HORAINI and intDt <= HORAFIM:
                content = PAGE.encode('utf-8')
            else:
                content = OUTTIME.encode('utf-8')
            # content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/reiniciarmalcooeo':
            os.system('sudo reboot')
        elif self.path == '/streammalucocabecao.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()



class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='1920x1080', framerate=30) as camera:
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    camera.rotation = 270
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('0.0.0.0', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
