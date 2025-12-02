import threading
import time
import signal
import sys
import os

WEIGHT = 100
HEIGHT = 100
TOTAL_PIXELS = WEIGHT * HEIGHT
TEST_KEYS = [88, 222, 5, 934]

# Shared progress counter with thread safety
progress = [0, 0, 0, 0]
progress_lock = threading.Lock()
time_ms = 0
should_continue = True

def decode_image(key_index):
    key = TEST_KEYS[key_index]
    
    try:
        # Read encrypted file
        # Note: The test script runs from test/ directory, so encrypt.bin should be there
        with open("encrypt.bin", "rb") as encrypted_file:
            # Create output directory if it doesn't exist
            os.makedirs("outputs", exist_ok=True)
            
            # Create output files
            ppm_filename = f"outputs/output_{key}.ppm"
            txt_filename = f"outputs/output_{key}.txt"
            
            with open(ppm_filename, "wb") as ppm_file, open(txt_filename, "w") as txt_file:
                # Write PPM header
                ppm_header = f"P6\n{WEIGHT} {HEIGHT}\n255\n"
                ppm_file.write(ppm_header.encode())
                
                for _ in range(TOTAL_PIXELS):
                    # Read 3 bytes (RGB)
                    pixel_data = encrypted_file.read(3)
                    if len(pixel_data) != 3:
                        break
                    
                    # Convert to integers
                    r_enc, g_enc, b_enc = pixel_data
                    
                    # IMPORTANT: The key is applied differently!
                    # Based on typical XOR encryption, we should apply the same key byte to all channels
                    # OR apply different parts of the key to different channels
                    # Let's try the simple approach first: same key for all channels
                    key_byte = key & 0xFF  # Use only the lowest byte
                    r_dec = r_enc ^ key_byte
                    g_dec = g_enc ^ key_byte
                    b_dec = b_enc ^ key_byte
                    
                    # Alternative: If that doesn't work, try using the full key mod 256
                    # r_dec = r_enc ^ (key % 256)
                    # g_dec = g_enc ^ (key % 256)
                    # b_dec = b_enc ^ (key % 256)
                    
                    # Write to PPM file
                    ppm_file.write(bytes([r_dec, g_dec, b_dec]))
                    
                    # Write to TXT file
                    txt_file.write(f"{r_dec} {g_dec} {b_dec}\n")
                    
                    # Update progress
                    with progress_lock:
                        progress[key_index] += 1
                    
                    # Wait 200 microseconds
                    time.sleep(0.0002)  # 200 microseconds
                    
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
    
    # Set up signal handler for timer
    signal.signal(signal.SIGALRM, try_test)
    
    # Configure timer: first tick at 100ms, then every 200ms
    signal.setitimer(signal.ITIMER_REAL, 0.1, 0.2)  # 100ms initial, 200ms interval
    
    # Create and start threads
    threads = []
    for i in range(4):
        thread = threading.Thread(target=decode_image, args=(i,))
        threads.append(thread)
        thread.start()
        print(f"Started thread {i} with key {TEST_KEYS[i]}")
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Disable timer
    signal.setitimer(signal.ITIMER_REAL, 0)
    
    # Final progress report
    print("\nFinal results:")
    for i in range(4):
        percentage = (progress[i] * 100.0) / TOTAL_PIXELS
        print(f"  Thread {i} (key {TEST_KEYS[i]}): {progress[i]}/{TOTAL_PIXELS} pixels ({percentage:.2f}%)")
    
    print("\nDone!")

if __name__ == "__main__":
    main()