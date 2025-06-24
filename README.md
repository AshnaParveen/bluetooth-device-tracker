# 🔵 Bluetooth Device Tracker

A desktop application for scanning, pairing, connecting, and tracking Bluetooth devices — with **real-time distance estimation** and **graphical monitoring**. Built using a **Flask backend**, **React frontend**, and packaged as a cross-platform app using **Electron**.

---

## ✨ Features

- 🔍 **Scan** nearby Bluetooth devices  
- 🤝 **Pair** and **connect** to selected devices  
- 📶 **Estimate distances** using RSSI + smoothing filters  
- 📊 **Live graph** of device proximity over time  
- 🔁 **Connect / Disconnect** and **Unpair** support  
- 📦 Packaged as `.deb` and `.AppImage` for easy installation on Raspberry Pi/Linux

---

## 🗂️ Folder Structure

```
bluetooth-app/
├── bluetooth-frontend/         # React frontend for UI
├── bluetooth-electron-app/     # Electron + Flask backend
│   ├── main.js                 # Electron main process
│   ├── bluet5.py               # Flask server for Bluetooth management
│   ├── venv/                   # Python virtual environment (not tracked)
│   └── requirements.txt        # Python dependencies
└── .gitignore                  # Excludes build artifacts & venv
```

---

## ⚙️ How to Run the App

### 1️⃣ Backend Setup (Python + Flask)

```bash
cd bluetooth-electron-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Frontend Setup (React)

```bash
cd ../bluetooth-frontend
npm install
npm run build
```

### 3️⃣ Run the App (Electron)

```bash
cd ../bluetooth-electron-app
npm start
```

> Make sure the Flask server (`bluet5.py`) is running in the background on port `5000`.

---

## 📏 Distance Estimation

Distance is estimated using Bluetooth RSSI signals with:
- 📉 **Median Smoothing** for noise reduction  
- 📈 **Kalman Filtering** (or UKF) for more accurate tracking  
- 💡 Sensor fusion techniques help stabilize proximity estimation in noisy environments

---

## 📦 Packaging

You can build your Electron app as `.deb` or `.AppImage`:

```bash
npm run dist
```

Then upload your installers in the [GitHub Releases](https://github.com/AshnaParveen/bluetooth-device-tracker/releases) section.

---

## 👩‍💻 Developer

**Ashna Parveen P. S.**  
`B.Tech - Rajagiri School of Engineering and Technology`

---
---

## ❗ License

This project is protected under an **All Rights Reserved** license.

You are allowed to:
- View the code publicly for educational or reference purposes.

You are **not allowed to**:
- Copy, reuse, modify, distribute, or publish this code (or any part of it)
- Use it in academic, personal, or commercial projects without **explicit written permission** from the author.

🔒 Unauthorized use is strictly prohibited.
📩 Contact **Ashna Parveen** for licensing inquiries.

