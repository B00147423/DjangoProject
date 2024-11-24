import aioredis
import asyncio

async def test_redis():
    redis = await aioredis.create_redis_pool("redis://localhost:6379")
    try:
        # Test BZPOPMIN to see if it's recognized
        await redis.bzpopmin("test_key", timeout=1)
    except Exception as e:
        print("Error:", e)
    finally:
        redis.close()
        await redis.wait_closed()

asyncio.run(test_redis())