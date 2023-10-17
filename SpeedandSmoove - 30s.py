import numpy as np
import cv2
from tkinter import filedialog
from tqdm import tqdm
import time
import os
import math
from concurrent.futures import ThreadPoolExecutor

def process_video(args):
    try:
        input_filename, _ = args  # speed_up_factor is ignored
        cap = cv2.VideoCapture(input_filename)

        # Calculate original video duration
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        original_duration = total_frames / fps
        
        # Check for minimum duration and skip processing if less than 120s
        if original_duration < 120:
            print(f"Skipping {input_filename} as it is shorter than 120 seconds.")
            return
        
        # Decide whether to adjust speed_up_factor
        if original_duration > 120:
            desired_duration = 30  # seconds
            speed_up_factor = math.ceil(original_duration / desired_duration)
        else:
            return
        
        base, ext = os.path.splitext(input_filename)
        output_filename = f"{base}_{speed_up_factor}x_timelapse{ext}"

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_filename, fourcc, 30, (int(cap.get(3)), int(cap.get(4))))

        print(f"Processing {input_filename} with batch size of {speed_up_factor}")

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

        if running_sum is not None:
            avg_frame = (running_sum / count).astype(np.uint8)
            out.write(avg_frame)

        cap.release()
        out.release()
        print(f"Processing completed for {input_filename}. Output saved as {output_filename}")

    except Exception as e:
        print(f"An error occurred while processing {input_filename}: {e}")

def main():
    try:
        filenames = filedialog.askopenfilenames(filetypes=[("MP4 files", "*.mp4")])

        num_files = len(filenames)
        num_cores = os.cpu_count()
        print(f"Detected {num_cores} CPU cores.")
        
        if num_files <= num_cores:
            print(f"Processing {num_files} videos sequentially.")
            for filename in tqdm(filenames, desc="Overall Progress", unit="file"):
                process_video((filename, None))
        else:
            chunk_size = num_files // num_cores
            print(f"Processing videos in {num_cores} chunks with each chunk having {chunk_size} videos.")
            with ThreadPoolExecutor(max_workers=num_cores) as executor:
                list(tqdm(executor.map(process_video, [(filename, None) for filename in filenames]), total=len(filenames), desc="Overall Progress", unit="file"))

        print("All processing completed.")
        print(input)
    except Exception as e:
        print(f"An error occurred: {e}")
        print(input)

if __name__ == "__main__":
    main()
