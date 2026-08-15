const https = require("https");
const http = require("http");

console.log("Pocket Option Signal Bot");
console.log("========================");
console.log("Market: EUR/USD OTC");
console.log("Timeframe: M1");
console.log("Strategy: EMA + RSI");
console.log("Status: ACTIVE");

// Telegram settings
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;

// Test candles
const candles = [
  1.1000, 1.1002, 1.1001, 1.1004, 1.1005,
  1.1007, 1.1006, 1.1008, 1.1010, 1.1009,
  1.1012, 1.1014, 1.1013, 1.1015, 1.1017,
  1.1016, 1.1018, 1.1020, 1.1019, 1.1021
];

function calculateEMA(prices, period) {
  const multiplier = 2 / (period + 1);
  let ema = prices[0];

  for (let i = 1; i < prices.length; i++) {
    ema = ((prices[i] - ema) * multiplier) + ema;
  }

  return ema;
}

function calculateRSI(prices, period = 14) {
  let gains = 0;
  let losses = 0;

  for (let i = prices.length - period; i < prices.length; i++) {
    const change = prices[i] - prices[i - 1];

    if (change > 0) gains += change;
    if (change < 0) losses += Math.abs(change);
  }

  if (losses === 0) return 100;

  const rs = gains / losses;
  return 100 - (100 / (1 + rs));
}

function sendTelegramMessage(message) {
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
    console.log("Telegram credentials are missing.");
    return;
  }

  const data = JSON.stringify({
    chat_id: TELEGRAM_CHAT_ID,
    text: message
  });

  const options = {
    hostname: "api.telegram.org",
    path: `/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Content-Length": Buffer.byteLength(data)
    }
  };

  const request = https.request(options, (response) => {
    let body = "";

    response.on("data", (chunk) => {
      body += chunk;
    });

    response.on("end", () => {
      console.log("Telegram response:", body);
    });
  });

  request.on("error", (error) => {
    console.log("Telegram error:", error.message);
  });

  request.write(data);
  request.end();
}

function generateSignal() {
  const price = candles[candles.length - 1];
  const ema = calculateEMA(candles, 9);
  const rsi = calculateRSI(candles);

  let signal = "NO TRADE";

  if (price > ema && rsi >= 55) {
    signal = "BUY";
  } else if (price < ema && rsi <= 45) {
    signal = "SELL";
  }

  console.log("--------------------------------");
  console.log(`Price: ${price}`);
  console.log(`EMA: ${ema.toFixed(5)}`);
  console.log(`RSI: ${rsi.toFixed(2)}`);
  console.log(`Signal: ${signal}`);

  if (signal === "BUY" || signal === "SELL") {
    const message =
      `🚨 POCKET OPTION SIGNAL 🚨\n\n` +
      `Market: EUR/USD OTC\n` +
      `Timeframe: M1\n` +
      `Signal: ${signal}\n` +
      `Price: ${price}\n` +
      `EMA: ${ema.toFixed(5)}\n` +
      `RSI: ${rsi.toFixed(2)}\n\n` +
      `Strategy: EMA + RSI`;

    sendTelegramMessage(message);
  } else {
    console.log("No trade signal.");
  }

  console.log("Waiting for next signal...");
}

// Run immediately
generateSignal();

// Check every 60 seconds
setInterval(generateSignal, 60000);

// Render web server
const PORT = process.env.PORT || 10000;

http.createServer((req, res) => {
  res.writeHead(200, {
    "Content-Type": "text/plain"
  });

  res.end("Pocket Option Signal Bot is running");
}).listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
