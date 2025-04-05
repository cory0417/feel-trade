import math
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

latest_prices = {}
data_lock = threading.Lock()


def generate_price(x: float) -> float:
    return 1.2 * (5 * math.sin(x) - 3 * math.sin(2 * x) + 7 * math.cos(1.5 + x)) + 100


def start_price_generator(symbol="SYNTH"):
    def updater():
        x = 0.0
        while True:
            price = generate_price(x)
            with data_lock:
                latest_prices[symbol.upper()] = round(price, 4)
            x += 0.1
            time.sleep(1)

    thread = threading.Thread(target=updater, daemon=True)
    thread.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_price_generator()  # starts updating "SYNTH"
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/stock/{symbol}")
async def get_stock_price(symbol: str):
    with data_lock:
        price = latest_prices.get(symbol.upper())
    if price is None:
        raise HTTPException(status_code=404,
                            detail="Symbol not found or not updated yet")
    return {"symbol": symbol.upper(), "price": price}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
