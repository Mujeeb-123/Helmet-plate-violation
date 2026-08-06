from ultralytics import YOLO
import cv2
import easyocr
from database.db import get_connection
from difflib import SequenceMatcher
import os
import re


model=YOLO("model/best.pt")
reader=easyocr.Reader(['en'],gpu=False)


def process_video(video_path):

    cap = cv2.VideoCapture(video_path)

    output_path = "static/output/output.mp4"

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    out = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    frame_count = 0
    saved_plates = []
    last_saved_frame = -1000
    SAVE_AFTER = 90      # ~3 sec for 30 FPS (adjust if needed)

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1

        results = model(frame, imgsz=640, conf=0.35)

        annotated_frame = results[0].plot()

        boxes = results[0].boxes

        plate_box = None
        violations = []

        for box in boxes:
            cls = int(box.cls[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if cls == 0:
                plate_box = (x1, y1, x2, y2)
            elif cls == 2:
                violations.append("WithoutHelmet")
            elif cls == 3:
                violations.append("TripleRiding")

        # OCR
        
        if plate_box is not None and len(violations) > 0:

            x1, y1, x2, y2 = plate_box

            margin = 5

            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(frame.shape[1], x2 + margin)
            y2 = min(frame.shape[0], y2 + margin)

            plate = frame[y1:y2, x1:x2]

            ocr_result = reader.readtext(plate)

            if len(ocr_result) > 0:

                best = max(ocr_result, key=lambda x: x[2])

                plate_number = best[1]
                confidence = best[2]

                # Clean OCR text
                plate_number = plate_number.upper()
                plate_number = re.sub(r'[^A-Z0-9]', '', plate_number)

                if confidence > 0.40:
                    duplicate = False

                    for saved in saved_plates:

                        similarity = SequenceMatcher(None, plate_number, saved).ratio()

                        if similarity > 0.80:
                            duplicate = True
                            break

                    # 3-second cooldown
                    if frame_count - last_saved_frame < SAVE_AFTER:
                        duplicate = True

                    if duplicate:
                        continue

                    saved_plates.append(plate_number)
                    last_saved_frame = frame_count

                    violation_text = ", ".join(set(violations))

                    # Save full frame
                    frame_name = f"{plate_number}_{frame_count}.jpg"
                    frame_path = os.path.join("static", "violations", frame_name)

                    cv2.imwrite(frame_path, frame)

                    # Save cropped plate
                    plate_name = f"{plate_number}_{frame_count}.jpg"
                    plate_path = os.path.join("static", "plates", plate_name)

                    cv2.imwrite(plate_path, plate)

                    conn = get_connection()

                    query = """
                    INSERT INTO violations
                    (
                        plate_number,
                        violation_type,
                        image_path,
                        plate_image,
                        violation_time
                    )
                    VALUES (%s,%s,%s,%s,NOW())
                    """

                    values = (
                        plate_number,
                        violation_text,
                        frame_path,
                        plate_path
                    )

                    if conn is None:
                        print("Database connection failed")
                    else:
                        cursor = conn.cursor()
                        cursor.execute(query, values)
                        conn.commit()
                        cursor.close()
                        conn.close()

                    print("=" * 50)
                    print("Plate :", plate_number)
                    print("Violation :", violation_text)
                    print("Confidence :", round(confidence, 2))

        out.write(annotated_frame)

    cap.release()
    out.release()

    return "output/output.mp4"