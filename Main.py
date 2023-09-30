import cv2
import numpy as np
import threading
from tkinter import filedialog, simpledialog, Tk, ttk, Label
from queue import Queue


def process_video(input_filename, output_filename, speed_up_factor, queue):
    cap = cv2.VideoCapture(input_filename)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_filename, fourcc, fps, (frame_width, frame_height))

    frames = []
    for i in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        if len(frames) == speed_up_factor:
            avg_frame = np.mean(frames, axis=0).astype(np.uint8)
            out.write(avg_frame)
            frames = []
        queue.put((i + 1, total_frames))

    if frames:
        avg_frame = np.mean(frames, axis=0).astype(np.uint8)
        out.write(avg_frame)

    cap.release()
    out.release()
    queue.put("done")


def update_ui(queue, progress, label):
    while True:
        message = queue.get()
        if message == "done":
            label.config(text="Processing completed")
            break
        current_frame, total_frames = message
        progress['value'] = (current_frame / total_frames) * 100
        label.config(text=f"Processing frame {current_frame}/{total_frames}")


def main():
    root = Tk()

    filenames = filedialog.askopenfilenames(filetypes=[("MP4 files", "*.mp4")])
    speed_up_factor = simpledialog.askinteger("Input", "Enter the speed-up factor:")
    output_filename = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])

    progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progress.pack()

    label = Label(root)
    label.pack()

    queue = Queue()
    threads = []
    for filename in filenames:
        t = threading.Thread(target=process_video, args=(filename, output_filename, speed_up_factor, queue))
        t.start()
        threads.append(t)

    ui_thread = threading.Thread(target=update_ui, args=(queue, progress, label))
    ui_thread.start()

    for t in threads:
        t.join()

    ui_thread.join()

    root.mainloop()


if __name__ == "__main__":
    main()
