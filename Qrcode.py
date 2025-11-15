import cv2

def read_qr_from_image(path):
    """
    Reads a QR code from an image file.
    Returns (value, img_with_box)
    """

    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {path}")

    detector = cv2.QRCodeDetector()
    value, points, _ = detector.detectAndDecode(img)

    if value and points is not None:
        pts = points[0]  # simplify shape
        x1, y1 = int(pts[0][0]), int(pts[0][1])
        x2, y2 = int(pts[2][0]), int(pts[2][1])

        cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.putText(img, value, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    return value, img
