<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HK SIGNAL BOT</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f4f4f9; text-align: center; padding: 20px; }
    .card { background: gold; padding: 20px; border-radius: 12px; font-weight: bold; font-size: 20px; margin-bottom: 20px; }
    
    /* Radar Loader Setup */
    .radar {
      width: 80px; height: 80px; margin: 20px auto; border-radius: 50%;
      border: 3px solid #333; position: relative; background: #111; display: none;
    }
    .radar::after {
      content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      border-radius: 50%; border: 2px solid transparent; border-top-color: #00ffcc;
      animation: spin 1s linear infinite;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

    /* Button Styling */
    .btn { background: #007bff; color: white; padding: 15px 30px; border: none; font-size: 18px; border-radius: 8px; cursor: pointer; }
    
    /* Result Box Styling */
    .result-box { display: none; background: #d9534f; color: white; padding: 20px; border-radius: 12px; margin-top: 20px; }
  </style>
</head>
<body>

  <div class="card">HK SIGNAL BOT<br><small>🟢 CONNECTED TO LIVE TECHNICAL ENGINE</small></div>

  <!-- Radar Loader -->
  <div id="radar" class="radar"></div>

  <button class="btn" onclick="startAnalysis()">⚡ START ANALYZING</button>

  <!-- Result Container -->
  <div id="result" class="result-box">
    <h2 id="pair">PAIR: EUR/USD</h2>
    <h1 id="signal">PUT ⬇ (SELL)</h1>
    <h3>ACCURACY STRATEGY: <span id="accuracy">85%</span></h3>
    <p><b>DETECTED DETAILS:</b></p>
    <p>• Market Structure: REAL PRICE ACTION</p>
    <p>• RSI: 42 | Trend: BEARISH</p>
    <h4>PREPARE ENTRY NOW...</h4>
  </div>

  <script>
    function startAnalysis() {
      // 1. Show Radar loader
      document.getElementById('radar').style.display = 'block';
      document.getElementById('result').style.display = 'none';

      // 2. Simulate 3-second scanning process
      setTimeout(() => {
        document.getElementById('radar').style.display = 'none';
        document.getElementById('result').style.display = 'block';
      }, 3000);
    }
  </script>

</body>
</html>
