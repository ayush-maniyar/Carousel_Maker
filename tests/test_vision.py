import cv2
import os
import numpy as np # Adding this for the math part

def quick_opencv_test():
    print("--- OpenCV System Diagnostic ---")
    
    # 1. Check Library Version
    print(f"OpenCV Version: {cv2.__version__}")
    
    # 2. Test Image Creation (The part that failed)
    # We take 10,000 random bytes and turn them into a 100x100 square image
    random_data = os.urandom(10000)
    flat_array = np.frombuffer(random_data, dtype=np.uint8) # The Fix
    test_img = flat_array.reshape(100, 100)
    
    if cv2.imwrite("io_test.jpg", test_img):
        print("Success: Basic Disk I/O (Writing images) is working.")
        os.remove("io_test.jpg")
    
    # 3. Test Video File Access
    target_video = "temp_video.mp4" 
    
    if os.path.exists(target_video):
        print(f"Found {target_video}. Testing frame extraction...")
        cap = cv2.VideoCapture(target_video)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite("diagnostic_frame.jpg", frame)
            print("Success: OpenCV successfully read and extracted a frame!")
        else:
            print("Error: OpenCV found the file but could not read it. Check codecs.")
        cap.release()
    else:
        print("Note: temp_video.mp4 not found. Run prepare_test.py first!")

    print("--- Diagnostic Complete ---")

if __name__ == "__main__":
    quick_opencv_test() 