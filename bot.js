const https = require("https");
const http = require("http");

// ================================
// TELEGRAM CONFIGURATION
// ================================

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;

// ================================
// BOT INFORMATION
// ================================

console.log("================================");
console.log("Pocket Option Signal Bot");
console.log("================================");
console.log("Market: EUR/USD OTC");
console.log("Timeframe: M1");
console.log("Strategy: EMA + RSI");
console.log("Status: ACTIVE");

// Check Telegram credentials
if (TELEGRAM_BOT_TOKEN && TELEGRAM_CHAT_ID) {
  console.log("Telegram credentials: FOUND");
} else {
  console.log("Telegram credentials: MISSING");
}

// ================================
// TEST CANDLE DATA
// ================================

const candles = [
  1.1000, 1.1002, 1.1001, 1.1004, 1.1005,
  1.1007, 1.1006, 1.1008, 1.1010, 1.1009,
  1.1012, 1.1014, 1.1013, 1.1015, 1.1017,
  1.1016, 1.1018, 1.1020, 1.1019, 1.1021
];

// ================================
// EMA
// ================================

function calculateEMA(prices, period) {
  const multiplier = 2 / (period + 1);

  let ema = prices[0];

  for (let i = 1; i < prices.length; i++) {
    ema =
      ((prices[i] - ema) * multiplier) +
      ema;
  }

  return ema;
}

// ================================
// RSI
// ================================

function calculateRSI(prices, period = 14) {
  let gains = 0;
  let losses = 0;

  for (
    let i = prices.length - period;
    i < prices.length;
    i++
  ) {
    const change = prices[i] - prices[i - 1];

    if (change > 0) {
      gains += change;
    }

    if (change < 0) {
      losses += Math.abs(change);
    }
  }

  if (losses === 0) {
    return 100;
  }

  const rs = gains / losses;

  return 100 - (100 / (1 + rs));
}

// ================================
// SEND TELEGRAM MESSAGE
// ================================

function sendTelegramMessage(message) {

  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
    console.log("Telegram credentials are missing.");
    return;
  }

  const telegramData = JSON.stringify({
    chat_id: TELEGRAM_CHAT_ID,
    text: message
  });

  const options = {
    hostname: "api.telegram.org",

    path:
      `/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,

    method: "POST",

    headers: {
      "Content-Type": "application/json",
      "Content-Length":
        Buffer.byteLength(telegramData)
    }
  };

  const request = https.request(
    options,
    (response) => {

      let responseData = "";

      response.on(
        "data",
        (chunk) => {
          responseData += chunk;
        }
      );

      response.on(
        "end",
        () => {

          console.log(
            "Telegram HTTP status:",
            response.statusCode
          );

          console.log(
            "Telegram response:",
            responseData
          );

        }
      );

    }
  );

  request.on(
    "error",
    (error) => {

      console.log(
        "Telegram connection error:",
        error.message
      );

    }
  );

  request.write(telegramData);

  request.end();
}

// ================================
// TEST TELEGRAM
// ================================

function sendTelegramTest() {

  console.log("Sending Telegram test message...");

  sendTelegramMessage(
    "✅ Pocket Option Signal Bot is ONLINE\n\n" +
    "Market: EUR/USD OTC\n" +
    "Timeframe: M1\n" +
    "Strategy: EMA + RSI\n\n" +
    "Telegram connection test successful."
  );
}

// ================================
// SIGNAL GENERATOR
// ================================

function generateSignal() {

  const price =
    candles[candles.length - 1];

  const ema =
    calculateEMA(candles, 9);

  const rsi =
    calculateRSI(candles);

  let signal = "NO TRADE";

  if (
    price > ema &&
    rsi >= 55
  ) {
    signal = "BUY";
  }

  else if (
    price < ema &&
    rsi <= 45
  ) {
    signal = "SELL";
  }

  console.log("--------------------------------");
  console.log("Price:", price);
  console.log("EMA:", ema.toFixed(5));
  console.log("RSI:", rsi.toFixed(2));
  console.log("Signal:", signal);

  // Send only BUY or SELL signals
  if (
    signal === "BUY" ||
    signal === "SELL"
  ) {

    const message =
      "🚨 POCKET OPTION SIGNAL 🚨\n\n" +

      "Market: EUR/USD OTC\n" +

      "Timeframe: M1\n" +

      `Signal: ${signal}\n` +

      `Price: ${price}\n` +

      `EMA: ${ema.toFixed(5)}\n` +

      `RSI: ${rsi.toFixed(2)}\n\n` +

      "Strategy: EMA + RSI";

    console.log(
      "Sending signal to Telegram..."
    );

    sendTelegramMessage(message);

  } else {

    console.log(
      "No trade signal."
    );

  }

  console.log(
    "Waiting for next signal..."
  );
}

// ================================
// START BOT
// ================================

console.log("Starting bot...");

// Send Telegram connection test
sendTelegramTest();

// Generate first signal
generateSignal();

// Check every 60 seconds
setInterval(
  generateSignal,
  60000
);

// ================================
// RENDER WEB SERVER
// ================================

const PORT =
  process.env.PORT || 10000;

const server =
  http.createServer(
    (req, res) => {

      res.writeHead(
        200,
        {
          "Content-Type":
            "text/plain"
        }
      );

      res.end(
        "Pocket Option Signal Bot is running"
      );

    }
  );

server.listen(
  PORT,
  () => {

    console.log(
      `Server running on port ${PORT}`
    );

  }
);
