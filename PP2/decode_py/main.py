import threading
import time
import signal
import sys
import os

WEIGHT = 100
HEIGHT = 100
TOTAL_PIXELS = WEIGHT * HEIGHT
TEST_KEYS = [88, 222, 5, 934]

progress = [0, 0, 0, 0]
progress_lock = threading.Lock()
time_ms = 0
should_continue = True

def decode_image(key_index):
    key = TEST_KEYS[key_index]
    
    try:
        with open("encrypt.bin", "rb") as encrypted_file:
            os.makedirs("outputs", exist_ok=True)
            
            ppm_filename = f"outputs/output_{key}.ppm"
            txt_filename = f"outputs/output_{key}.txt"
            
            with open(ppm_filename, "wb") as ppm_file, open(txt_filename, "w") as txt_file:
                # write PPM header
                ppm_header = f"P6\n{WEIGHT} {HEIGHT}\n255\n"
                ppm_file.write(ppm_header.encode())
                
                for _ in range(TOTAL_PIXELS):
                    pixel_data = encrypted_file.read(3)
                    if len(pixel_data) != 3:
                        break
                    
                    # convert to integers
                    r_enc, g_enc, b_enc = pixel_data
                    
                    key_byte = key & 0xFF  
                    r_dec = r_enc ^ key_byte
                    g_dec = g_enc ^ key_byte
                    b_dec = b_enc ^ key_byte
                    
                    # write to PPM file
                    ppm_file.write(bytes([r_dec, g_dec, b_dec]))
                    
                    # write to TXT file
                    txt_file.write(f"{r_dec} {g_dec} {b_dec}\n")
                    
                    with progress_lock:
                        progress[key_index] += 1
                    
                    # time.sleep(0.0002)  # 200 microseconds   0.0002

            print(f"Thread {key_index} finished", flush=True)
            time.sleep(0.002)   # 2 milliseconds is enough
                    
    except FileNotFoundError as e:
        print(f"Error: encrypt.bin not found at {os.path.abspath('encrypt.bin')}")
        print(f"Current directory: {os.getcwd()}")
    except Exception as e:
        print(f"Error in thread {key_index}: {e}")
        import traceback
        traceback.print_exc()

def try_test(signum, frame):
    global time_ms
    
    with progress_lock:
        print(f"Timer tick: {time_ms} ms")
        
        for i in range(4):
            percentage = (progress[i] * 100.0) / TOTAL_PIXELS
            print(f"  Thread {i} (key {TEST_KEYS[i]}): {progress[i]}/{TOTAL_PIXELS} pixels ({percentage:.2f}%)")
        
        print()
        time_ms += 200

def main():
    global time_ms
    
    signal.signal(signal.SIGALRM, try_test)
    
    signal.setitimer(signal.ITIMER_REAL, 0.1, 0.2)  
    
    threads = []
    for i in range(4):
        thread = threading.Thread(target=decode_image, args=(i,))
        threads.append(thread)
        thread.start()
        print(f"Started thread {i} with key {TEST_KEYS[i]}", flush=True)
    
    sleep(1)  # Allow threads to start properly

    for thread in threads:
        thread.join()
    
    signal.setitimer(signal.ITIMER_REAL, 0)
    
    print("\nFinal results:")
    for i in range(4):
        percentage = (progress[i] * 100.0) / TOTAL_PIXELS
        print(f"  Thread {i} (key {TEST_KEYS[i]}): {progress[i]}/{TOTAL_PIXELS} pixels ({percentage:.2f}%)")
    
    print("\nDone!")

if __name__ == "__main__":
    main()