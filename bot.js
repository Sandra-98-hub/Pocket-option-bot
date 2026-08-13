console.log("Pocket Option Signal Bot");
console.log("========================");
console.log("Market: OTC M1");
console.log("Status: ACTIVE");

function generateSignal() {
  const signals = ["BUY", "SELL"];
  const signal = signals[Math.floor(Math.random() * signals.length)];

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
