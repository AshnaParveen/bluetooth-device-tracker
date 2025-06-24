// Updated App.js with chart and distances for all discoverable devices
import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend
} from "chart.js";
import "./App.css";

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Title, Tooltip, Legend);

function App() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDevices = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/devices");
      const data = await response.json();
      if (data.devices) {
        setDevices(data.devices);
        setError(null);
      } else {
        setError("Failed to fetch devices");
      }
    } catch (err) {
      setError("Backend unreachable");
    }
  };

  useEffect(() => {
    fetchDevices();
    const interval = setInterval(fetchDevices, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleScan = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ duration: 10 })
      });
      const data = await res.json();
      if (data.devices) {
        setDevices(data.devices);
        setError(null);
      } else {
        setError("Scan failed");
      }
    } catch (e) {
      setError("Scan failed");
    }
    setLoading(false);
  };

  const handlePair = async (mac) => {
    await fetch("http://localhost:5000/api/pair", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mac })
    });
    await fetch("http://localhost:5000/api/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mac })
    });
    await fetchDevices(); // ensure UI reflects new connection state
  };

  const handleDisconnect = async (mac) => {
    await fetch("http://localhost:5000/api/disconnect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mac })
    });
    fetchDevices();
  };

  const chartData = {
    labels: devices.map(d => d.name || d.mac),
    datasets: [
      {
        label: "Distance (m)",
        data: devices.map(d => d.distance !== null && d.distance !== undefined ? d.distance : 0),
        fill: false,
        borderColor: "#4bc0c0",
        backgroundColor: "#4bc0c0",
        tension: 0.1
      }
    ]
  };

  return (
    <div className="app-container">
      <h1 className="title">Bluetooth Device Tracker</h1>
      <div className="main-grid">
        <div className="card">
          <div className="card-header">
            <h2>Discoverable Devices</h2>
            <button className="btn" onClick={handleScan} disabled={loading}>
              {loading ? "Scanning..." : "Scan"}
            </button>
          </div>
          <div className="card-content">
            <ul className="device-list">
              {devices.map((dev, idx) => (
                <li key={idx} className="device-item">
                  <div>
                    <p className="device-name">{dev.name || "Unknown Device"}</p>
                    <p className="device-mac">{dev.mac}</p>
                    <p className="device-distance">Distance: {dev.distance !== null && dev.distance !== undefined ? `${dev.distance} m` : "?"}</p>
                  </div>
                  <div>
                    {!dev.connected ? (
                      <button className="btn" onClick={() => handlePair(dev.mac)}>Pair</button>
                    ) : (
                      <button className="btn disconnect" onClick={() => handleDisconnect(dev.mac)}>Disconnect</button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
            {error && <p className="error">{error}</p>}
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <h2>All Devices - Distance Chart</h2>
          </div>
          <div className="card-content">
            <Line data={chartData} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
