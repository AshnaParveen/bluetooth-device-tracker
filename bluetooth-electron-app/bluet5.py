#!/usr/bin/env python3
import pexpect
import time
import re
import json
import math
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import numpy as np
from filterpy.kalman import UnscentedKalmanFilter as UKF
from filterpy.kalman import MerweScaledSigmaPoints

app = Flask(__name__)
CORS(app)

class BluetoothManager:
    def __init__(self):
        self.child = None
        self.connected_devices = {}
        self.discovered_devices = {}
        self.last_known_rssi = {}
        self.last_known_distance = {}
        self.device_filters = {}  # UKF filters per MAC
        self.lock = threading.Lock()
        self._start_monitor_thread()

    def _start_monitor_thread(self):
        def monitor():
            while True:
                with self.lock:
                    for mac, dev in self.connected_devices.items():
                        rssi = self.get_device_rssi(mac, allow_cache=True)
                        distance = self.estimate_distance(rssi)

                        if distance is None:
                            distance = self.last_known_distance.get(mac)
                        else:
                            self.last_known_distance[mac] = distance

                        filtered_distance = self.update_ukf(mac, distance)
                        dev['rssi'] = rssi
                        dev['distance'] = filtered_distance if filtered_distance and filtered_distance > 0 else None
                        dev['connected'] = self.is_device_connected(mac)
                        dev['txPower'] = -59
                time.sleep(5)

        threading.Thread(target=monitor, daemon=True).start()

    def create_ukf(self, initial_distance):
        def fx(x, dt):
            return np.array([x[0] + x[1]*dt, x[1]])

        def hx(x):
            return np.array([x[0]])

        dt = 1
        points = MerweScaledSigmaPoints(n=2, alpha=0.1, beta=2.0, kappa=0.0)
        ukf = UKF(dim_x=2, dim_z=1, fx=fx, hx=hx, dt=dt, points=points)
        ukf.x = np.array([initial_distance, 0.0])
        ukf.P *= 10
        ukf.R = np.array([[.5]])
        ukf.Q = np.eye(2) * 0.1
        return ukf

    def update_ukf(self, mac, distance):
        if distance is None:
            return self.last_known_distance.get(mac)

        if mac not in self.device_filters:
            self.device_filters[mac] = self.create_ukf(distance)

        ukf = self.device_filters[mac]
        ukf.predict()
        ukf.update(np.array([distance]))
        return round(ukf.x[0], 2)

    def start_bluetoothctl(self):
        if self.child:
            self.child.close()
        self.child = pexpect.spawn("bluetoothctl", echo=False)
        self.send_cmd("agent on")
        self.send_cmd("default-agent")
        self.send_cmd("power on")

    def send_cmd(self, cmd, wait=1):
        if self.child:
            self.child.sendline(cmd)
            time.sleep(wait)

    def get_device_name(self, mac):
        try:
            result = subprocess.run(['bluetoothctl', 'info', mac], capture_output=True, text=True, timeout=5)
            match = re.search(r'Name: (.+)', result.stdout)
            return match.group(1).strip() if match else mac
        except:
            return mac

    def get_device_rssi(self, mac, allow_cache=False):
        try:
            result = subprocess.run(['hcitool', 'rssi', mac], capture_output=True, text=True, timeout=3)
            match = re.search(r'RSSI return value: (-?\d+)', result.stdout)
            if match:
                rssi = int(match.group(1))
                if rssi != 0:
                    self.last_known_rssi[mac] = rssi
                    return rssi
        except:
            pass

        if allow_cache:
            return self.last_known_rssi.get(mac)

        return None

    def estimate_distance(self, rssi, tx_power=-59):
        if rssi is None or rssi <= -100:
            return None
        try:
            n = 2.5
            dist = math.pow(10, (tx_power - rssi) / (10.0 * n))
            return round(dist, 1) if dist > 0 else None
        except:
            return None

    def scan_devices(self, duration=8):
        print("\U0001F50D Scanning for devices...")
        self.discovered_devices.clear()
        self.send_cmd("scan on")
        buffer = ""
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                self.child.expect("\r\n", timeout=1)
                line = self.child.before.decode("utf-8").strip()
                buffer += line + "\n"
            except pexpect.exceptions.TIMEOUT:
                continue
        self.send_cmd("scan off")

        # Collect RSSI samples per device
        rssi_samples = {}
        rssi_regex = re.compile(r"Device ([0-9A-F:]{17}) RSSI: (-?\d+)")
        for match in rssi_regex.finditer(buffer):
            mac, rssi_val = match.group(1), int(match.group(2))
            if -100 < rssi_val < 0:  # Valid RSSI range
                rssi_samples.setdefault(mac, []).append(rssi_val)

        # Collect device names
        device_regex = re.compile(r"Device ([0-9A-F:]{17}) (.+)")
        for match in device_regex.finditer(buffer):
            mac, name = match.group(1), match.group(2).strip()

            if re.match(r'(RSSI:|Connected|ServiceResolved|Paired:|TxPower|[+-]?\d+)', name):
                name = self.get_device_name(mac)
            if not name or name.lower() == "unknown":
                name = self.get_device_name(mac)

            rssi_list = rssi_samples.get(mac, [])
            rssi = int(np.median(rssi_list)) if rssi_list else self.get_device_rssi(mac, allow_cache=True)

            if rssi is not None:
                self.last_known_rssi[mac] = rssi

            distance = self.estimate_distance(rssi)
            if distance:
                self.last_known_distance[mac] = distance

            filtered_distance = self.update_ukf(mac, distance)

            self.discovered_devices[mac] = {
                'mac': mac,
                'name': name,
                'rssi': rssi,
                'distance': filtered_distance if filtered_distance and filtered_distance > 0 else None,
                'connected': self.is_device_connected(mac),
                'paired': self.is_device_paired(mac),
                'txPower': -59
            }

        # Include connected devices not seen in this scan
        for mac, info in self.connected_devices.items():
            if mac not in self.discovered_devices:
                self.discovered_devices[mac] = info

        return list(self.discovered_devices.values())

    def is_device_connected(self, mac):
        try:
            result = subprocess.run(['bluetoothctl', 'info', mac], capture_output=True, text=True, timeout=5)
            return 'Connected: yes' in result.stdout
        except:
            return False

    def is_device_paired(self, mac):
        try:
            result = subprocess.run(['bluetoothctl', 'info', mac], capture_output=True, text=True, timeout=5)
            return 'Paired: yes' in result.stdout
        except:
            return False

    def pair_device(self, mac):
        self.send_cmd(f"pair {mac}", wait=4)
        self.send_cmd(f"trust {mac}", wait=2)
        return True

    def connect_device(self, mac):
        self.send_cmd(f"connect {mac}", wait=4)
        if self.is_device_connected(mac):
            name = self.get_device_name(mac)
            rssi = self.get_device_rssi(mac, allow_cache=True)
            if rssi is not None and rssi != 0:
                self.last_known_rssi[mac] = rssi
            distance = self.estimate_distance(rssi)
            if distance is None:
                distance = self.last_known_distance.get(mac)
            else:
                self.last_known_distance[mac] = distance

            filtered_distance = self.update_ukf(mac, distance)

            self.connected_devices[mac] = {
                'mac': mac,
                'name': name,
                'rssi': rssi,
                'distance': filtered_distance if filtered_distance and filtered_distance > 0 else None,
                'connected': True,
                'paired': True,
                'txPower': -59
            }
            return True
        return False

    def disconnect_device(self, mac):
        self.send_cmd(f"disconnect {mac}", wait=3)
        if not self.is_device_connected(mac):
            self.connected_devices.pop(mac, None)
            return True
        return False

    def get_all_devices(self):
        all_devices = {**self.discovered_devices, **self.connected_devices}
        return list(all_devices.values())


# Initialize Bluetooth manager
bt = BluetoothManager()
bt.start_bluetoothctl()

# API endpoints
@app.route('/api/scan', methods=['POST'])
def api_scan():
    devices = bt.scan_devices()
    return jsonify({'success': True, 'devices': devices})

@app.route('/api/devices', methods=['GET'])
def api_get_devices():
    return jsonify({'devices': bt.get_all_devices()})

@app.route('/api/pair', methods=['POST'])
def api_pair():
    mac = request.json.get('mac')
    return jsonify({'success': bt.pair_device(mac)})

@app.route('/api/connect', methods=['POST'])
def api_connect():
    mac = request.json.get('mac')
    return jsonify({'success': bt.connect_device(mac)})

@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    mac = request.json.get('mac')
    return jsonify({'success': bt.disconnect_device(mac)})

if __name__ == '__main__':
    print("\U0001F535 Bluetooth Backend Started on port 5000")
    app.run(host='0.0.0.0', port=5000)
