const https = require("https");
const http = require("http");

// ==========================================
// ENVIRONMENT VARIABLES
// ==========================================

const TELEGRAM_BOT_TOKEN =
  process.env.TELEGRAM_BOT_TOKEN;

const TELEGRAM_CHAT_ID =
  process.env.TELEGRAM_CHAT_ID;

const TWELVE_DATA_API_KEY =
  process.env.TWELVE_DATA_API_KEY;

// ==========================================
// SETTINGS
// ==========================================

const SYMBOL = "EUR/USD";
const INTERVAL = "1min";

const CHECK_EVERY = 60000;

const EMA_FAST = 9;
const EMA_SLOW = 21;
const RSI_PERIOD = 14;

const MIN_CONFIDENCE = 75;

let lastCandleTime = null;
let lastSentSignal = null;

// ==========================================
// STARTUP
// ==========================================

console.log("====================================");
console.log("LIVE EUR/USD SIGNAL BOT");
console.log("====================================");

console.log("Market:", SYMBOL);
console.log("Timeframe:", INTERVAL);
console.log("Strategy: EMA 9 + EMA 21 + RSI 14");
console.log(
  "Minimum confidence:",
  MIN_CONFIDENCE + "%"
);

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

// ==========================================
// EMA
// ==========================================

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

// ==========================================
// RSI
// ==========================================

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

