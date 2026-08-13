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
