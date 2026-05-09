#include "HtmlPages.h"

const char index_html[] = R"rawliteral(
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Snow sensor ❄️</title>
  </head>
  <body>
    <h1>Snow sensor ❄️</h1>
    <p>Temperature: <span id="temp">—</span> ˚C</p>
    <p>Snow: <span id="snow">—</span> cm</p>
    <p>Pressure: <span id="press">—</span> hPa</p>

    <form action='/' method='POST'>
      <label>Known snow depth (cm):</label>
      <input type='number' step='0.1' name='snow_depth' value='0'><br><br>
      <input type='submit' value='Calibrate Sensor'>
    </form>

    <h1>Settings</h1>
    <p><a href="/wifi">WiFi Settings</a></p>
    <p><a href="/mqtt">MQTT Settings</a></p>
    <p><a href="/update">OTA Update</a></p>

    <script>
      async function update() {
        try {
          const r = await fetch('/sensor');
          const j = await r.json();
          document.getElementById('temp').textContent = j.temperature_c.toFixed(2);
          document.getElementById('snow').textContent = j.snow_depth_cm.toFixed(0);
          document.getElementById('press').textContent = j.pressure_hpa.toFixed(2);
        } catch (e) {
          document.getElementById('temp').textContent = 'err';
          document.getElementById('snow').textContent = 'err';
          document.getElementById('press').textContent = 'err';
        }
      }
      update();
      setInterval(update, 10000);
    </script>
  </body>
</html>
)rawliteral";

const char wifi_html[] = R"rawliteral(
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Snow sensor ❄️</title>
  </head>
  <body>
    <h1>Wifi manager</h1>
    <form action='/wifi' method='POST'>
    <label>SSID:</label><input type='text' name='ssid' value='%SSID%'><br><br>
    <label>Password:</label><input type='password' name='password'><br><br>
    <label>Static IP:</label><input type='text' name='ip' value='%IP%'><br><br>
    <label>Gateway IP:</label><input type='text' name='gateway' value='%GATEWAY%'><br><br>

    <input type='submit' value='Save & Restart'>
    </form>
  </body>
</html>
)rawliteral";

const char mqtt_html[] = R"rawliteral(
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Snow sensor ❄️</title>
  </head>
  <body>
    <h1>MQTT Settings</h1>
    <form action='/mqtt' method='POST'>
    <label>Broker IP:</label><input type='text' name='broker' value='%BROKER%'><br><br>
    <input type='submit' value='Save & Restart'>
    </form>
  </body>
</html>
)rawliteral";