// ==========================================
// TWELVE DATA
// ==========================================

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

      const request =
        https.request(
          {
            hostname:
              "api.twelvedata.com",

            path: path,

            method: "GET"
          },

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

// ==========================================
// TELEGRAM
// ==========================================

function sendTelegramMessage(message) {

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

      text:
        message
    });

  const request =
    https.request(
      {
        hostname:
          "api.telegram.org",

        path:
          `/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,

        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json",

          "Content-Length":
            Buffer.byteLength(data)
        }
      },

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

// ==========================================
// SIGNAL CALCULATION
// ==========================================

function calculateSignal(
  prices,
  latest,
  previous
) {

  const ema9 =
    calculateEMA(
      prices,
      EMA_FAST
    );

  const ema21 =
    calculateEMA(
      prices,
      EMA_SLOW
    );

  const rsi =
    calculateRSI(
      prices,
      RSI_PERIOD
    );

  if (
    ema9 === null ||
    ema21 === null ||
    rsi === null
  ) {

    return {
      signal: "NO TRADE",
      confidence: 0,
      ema9,
      ema21,
      rsi,
      buyScore: 0,
      sellScore: 0
    };

  }

  const price =
    Number(latest.close);

  const previousClose =
    Number(previous.close);

  const candleOpen =
    Number(latest.open);

  const candleClose =
    Number(latest.close);

  const bullishCandle =
    candleClose > candleOpen;

  const bearishCandle =
    candleClose < candleOpen;

  // ========================================
  // BUY SCORE
  // ========================================

  let buyScore = 0;

  if (ema9 > ema21) {
    buyScore += 25;
  }

  if (price > ema9) {
    buyScore += 20;
  }

  if (price > ema21) {
    buyScore += 15;
  }

  if (
    rsi >= 55 &&
    rsi <= 70
  ) {
    buyScore += 20;
  }

  if (bullishCandle) {
    buyScore += 10;
  }

  if (price > previousClose) {
    buyScore += 10;
  }

  // ========================================
  // SELL SCORE
  // ========================================

  let sellScore = 0;

  if (ema9 < ema21) {
    sellScore += 25;
  }

  if (price < ema9) {
    sellScore += 20;
  }

  if (price < ema21) {
    sellScore += 15;
  }

  if (
    rsi <= 45 &&
    rsi >= 30
  ) {
    sellScore += 20;
  }

  if (bearishCandle) {
    sellScore += 10;
  }

  if (price < previousClose) {
    sellScore += 10;
  }

  // ========================================
  // FINAL SIGNAL
  // ========================================

  let signal = "NO TRADE";
  let confidence = 0;

  if (
    buyScore >= MIN_CONFIDENCE &&
    buyScore > sellScore
  ) {

    signal = "BUY";
    confidence = buyScore;

  } else if (
    sellScore >= MIN_CONFIDENCE &&
    sellScore > buyScore
  ) {

    signal = "SELL";
    confidence = sellScore;

  }

  return {
    signal,
    confidence,
    ema9,
    ema21,
    rsi,
    buyScore,
    sellScore
  };
}

// ==========================================
// MARKET CHECK
// ==========================================

async function checkMarket() {

  console.log("------------------------------------");

  console.log(
    "Checking live EUR/USD M1..."
  );

  try {

    const candles =
      await getMarketData();

    const ordered =
      [...candles].reverse();

    const prices =
      ordered.map(
        candle =>
          Number(candle.close)
      );

    if (prices.length < 30) {

      console.log(
        "Not enough candles."
      );

      return;
    }

    const latest =
      ordered[
        ordered.length - 1
      ];

    const previous =
      ordered[
        ordered.length - 2
      ];

    const candleTime =
      latest.datetime;

    const price =
      Number(latest.close);

    // ======================================
    // SAME CANDLE PROTECTION
    // ======================================

    if (
      candleTime ===
      lastCandleTime
    ) {

      console.log(
        "Same candle - waiting..."
      );

      return;
    }

    lastCandleTime =
      candleTime;

    // ======================================
    // CALCULATE
    // ======================================

    const result =
      calculateSignal(
        prices,
        latest,
        previous
      );

    const {
      signal,
      confidence,
      ema9,
      ema21,
      rsi,
      buyScore,
      sellScore
    } = result;

    console.log(
      "Candle:",
      candleTime
    );

    console.log(
      "Price:",
      price.toFixed(5)
    );

    console.log(
      "EMA 9:",
      ema9.toFixed(5)
    );

    console.log(
      "EMA 21:",
      ema21.toFixed(5)
    );

    console.log(
      "RSI:",
      rsi.toFixed(2)
    );

    console.log(
      "BUY score:",
      buyScore
    );

    console.log(
      "SELL score:",
      sellScore
    );

    console.log(
      "Signal:",
      signal
    );

    console.log(
      "Confidence:",
      confidence + "%"
    );

    // ======================================
    // NO TRADE
    // ======================================

    if (
      signal === "NO TRADE"
    ) {

      console.log(
        "Conditions not strong enough."
      );

      return;
    }

    // ======================================
    // PREVENT DUPLICATES
    // ======================================

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

    // ======================================
    // CORRECT ARUBA TIME
    // ======================================

    const signalDate =
      new Date(
        candleTime.replace(
          " ",
          "T"
        ) + "-04:00"
      );

    const expiryDate =
      new Date(
        signalDate.getTime() +
        60000
      );

    const expiryTime =
      expiryDate.toLocaleTimeString(
        "en-US",
        {
          timeZone:
            "America/Aruba",

          hour:
            "2-digit",

          minute:
            "2-digit",

          hour12:
            false
        }
      );

    // ======================================
    // TELEGRAM MESSAGE
    // ======================================

    const message =
      "🚨 LIVE EUR/USD SIGNAL 🚨\n\n" +

      `📊 Signal: ${signal}\n` +

      `🎯 Filter score: ${confidence}%\n\n` +

      `💰 Entry: ${price.toFixed(5)}\n` +

      `⏰ Signal time: ${candleTime}\n` +

      `⏳ 1M expiry: ${expiryTime}\n\n` +

      `EMA 9: ${ema9.toFixed(5)}\n` +

      `EMA 21: ${ema21.toFixed(5)}\n` +

      `RSI 14: ${rsi.toFixed(2)}\n\n` +

      "Timeframe: M1\n" +

      "Source: Twelve Data\n" +

      "⚠️ Not Pocket Option OTC data\n\n" +

      "Filtered signal — not a guaranteed win.";

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

// ==========================================
// START BOT
// ==========================================

console.log(
  "Starting live market monitoring..."
);

checkMarket();

setInterval(
  checkMarket,
  CHECK_EVERY
);

// ==========================================
// RENDER SERVER
// ==========================================

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
