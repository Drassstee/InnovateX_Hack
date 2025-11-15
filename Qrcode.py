import cv2
import numpy as np

# Load your image
img = cv2.imread("my_image.jpg")  # ← change to your image file

detector = cv2.QRCodeDetector()

# Detect and decode
value, points, _ = detector.detectAndDecode(img)

if value != "":
    points = points[0]  # simplify array

    # Points come in order: top-left, top-right, bottom-right, bottom-left
    x1, y1 = int(points[0][0]), int(points[0][1])
    x2, y2 = int(points[2][0]), int(points[2][1])

    # Draw box
    cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)

    # Print detected value
    print("QR Value:", value)

    # Draw value on image
    cv2.putText(img, value, (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
else:
    print("No QR code detected.")

# Show image
cv2.imshow("Image QR Detection", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
