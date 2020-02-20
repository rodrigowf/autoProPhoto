# OpenCV program to detect face in real time
# import libraries of python OpenCV
# where its functionality resides
# https://www.geeksforgeeks.org/opencv-python-program-face-detection/
import cv2

# load the required trained XML classifiers
# https://github.com/Itseez/opencv/blob/master/
# data/haarcascades/haarcascade_frontalface_default.xml
# Trained XML classifiers describes some features of some
# object we want to detect a cascade function is trained
# from a lot of positive(faces) and negative(non-faces)
# images.
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


def detect_faces(img):
    # convert to gray scale of each frames
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detects faces of different sizes in the input image
    faces_coords = face_cascade.detectMultiScale(gray, 1.3, 5)

    ret_faces = []

    for (x, y, w, h) in faces_coords:
        # To draw a rectangle in a face
        roi_color = img[y:y + h, x:x + w]
        ret_faces.append((roi_color, x, y, w, h))

    return ret_faces
