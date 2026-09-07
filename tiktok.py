import time
import random
import subprocess

def warm_up_account(device_id: str, duration_minutes: int = 10):
    """Имитация активного пользователя (прогрев аккаунта)"""
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    while time.time() < end_time:
        subprocess.run(["adb", "-s", device_id, "shell", "input", "swipe", "500", "1500", "500", "500", "300"])
        time.sleep(5)

def anti_shadowban_upload(device_id: str, video_path: str, caption: str):
    """Загрузка видео с антифрод-задержками для обхода теневого бана"""
    try:
        remote_path = "/sdcard/Download/video_to_post.mp4"
        subprocess.run(["adb", "-s", device_id, "push", video_path, remote_path])
        time.sleep(2)
        
        time.sleep(random.uniform(3.0, 7.0))
        
        for char in caption:
            subprocess.run(["adb", "-s", device_id, "shell", "input", "text", char])
            time.sleep(random.uniform(0.05, 0.2))
            
        return True
    except Exception as e:
        return False
