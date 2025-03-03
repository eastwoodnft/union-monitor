import asyncio
from monitor import monitor

if __name__ == "__main__":
    print("Starting bot...")
    asyncio.run(monitor())
