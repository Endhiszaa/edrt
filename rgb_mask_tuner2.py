import sys
import cv2
import numpy as np

WINDOW = "RGB Mask Tuner"
CHANNELS = ("R", "G", "B")

def noop(_):
    pass

def fit(img):
    h, w = img.shape[:2]
    scale = min(1.0, 640 / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    return img

def main():
    cap = None
    args = sys.argv[1:]
    if not args or args[0] == "--cam":
        index = int(args[1]) if len(args) > 1 else 0
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
        if not cap.isOpened():
            sys.exit(f"Could not open camera {index}")
    else:
        img = cv2.imread(args[0])
        if img is None:
            sys.exit(f"Could not read image: {args[0]}")
        img = fit(img)
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    for c in CHANNELS:
        cv2.createTrackbar(f"{c} min", WINDOW, 0, 255, noop)
        cv2.createTrackbar(f"{c} max", WINDOW, 255, 255, noop)
    mins, maxs = [0, 0, 0], [255, 255, 255]
    failed_reads = 0
    while True:
        if cap is not None:
            ok, frame = cap.read()
            if not ok:
                failed_reads += 1
                if failed_reads > 50:
                    print("Lost camera feed")
                    break
                cv2.waitKey(30)
                continue
            failed_reads = 0
            img = fit(frame)
        mins = [cv2.getTrackbarPos(f"{c} min", WINDOW) for c in CHANNELS]
        maxs = [cv2.getTrackbarPos(f"{c} max", WINDOW) for c in CHANNELS]
        lower = np.array(mins[::-1], dtype=np.uint8)
        upper = np.array(maxs[::-1], dtype=np.uint8)
        mask = cv2.inRange(img, lower, upper)
        result = cv2.bitwise_and(img, img, mask=mask)
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        cv2.imshow(WINDOW, np.hstack([img, mask_bgr, result]))
        key = cv2.waitKey(30) & 0xFF
        if key == ord("p"):
            print(f"lower_rgb = {mins}, upper_rgb = {maxs}")
            print(f"lower_bgr = np.array({mins[::-1]}), upper_bgr = np.array({maxs[::-1]})")
        elif key in (ord("q"), 27):
            break
        if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            break
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print(f"Final: lower_rgb = {mins}, upper_rgb = {maxs}")

if __name__ == "__main__":
    main()
