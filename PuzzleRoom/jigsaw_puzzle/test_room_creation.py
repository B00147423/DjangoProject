# test_realtime_sync.py (Selenium with threading)
from selenium import webdriver
from threading import Thread
import time

def user1_actions():
    driver = webdriver.Chrome()
    driver.get("http://localhost:8000/room/test_room_id")
    time.sleep(2)
    piece = driver.find_element(By.ID, "piece-1")
    piece.click()
    print("User 1 moved piece-1")

def user2_monitor():
    driver = webdriver.Chrome()
    driver.get("http://localhost:8000/room/test_room_id")
    time.sleep(5)  # Wait for User 1's action
    piece = driver.find_element(By.ID, "piece-1")
    assert "moved" in piece.get_attribute("class")
    print("User 2 detected piece-1 movement")

Thread(target=user1_actions).start()
Thread(target=user2_monitor).start()