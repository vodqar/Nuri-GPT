import json
from app.services.vision import VisionService

try:
    with open("app/services/vision.py", "r") as f:
        print("Vision service loaded")
except Exception as e:
    print(e)
