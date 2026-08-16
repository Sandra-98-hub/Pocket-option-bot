const https = require("https");
const http = require("http");

// ================================
// ENVIRONMENT VARIABLES
// ================================

const TELEGRAM_BOT_TOKEN =
  process.env.TELEGRAM_BOT_TOKEN;

const TELEGRAM_CHAT_ID =
  process.env.TELEGRAM_CHAT_ID;

const TWELVE_DATA_API_KEY =
  process.env.TWELVE_DATA_API_KEY;

// ================================
// SETTINGS
// ================================

const SYMBOL = "EUR/USD";
const INTERVAL = "1min";
const CHECK_EVERY = 60000;

let lastCandleTime = null;
let lastSentSignal = null;

// ================================
// STARTUP
// ================================

console.log("================================");
console.log("Pocket Option Signal Bot");
console.log("================================");
console.log("Market:", SYMBOL);
console.log("Timeframe: M1");
console.log("Strategy: EMA + RSI");
console.log("Status: ACTIVE");

console.log(
  "Telegram:",
  TELEGRAM_BOT_TOKEN && TELEGRAM_CHAT_ID
    ? "FOUND"
    : "MISSING"
);

console.log(
  "Twelve Data:",
  TWELVE_DATA_API_KEY
    ? "FOUND"
    : "MISSING"
);

// ================================
// EMA
// ================================

function calculateEMA(prices, period) {
  if (prices.length < period) {
    return null;
  }

  const multiplier =
    2 / (period + 1);

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

function calculateRSI(
  prices,
  period = 14
) {
  if (prices.length <= period) {
    return null;
  }

  let gains = 0;
  let losses = 0;

  for (
    let i = prices.length - period;
    i < prices.length;
    i++
  ) {
    const change =
      prices[i] - prices[i - 1];

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

  const rs =
    gains / losses;

  return 100 -
    (100 / (1 + rs));
}

// ================================
// GET TWELVE DATA
// ================================

function getMarketData() {

  return new Promise(
    (resolve, reject) => {

      if (!TWELVE_DATA_API_KEY) {
        reject(
          new Error(
            "TWELVE_DATA_API_KEY is missing"
          )
        );
        return;
      }

      const path =
        "/time_series" +
        "?symbol=" +
        encodeURIComponent(SYMBOL) +
        "&interval=" +
        INTERVAL +
        "&outputsize=50" +
        "&timezone=America/Aruba" +
        "&apikey=" +
        encodeURIComponent(
          TWELVE_DATA_API_KEY
        );

      const options = {
        hostname: "api.twelvedata.com",
        path: path,
        method: "GET"
      };

      const request =
        https.request(
          options,
          (response) => {

            let data = "";

            response.on(
              "data",
              (chunk) => {
                data += chunk;
              }
            );

            response.on(
              "end",
              () => {

                try {

                  const json =
                    JSON.parse(data);

                  if (
                    json.status === "error"
                  ) {
                    reject(
                      new Error(
                        json.message ||
                        "Twelve Data error"
                      )
                    );
                    return;
                  }

                  if (
                    !json.values ||
                    !Array.isArray(
                      json.values
                    )
                  ) {
                    reject(
                      new Error(
                        "No market data received"
                      )
                    );
                    return;
                  }

                  resolve(
                    json.values
                  );

                } catch (error) {

                  reject(error);

                }

              }
            );

          }
        );

      request.on(
        "error",
        (error) => {
          reject(error);
        }
      );

      request.end();

    }
  );
}

// ================================
// TELEGRAM
// ================================

function sendTelegramMessage(
  message
) {

  if (
    !TELEGRAM_BOT_TOKEN ||
    !TELEGRAM_CHAT_ID
  ) {
    console.log(
      "Telegram credentials are missing."
    );
    return;
  }

  const data =
    JSON.stringify({
      chat_id:
        TELEGRAM_CHAT_ID,
      text: message
    });

  const options = {
    hostname:
      "api.telegram.org",

    path:
      `/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,

    method: "POST",

    headers: {
      "Content-Type":
        "application/json",

      "Content-Length":
        Buffer.byteLength(data)
    }
  };

  const request =
    https.request(
      options,
      (response) => {

        let body = "";

        response.on(
          "data",
          (chunk) => {
            body += chunk;
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
              body
            );

          }
        );

      }
    );

  request.on(
    "error",
    (error) => {

      console.log(
        "Telegram error:",
        error.message
      );

    }
  );

  request.write(data);
  request.end();
}

// ================================
// ANALYZE MARKET
// ================================

async function checkMarket() {

  console.log("--------------------------------");
  console.log(
    "Checking live EUR/USD M1 data..."
  );

  try {

    const candles =
      await getMarketData();

    // Twelve Data returns newest first,
    // so reverse into oldest -> newest.
    const ordered =
      [...candles].reverse();

    const prices =
      ordered.map(
        candle =>
          Number(candle.close)
      );

    if (prices.length < 20) {

      console.log(
        "Not enough candles."
      );

      return;
    }

    const latest =
      ordered[
        ordered.length - 1
      ];

    const candleTime =
      latest.datetime;

    const price =
      Number(latest.close);

    const ema =
      calculateEMA(
        prices,
        9
      );

    const rsi =
      calculateRSI(
        prices,
        14
      );

    console.log(
      "Candle time:",
      candleTime
    );

    console.log(
      "Price:",
      price
    );

    console.log(
      "EMA:",
      ema.toFixed(5)
    );

    console.log(
      "RSI:",
      rsi.toFixed(2)
    );

    // Don't process the same candle repeatedly.
    if (
      candleTime === lastCandleTime
    ) {

      console.log(
        "Same candle - waiting..."
      );

      return;
    }

    lastCandleTime =
      candleTime;

    let signal =
      "NO TRADE";

    if (
      price > ema &&
      rsi >= 55
    ) {

      signal = "BUY";

    } else if (
      price < ema &&
      rsi <= 45
    ) {

      signal = "SELL";

    }

    console.log(
      "Signal:",
      signal
    );

    // Only send BUY/SELL.
    if (
      signal !== "BUY" &&
      signal !== "SELL"
    ) {

      console.log(
        "No trade signal."
      );

      return;
    }

    // Don't repeatedly send
    // the same direction.
    if (
      signal === lastSentSignal
    ) {

      console.log(
        "Same signal as previous."
      );

      return;
    }

    lastSentSignal =
      signal;

    const message =
      "🚨 LIVE EUR/USD SIGNAL 🚨\n\n" +

      `Signal: ${signal}\n` +

      `Time: ${candleTime}\n` +

      `Price: ${price.toFixed(5)}\n` +

      `EMA(9): ${ema.toFixed(5)}\n` +

      `RSI(14): ${rsi.toFixed(2)}\n\n` +

      "Timeframe: M1\n" +

      "Source: Twelve Data\n" +

      "⚠️ Not Pocket Option OTC data";

    console.log(
      "Sending signal to Telegram..."
    );

    sendTelegramMessage(
      message
    );

  } catch (error) {

    console.log(
      "Market data error:",
      error.message
    );

  }
}

// ================================
// RUN BOT
// ================================

checkMarket();

setInterval(
  checkMarket,
  CHECK_EVERY
);

// ================================
// RENDER SERVER
// ================================

const PORT =
  process.env.PORT || 10000;

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
      "Live EUR/USD Signal Bot is running"
    );

  }
).listen(
  PORT,
  () => {

    console.log(
      `Server running on port ${PORT}`
    );

  }
);
