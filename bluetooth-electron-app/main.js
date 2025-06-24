const { app, BrowserWindow } = require("electron");
const path = require("path");
const { exec } = require("child_process");

app.disableHardwareAcceleration();

function createWindow() {
  const win = new BrowserWindow({
    width: 1024,
    height: 700,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  win.setMenu(null); // 🚫 Disable default menu

  win.loadFile(path.join(__dirname, 'build', 'index.html'));
  exec("venv/bin/python3 bluet5.py", (error, stdout, stderr) => {
  if (error) {
    console.error(`Backend failed to start: ${error.message}`);
  }
});

  // Optional: Start Flask backend
  // exec("python3 bluet5.py &");
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
