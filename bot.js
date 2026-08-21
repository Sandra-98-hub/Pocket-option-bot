const axios = require("axios");

// ========================================
// SETTINGS
// ========================================

const TWELVE_DATA_API_KEY = process.env.TWELVE_DATA_API_KEY;
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;

const SYMBOLS = [
  "EUR/USD",
  "GBP/USD",
  "USD/JPY",
  "USD/CHF",
  "AUD/USD",
  "USD/CAD",
  "NZD/USD",
  "EUR/GBP"
];

const INTERVAL = "1min";
const OUTPUT_SIZE = 100;

// ========================================
// CHECK ENVIRONMENT VARIABLES
// ========================================

if (!TWELVE_DATA_API_KEY) {
  console.error("ERROR: TWELVE_DATA_API_KEY is missing");
  process.exit(1);
}

if (!TELEGRAM_BOT_TOKEN) {
  console.error("ERROR: TELEGRAM_BOT_TOKEN is missing");
  process.exit(1);
}

if (!TELEGRAM_CHAT_ID) {
  console.error("ERROR: TELEGRAM_CHAT_ID is missing");
  process.exit(1);
}

// ========================================
// EMA
// ========================================

function calculateEMA(values, period) {
  if (values.length < period) {
    return null;
  }

  const multiplier = 2 / (period + 1);

  let ema =
    values
      .slice(0, period)
      .reduce((sum, value) => sum + value, 0) / period;

  for (let i = period; i < values.length; i++) {
    ema =
      (values[i] - ema) * multiplier + ema;
  }

  return ema;
}

// ========================================
// RSI
// ========================================

function calculateRSI(values, period = 14) {
  if (values.length <= period) {
    return null;
  }

  let gains = 0;
  let losses = 0;

  for (let i = 1; i <= period; i++) {
    const change = values[i] - values[i - 1];

    if (change > 0) {
      gains += change;
    } else {
      losses += Math.abs(change);
    }
  }

  let averageGain = gains / period;
  let averageLoss = losses / period;

  for (let i = period + 1; i < values.length; i++) {
    const change = values[i] - values[i - 1];

    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? Math.abs(change) : 0;

    averageGain =
      (averageGain * (period - 1) + gain) / period;

    averageLoss =
      (averageLoss * (period - 1) + loss) / period;
  }

  if (averageLoss === 0) {
    return 100;
  }

  const rs = averageGain / averageLoss;

  return 100 - 100 / (1 + rs);
}

// ========================================
// GET CANDLES
// ========================================

async function getCandles(symbol) {
  const url =
    "https://api.twelvedata.com/time_series";

  const response = await axios.get(url, {
    params: {
      symbol: symbol,
      interval: INTERVAL,
      outputsize: OUTPUT_SIZE,
      apikey: TWELVE_DATA_API_KEY,
      timezone: "UTC"
    }
  });

  if (
    !response.data ||
    !response.data.values ||
    response.data.values.length < 30
  ) {
    throw new Error(
      `No sufficient candle data for ${symbol}`
    );
  }

  // Twelve Data sends newest candle first.
  // Reverse so calculations run oldest → newest.
  return response.data.values.reverse();
}

// ========================================
// GENERATE SIGNAL
// ========================================

function generateSignal(candles) {
  const closes = candles.map(
    candle => Number(candle.close)
  );

  const price = closes[closes.length - 1];

  const ema9 =
    calculateEMA(closes, 9);

  const ema21 =
    calculateEMA(closes, 21);

  const rsi =
    calculateRSI(closes, 14);

  if (
    ema9 === null ||
    ema21 === null ||
    rsi === null
  ) {
    return null;
  }

  // -------------------------------
  // BUY SCORE
  // -------------------------------

  let buyScore = 0;

  if (ema9 > ema21) {
    buyScore += 40;
  }

  if (rsi > 50) {
    buyScore += 30;
  }

  if (price > ema9) {
    buyScore += 30;
  }

  // -------------------------------
  // SELL SCORE
  // -------------------------------

  let sellScore = 0;

  if (ema9 < ema21) {
    sellScore += 40;
  }

  if (rsi < 50) {
    sellScore += 30;
  }

  if (price < ema9) {
    sellScore += 30;
  }

  let signal = null;
  let score = 0;

  if (buyScore >= 80) {
    signal = "BUY";
    score = buyScore;
  }

  if (sellScore >= 80 && sellScore > buyScore) {
    signal = "SELL";
    score = sellScore;
  }

  if (!signal) {
    return null;
  }

  return {
    signal,
    score,
    price,
    ema9,
    ema21,
    rsi,
    candleTime:
      candles[candles.length - 1].datetime
  };
}

