# extrairGabarito.py / não remover esse comentário
# esse arquivo é feita a extração do gabarito usando threshold para reconhecimento dos pontos brancos de respostas
import cv2
import numpy as np

def extrairMaiorCtn(img):
    img = cv2.resize(img, (400, 500), interpolation=cv2.INTER_AREA)
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgTh = cv2.adaptiveThreshold(imgGray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 12)
    kernel = np.ones((2,2), np.uint8)
    imgDil = cv2.dilate(imgTh, kernel)
    contours, _ = cv2.findContours(imgDil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    maiorCtn = max(contours, key=cv2.contourArea)
    epsilon = 0.02 * cv2.arcLength(maiorCtn, True)
    approx = cv2.approxPolyDP(maiorCtn, epsilon, True)
    
    if len(approx) == 4:
        pts = approx.reshape(4, 2)
        pts = sorted(pts, key=lambda x: x[1])
        top_pts = sorted(pts[:2], key=lambda x: x[0])
        bottom_pts = sorted(pts[2:], key=lambda x: x[0])
        
        pts1 = np.float32([top_pts[0], top_pts[1], bottom_pts[0], bottom_pts[1]])
        pts2 = np.float32([[0, 0], [400, 0], [0, 500], [400, 500]])
        
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        recorte = cv2.warpPerspective(img, matrix, (400, 500))
        x, y, w, h = cv2.boundingRect(maiorCtn)
    else:
        x, y, w, h = cv2.boundingRect(maiorCtn)
        recorte = img[y:y+h, x:x+w]
        recorte = cv2.resize(recorte, (400, 500), interpolation=cv2.INTER_AREA)
    
    return recorte, (x, y, w, h)