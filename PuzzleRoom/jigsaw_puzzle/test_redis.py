import redis

def test_redis():
    try:
        redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        response = redis_client.ping()
        assert response is True
        print("Redis connection successful.")
    except Exception as e:
        print(f"Redis connection failed: {e}")
