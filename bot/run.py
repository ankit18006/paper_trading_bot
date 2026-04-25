import time
import subprocess

while True:
    subprocess.run(["python", "-m", "bot.cli", "order",
                    "--symbol", "BTCUSDT", "--side", "BUY",
                    "--type", "MARKET", "--quantity", "0.001"])
    print("Sleeping 60s...")
    time.sleep(60)
