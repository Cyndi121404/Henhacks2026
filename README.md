# Hen-Tersection 🐔🚦

**Intelligent Crosswalk System** — Henhacks 2026

---

## Overview

Hen-Tersection is an AI-powered smart crosswalk system that reduces pedestrian wait times, enhances safety through automated signal adjustments, and provides inclusive crossing times for people with disabilities.

---

## Features

### 🎯 Live Pedestrian Monitoring
- Real-time computer vision using TensorFlow.js (COCO-SSD model)
- Detects and tracks pedestrians crossing the street
- Identifies mobility aids (wheelchairs, canes, umbrellas, bags)
- Flags and logs jaywalking violations with photo evidence

### 🚦 Adaptive Traffic Signal Control
- **Smart Queue Detection** — Triggers crossing earlier when pedestrians are waiting
- **Mobility Aid Extension** — Automatically adds extra crossing time for wheelchair/cane users
- **Jaywalker Response** — Triggers yellow light when pedestrians enter crosswalk during red
- **Early Clearance** — Ends walk phase early when crosswalk is clear
- **Peak Hour Boost** — Auto-increases crossing time during rush hours (7-9 AM, 5-7 PM)

### 🔊 Voice Announcements & Alerts
- Text-to-speech instructions for pedestrians
- Configurable messages for walk, warning, stop, and mobility-assist scenarios
- Adjustable speech rate and volume
- Visual countdown with animated signals

### 📊 Data Logging & Analytics
- **Snowflake Integration** — Persistent storage of crossing events and violations
- Event log with filtering (Normal / Mobility Aid / Jaywalkers)
- Statistics dashboard: crossings today, jaywalkers, mobility assists, average cross time
- CSV export for data analysis

### 🎮 Traffic Simulation
- Interactive traffic flow simulation
- Multiple view modes: Intersection, Horizontal Road, Vertical Road, Side-On Street View
- Real-time signal status and queue length display
- Configurable speed and traffic density

### ⚙️ Admin Settings
| Category | Options |
|----------|---------|
| **Timing** | Default crossing time, mobility extension, warning countdown, smart queue, slow crosser detection |
| **Detection** | Person detection threshold, mobility sensitivity, jaywalker logging |
| **Voice** | Enable/disable TTS, speech rate, volume, custom messages |
| **Zones** | Drag-and-drop crossing zone editor |
| **Signals** | Vehicle phases (red/yellow/green), pedestrian signal options |
| **Database** | Snowflake account configuration |

---

## Tech Stack

- **Frontend**: HTML5, CSS3 (custom dark theme), Vanilla JavaScript
- **AI/ML**: TensorFlow.js, COCO-SSD object detection model
- **Backend**: Python Flask + Snowflake connector
- **Database**: Snowflake (cloud data warehouse)

---

## Quick Start

### 1. Install Dependencies

Run the following commands in your terminal:

| Step | Action | Command |
|------|--------|---------|
| 1 | Check Python version | `python --version` |
| 2 | Install Snowflake connector | `pip install snowflake-connector-python` |
| 3 | Install Flask | `pip install flask` |
| 4 | Install Flask CORS | `pip install flask-cors` |

**Or install all at once:**
```
bash
pip install snowflake-connector-python flask flask-cors
```

### 2. Start the Backend Server

```
bash
python Hen-tersection.py
```

The server starts on `http://localhost:5050`

### 3. Open the Interface

Open `index.html` in a modern web browser (Chrome recommended).

---

## Project Structure

```
Henhacks2026/
├── index.html           # Main web interface (all pages)
├── Hen-tersection.py    # Flask backend + Snowflake integration
├── README.md            # This file
└── LICENSE              # MIT License
```

---

## Demo Features (Pre-loaded)

The interface comes with demo data seeded for testing:
- Sample crossing events (normal, mobility, jaywalk)
- Live camera feed (requires camera permission)
- Traffic simulation with cars, queues, and signal phases

---

## Screenshots

| Page | Description |
|------|-------------|
| **Live Monitor** | Real-time camera feed with AI detection, signal status, countdown timer |
| **Event Log** | Tabular view of all crossings and violations with filters |
| **Traffic Sim** | Animated intersection with vehicle flow and signal control |
| **Admin Settings** | Configuration panels for timing, detection, voice, zones, signals, DB |

## License

MIT License — See `LICENSE` file for details.

---

*Built with ❤️ for Henhacks 2026*
