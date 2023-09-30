import cv2
import numpy as np
import threading
from tkinter import filedialog
from tqdm import tqdm
import os


def process_video(input_filename, speed_up_factor):
    # Open the video file.
    cap = cv2.VideoCapture(input_filename)

    # Generate the output filename.
    base, ext = os.path.splitext(input_filename)
    output_filename = f"{base}_{speed_up_factor}x_timelapse{ext}"

    # Get the total number of frames in the video.
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Create a VideoWriter object to write the output video.
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_filename, fourcc, 30, (int(cap.get(3)), int(cap.get(4))))

    frames = []
    for _ in tqdm(range(total_frames), desc=f"Processing {input_filename}"):
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        if len(frames) == speed_up_factor:
            avg_frame = np.mean(frames, axis=0).astype(np.uint8)
            out.write(avg_frame)
            frames = []

    # If there are any remaining frames, average and write them.
    if frames:
        avg_frame = np.mean(frames, axis=0).astype(np.uint8)
        out.write(avg_frame)

    # Release the VideoCapture and VideoWriter objects.
    cap.release()
    out.release()
    print(f"Processing completed for {input_filename}. Output saved as {output_filename}")


def main():
    # Ask the user for the speed-up factor.
    speed_up_factor = int(input("Enter the speed-up factor: "))

    # Show an "Open" dialog box and return the path to the selected file(s).
    filenames = filedialog.askopenfilenames(filetypes=[("MP4 files", "*.mp4")])

    threads = []
    for filename in filenames:
        t = threading.Thread(target=process_video, args=(filename, speed_up_factor))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("All processing completed.")


if __name__ == "__main__":
    main()
