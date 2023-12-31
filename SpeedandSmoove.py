import numpy as np
import cv2
from tkinter import filedialog
from tqdm import tqdm
import time
import os

def process_video(args):
    try:
        input_filename, speed_up_factor = args
        cap = cv2.VideoCapture(input_filename)

        base, ext = os.path.splitext(input_filename)
        output_filename = f"{base}_{speed_up_factor}x_timelapse{ext}"

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_filename, fourcc, 30, (int(cap.get(3)), int(cap.get(4))))

        print(f"Processing {input_filename} with batch size of {speed_up_factor}")

        running_sum = None
        count = 0

        start_time = time.time()
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

        end_time = time.time()
        processing_time = end_time - start_time
        fps = total_frames / processing_time

        if running_sum is not None:
            avg_frame = (running_sum / count).astype(np.uint8)
            out.write(avg_frame)

        cap.release()
        out.release()
        print(f"Processing completed for {input_filename}. Output saved as {output_filename}")
        print(f"Processed at {fps:.2f} frames/sec")
    except Exception as e:
        print(f"An error occurred while processing {args[0]}: {e}")

def main():
    try:
        speed_up_factor = int(input("Enter the speed-up factor: "))
        filenames = filedialog.askopenfilenames(filetypes=[("MP4 files", "*.mp4")])

        print(f"Processing videos sequentially.")

        for filename in filenames:
            process_video((filename, speed_up_factor))

        print("All processing completed.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
