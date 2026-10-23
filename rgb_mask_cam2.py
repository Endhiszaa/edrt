import sys

import cv2
import numpy as np

LOWER_RGB = [15, 53, 56]
UPPER_RGB = [84, 89, 92]

WINDOW = "RGB Mask Cam"

MIN_AREA = 500


def main():
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
    if not cap.isOpened():
        sys.exit(f"Could not open camera {index}")
    lower = np.array(LOWER_RGB[::-1], dtype=np.uint8)
    upper = np.array(UPPER_RGB[::-1], dtype=np.uint8)
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    failed_reads = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            failed_reads += 1
            if failed_reads > 50:
                print("Lost camera feed")
                break
            cv2.waitKey(30)
            continue
        failed_reads = 0
        mask = cv2.inRange(frame, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            biggest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(biggest) >= MIN_AREA:
                x, y, w, h = cv2.boundingRect(biggest)
                cx, cy = x + w // 2, y + h // 2
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                cv2.putText(frame, f"({cx}, {cy})", (x, y - 8),cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        cv2.imshow(WINDOW, np.hstack([frame, mask_bgr]))
        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            break
        if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
