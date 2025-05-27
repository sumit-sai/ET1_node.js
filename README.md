# 🤖 ET1 – Web-Controlled Autonomous Robot  
**Embedded Computing Task 3 Remote Control**

## 📖 Overview
**ET1** is a Raspberry Pi-powered autonomous robot system that can be controlled via a browser-based interface. The task demonstrate control of ET1 through webUI and node.js to perform various tasks such as obstacle detection, reverse turning, and looped behavior — 

---

## 📸 Features
- ✅ Forward motion with ultrasonic obstacle detection (HC-SR04)
- 🔄 Auto-reverse with randomized turn direction
- 🔁 Loop mode for repeated autonomous behavior
- 🌐 Web UI to trigger and monitor robot actions
- 📊 updates on obstacle distance sensors, wheel travel distance values, and action logs

---

## 🗂️ Project Structure
```
project/
├── public/
│ ├── index.html # Web interface
│ └── styles.css # UI styling
├── scripts/
│ ├── move_forward_until_obstacle.py
│ ├── move_backwards_random_turn.py
├── webserver.js # Node.js server with socket.io integration
└── README.md # Project documentation
```

## ▶️ Run the Web Server
From the project directory:
```bash
sudo node webserver.js
```
## 🌐 Access the Interface
Visit in browser:
```bash
http://localhost:8080
```
