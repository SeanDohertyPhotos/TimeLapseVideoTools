import os
import shutil
import cv2
import numpy as np
import math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time

def get_drives():
    drives = [chr(x) + ':' for x in range(65, 91) if os.path.exists(chr(x) + ':\\') and chr(x) not in ['C', 'D', 'Z']]
    return drives

def scan_for_mp4(drives, dest_root):
    mp4_files = []
    total_size = 0
    dates = set()
    durations = {}

    for drive in drives:
        for subdir, _, files in os.walk(drive + '\\'):
            for file in files:
                if file.lower().endswith('.mp4'):
                    full_file_path = os.path.join(subdir, file)
                    timestamp = os.path.getctime(full_file_path)
                    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                    
                    cap = cv2.VideoCapture(full_file_path)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    cap.release()  # Release the VideoCapture object to free up resources
                    
                    if fps > 0:  # Check to ensure fps is not zero
                        original_duration = total_frames / fps
                        durations[full_file_path] = original_duration
                        
                        dest_folder = os.path.join(dest_root, date_str)
                        dest_path = os.path.join(dest_folder, os.path.basename(full_file_path))
                        
                        file_size = os.path.getsize(full_file_path)
                        mp4_files.append(full_file_path)
                        total_size += file_size
                        dates.add(date_str)
                    else:
                        print(f"Skipping {full_file_path} due to zero fps value.")

    return mp4_files, total_size, dates, durations

def process_video(args):
    input_filename, output_filename = args
    cap = cv2.VideoCapture(input_filename)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    original_duration = total_frames / fps

    if original_duration > 120:
        desired_duration = 30  # seconds
        speed_up_factor = math.ceil(original_duration / desired_duration)
    else:
        return
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_filename, fourcc, 30, (int(cap.get(3)), int(cap.get(4))))

    running_sum = None
    count = 0

    for _ in tqdm(range(total_frames), desc=f"Processing {input_filename}", unit="frame", unit_scale=True):
        ret, frame = cap.read()
        if not ret:
            break

        if running_sum is None:
            running_sum = np.array(frame, dtype=np.float64)
        else:
            running_sum += frame
        
        count += 1
        if count == speed_up_factor:
            avg_frame = (running_sum / count).astype(np.uint8)
            out.write(avg_frame)
            running_sum = None
            count = 0

    if count > 0:  # Process remaining frames
        avg_frame = (running_sum / count).astype(np.uint8)
        out.write(avg_frame)

    cap.release()
    out.release()

def move_mp4_file(file_path, dest_root, durations):
    timestamp = os.path.getctime(file_path)
    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    
    dest_folder = os.path.join(dest_root, date_str)
    dest_path = os.path.join(dest_folder, os.path.basename(file_path))
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    
    if durations[file_path] > 120:
        output_filename = os.path.join(dest_folder, f"speedup_{os.path.basename(file_path)}")
        process_video((file_path, output_filename))
        # No need to move or copy the original file, as the sped-up version is already created in the destination folder
    else:
        shutil.move(file_path, dest_path)  # Move the file if its duration is less than 120 seconds
    
    new_file_size = os.path.getsize(dest_path) if durations[file_path] <= 120 else os.path.getsize(output_filename)
    return new_file_size  # Return the size of the new file for accumulation


if __name__ == "__main__":
    print("Scanning drives...")
    start_time = time.time()  # Store the start time
    drives = get_drives()
    dest_root = os.path.join('D:', 'video', 'Starbase Video')
    mp4_files, original_total_size, dates, durations = scan_for_mp4(drives, dest_root)
    
    print(f"Drives found: {', '.join(drives)}")
    print(f"New .mp4 files to be moved: {len(mp4_files)}")
    print(f"Original total size of new files: {original_total_size / (1024 * 1024 * 1024):.2f} GB")

    # Move files in parallel
    with ThreadPoolExecutor() as executor:
        new_file_sizes = list(tqdm(executor.map(lambda file: move_mp4_file(file, dest_root, durations), mp4_files), desc="Moving files", total=len(mp4_files), unit="file"))
    
    new_total_size = sum(new_file_sizes)  # Sum the sizes of all new files
    print(f"New total size of processed files: {new_total_size / (1024 * 1024 * 1024):.2f} GB")

    end_time = time.time()  # Store the end time
    total_processing_time = end_time - start_time  # Calculate total processing time
    print(f"Total processing time: {total_processing_time:.2f} seconds")

    print("Files moved successfully!")
    input('Press enter to close program.')