// ========================================
// SEND TELEGRAM
// ========================================

async function sendTelegram(message) {
  const url =
    `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;

  await axios.post(url, {
    chat_id: TELEGRAM_CHAT_ID,
    text: message
  });
}

// ========================================
// FORMAT TELEGRAM SIGNAL
// ========================================

function formatSignal(symbol, data) {
  const price =
    Number(data.price).toFixed(5);

  const ema9 =
    Number(data.ema9).toFixed(5);

  const ema21 =
    Number(data.ema21).toFixed(5);

  const rsi =
    Number(data.rsi).toFixed(2);

  const candleDate =
    new Date(
      data.candleTime.replace(" ", "T") + "Z"
    );

  const signalTime =
    candleDate
      .toISOString()
      .replace("T", " ")
      .substring(0, 19);

  const expiryDate =
    new Date(
      candleDate.getTime() + 60 * 1000
    );

  const expiry =
    expiryDate
      .toISOString()
      .replace("T", " ")
      .substring(0, 19);

  return `🚨 BINARY OPTIONS SIGNAL 🚨

📊 Pair: ${symbol}

📈 Signal: ${data.signal}

🎯 Filter score: ${data.score}%

💰 Entry: ${price}

⏰ Signal candle: ${signalTime}

⏳ 1M expiry: ${expiry}

EMA 9: ${ema9}
EMA 21: ${ema21}
RSI 14: ${rsi}

Timeframe: M1

Source: Twelve Data

⚠️ Binary-options signal only.
⚠️ NOT Pocket Option OTC data.
⚠️ No signal is guaranteed.`;
}

// ========================================
// PREVENT DUPLICATES
// ========================================

const lastSignals = {};

// ========================================
// CHECK ONE MARKET
// ========================================

async function checkSymbol(symbol) {
  try {
    const candles =
      await getCandles(symbol);

    const data =
      generateSignal(candles);

    if (!data) {
      console.log(
        `${symbol}: No qualifying signal`
      );

      return;
    }

    const signalKey =
      `${symbol}-${data.candleTime}-${data.signal}`;

    if (
      lastSignals[symbol] === signalKey
    ) {
      return;
    }

    lastSignals[symbol] = signalKey;

    const message =
      formatSignal(symbol, data);

    console.log(message);

    await sendTelegram(message);

    console.log(
      `Telegram signal sent: ${symbol} ${data.signal}`
    );

  } catch (error) {
    console.error(
      `${symbol} ERROR:`,
      error.response?.data ||
      error.message
    );
  }
}

// ========================================
// CHECK ALL MARKETS
// ========================================

async function checkAllMarkets() {
  console.log(
    `Checking ${SYMBOLS.length} binary-options markets...`
  );

  for (const symbol of SYMBOLS) {
    await checkSymbol(symbol);
  }
}

// ========================================
// START BOT
// ========================================

console.log("================================");
console.log("BINARY OPTIONS SIGNAL BOT");
console.log("================================");
console.log("Timeframe: M1");
console.log("Strategy: EMA 9/21 + RSI 14");
console.log("Source: Twelve Data");
console.log("Markets:");

SYMBOLS.forEach(symbol => {
  console.log(`- ${symbol}`);
});

console.log("================================");

checkAllMarkets();

// Check every minute
setInterval(
  checkAllMarkets,
  60 * 1000
);
