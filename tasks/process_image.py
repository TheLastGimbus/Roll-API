"""
This is the task that takes already-taken image, and analyzes it to find dots
It could have different implementations - like Tensorflow, if your dice is in more extreme image-conditions
Now, it implements OpenCV's cv2.SimpleBlobDetector, because it's super fast and almost 100% successful
"""
import cv2
import datetime
import numpy as np
import os
import redis
import rq

# Places on picture from camera where the dice is (% of width and height for resolution-agnostic)
# This is VERY IMPORTANT - you need to cut out all the crap from the image, or otherwise, the detector will detect
# other crap as dice dots
# You can set them as env variables, if you don't want to modify the code
scale_x1, scale_x2 = float(os.getenv('ROLLAPI_CAM_SCALE_X1', 0.395)), float(os.getenv('ROLLAPI_CAM_SCALE_X2', 0.555))
scale_y1, scale_y2 = float(os.getenv('ROLLAPI_CAM_SCALE_Y2', 0.427)), float(os.getenv('ROLLAPI_CAM_SCALE_Y2', 0.650))

conn = redis.Redis()
queue_images = rq.Queue('images', connection=conn)


def process_image():
    # Get parent job to get it's output image
    current_job = rq.get_current_job(conn)
    image_job_id = current_job.dependency.id
    picture_bytes = queue_images.fetch_job(image_job_id).return_value()

    original_img = cv2.imdecode(np.fromstring(picture_bytes, np.uint8))
    img = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape
    x1, x2 = int(w * scale_x1), int(w * scale_x2)
    y1, y2 = int(h * scale_y1), int(h * scale_y2)
    img = img[y1:y2, x1:x2]  # Cut out the crap to get only the dice
    img = cv2.resize(img, (0, 0), fx=4, fy=4)  # Upscale image for recognition to work properly

    params = cv2.SimpleBlobDetector_Params()
    params.filterByInertia = True  # Find round stuff
    params.minInertiaRatio = 0.6  # Yes, round indeed
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
        'original_image': cv2.imencode('.webp', original_img, [cv2.IMWRITE_WEBP_QUALITY, 90])[1].tobytes(),
        'kp_image': cv2.imencode('.webp', kp, [cv2.IMWRITE_WEBP_QUALITY, 90])[1].tobytes(),  # Image with anal data
        'finished_time': datetime.datetime.now().timestamp(),  # Idk if this is available somewhere in job data
    }
