# Pocket Option OTC signal bot
# Markets: EUR/USD OTC, AUD/CAD OTC, AED/CNY OTC, AUD/NZD OTC

OTC_MARKETS = [
    "EURUSD_otc",
    "AUDCAD_otc",
    "AEDCNY_otc",
    "AUDNZD_otc",
]

print("Pocket Option OTC bot starting...")
print("OTC markets loaded:")
for market in OTC_MARKETS:
    print(market)
print("Waiting for OTC market data...")
