from ultralytics import YOLO
import cv2
from database.db import get_connection
from datetime import datetime
import os

helmet_model = YOLO("helmet_best.pt")


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
    saved_violation = False

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1

        results = helmet_model(frame, conf=0.25)

        for box in results[0].boxes:

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            cls = int(box.cls[0])

            label = helmet_model.names[cls]

            conf = float(box.conf[0])

            if label == "With Helmet":
                color = (0, 255, 0)
            else:
                color = (0, 0, 255)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            cv2.putText(
                frame,
                f"{label} {conf:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

            # Violation
            if label == "Without Helmet":
                if saved_violation:
                    continue

                filename = datetime.now().strftime(
                    "%Y%m%d_%H%M%S_%f.jpg"
                )

                image_path = (
                    f"static/violations/{filename}"
                )

                cv2.imwrite(
                    image_path,
                    frame
                )

                conn = get_connection()
                cursor = conn.cursor()

                query = """
                INSERT INTO violations
                (
                    plate_number,
                    violation_type,
                    image_path,
                    violation_time
                )
                VALUES
                (%s,%s,%s,NOW())
                """

                values = (
                    "UNKNOWN",
                    "No Helmet",
                    image_path
                )

                cursor.execute(
                    query,
                    values
                )

                conn.commit()

                cursor.close()
                conn.close()

                saved_violation = True
                
        out.write(frame)

    cap.release()
    out.release()

    return "output/output.mp4"