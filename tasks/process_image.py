import cv2
import datetime
import numpy as np
import redis
import rq

# Places on picture from camera where the dice is (% of width and height for resolution-agnostic)
scale_x1, scale_x2 = 0.395, 0.555
scale_y1, scale_y2 = 0.427, 0.650  # Cut off the screw in the cup

conn = redis.Redis()
queue_images = rq.Queue('images', connection=conn)


def process_image():
    current_job = rq.get_current_job(conn)
    image_job_id = current_job.dependency.id
    picture_bytes = queue_images.fetch_job(image_job_id).result

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
    if len(blobs) < 1 or len(blobs) > 6:
        name = f'failed/{current_job.id}'
        # Write all images down for analysis in future
        cv2.imwrite(f'{name}-orig.jpg', cv2.imdecode(np.fromstring(picture_bytes, np.uint8), cv2.IMREAD_COLOR))
        cv2.imwrite(f'{name}-anal.jpg', kp)
        raise Exception("There is wrong number of dots!")
    return {
        'number': len(blobs),
        'original_image': picture_bytes,
        'kp_image': cv2.imencode('.jpg', kp)[1].tobytes(),
        'finished_time': datetime.datetime.now().timestamp(),  # Idk if this is available somewhere in job data
    }
