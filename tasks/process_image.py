import cv2
import numpy as np
import redis
import rq

# Places on picture from camera where the dice is (% of width and height for resolution-agnostic)
scale_x1, scale_x2 = 0.395, 0.555
scale_y1, scale_y2 = 0.427, 0.697

conn = redis.Redis()
queue_images = rq.Queue('images', connection=conn)


def process_image():
    current_job = rq.get_current_job(conn)
    print(current_job)
    image_job_id = current_job.dependency.id
    print(image_job_id)
    picture_bytes = queue_images.fetch_job(image_job_id).result
    print(len(picture_bytes))

    img = cv2.imdecode(np.fromstring(picture_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    h, w = img.shape
    x1, x2 = int(w * scale_x1), int(w * scale_x2)
    y1, y2 = int(h * scale_y1), int(h * scale_y2)
    img = img[y1:y2, x1:x2]
    # Upscale image for recognition to work properly
    img = cv2.resize(img, (0, 0), fx=4, fy=4)

    params = cv2.SimpleBlobDetector_Params()
    params.filterByInertia = True
    params.minInertiaRatio = 0.6
    detector = cv2.SimpleBlobDetector_create(params)

    blobs = detector.detect(img)
    kp = cv2.drawKeypoints(img, blobs, np.array([]), (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    return cv2.imencode('.jpg', kp)[1].tobytes()
