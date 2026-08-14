console.log("Pocket Option Signal Bot");
console.log("========================");
console.log("Market: EUR/USD OTC");
console.log("Timeframe: M1");
console.log("Strategy: EMA + RSI");
console.log("Status: ACTIVE");

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

  console.log(`Price: ${price}`);
  console.log(`EMA: ${ema.toFixed(5)}`);
  console.log(`RSI: ${rsi.toFixed(2)}`);
  console.log(`Signal: ${signal}`);
  console.log("Waiting for next signal...");
}

generateSignal();

setInterval(generateSignal, 60000);

const http = require("http");

const PORT = process.env.PORT || 10000;

http.createServer((req, res) => {
  res.writeHead(200);
  res.end("Pocket Option Bot is running");
}).listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
const http = require("http");

const PORT = process.env.PORT || 10000;

http.createServer((req, res) => {
  res.writeHead(200);
  res.end("Pocket Option Bot is running");
}).listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
