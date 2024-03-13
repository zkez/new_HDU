import ctypes
import os
import shutil
import time
import cv2
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from macro import PLUGIN_LIBRARY, car_engine_file_path, armor_engine_file_path
from detect.detect import YoLov8TRT, InferCameraThread, locations
from camera.camera import CameraThread

if __name__ == "__main__":
    ctypes.CDLL(PLUGIN_LIBRARY)

    categories = ["B1", "B2", "B3", "B4", "B5", "B7", "R1", "R2", "R3", "R4", "R5", "R7"]
    if os.path.exists('output/'):
        shutil.rmtree('output/')
    os.makedirs('output/')

    YOLOv8_car = YoLov8TRT(car_engine_file_path)
    YOLOv8_armor = YoLov8TRT(armor_engine_file_path)
    for i in range(10):
        car_batch_image_raw, use_time_car, *a_car = YOLOv8_car.infer(YOLOv8_car.get_raw_image_zeros())
        armor_batch_image_raw, use_time_armor, *a_armor = YOLOv8_armor.infer(YOLOv8_armor.get_raw_image_zeros())

    cap = CameraThread(0)
    try:
        while True:
            t1 = time.time()
            ret, frame = cap.read()
            if ret:
                InferCameraThread(YOLOv8_car, YOLOv8_armor, frame)
                print(locations)
            else:
                break
            cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
            cv2.imshow('frame', frame)
            cv2.waitKey(1)
            print('fps->{:.2f}'.format(1 / (time.time() - t1)))

    finally:
        YOLOv8_car.destroy()
        YOLOv8_armor.destroy()
