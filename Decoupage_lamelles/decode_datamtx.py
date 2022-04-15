from pylibdmtx.pylibdmtx import decode
import cv2
import time

SEUIL_THRESH = 225

start_time = time.time()

img = cv2.imread('B00501_001.jpg')

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

cv2.imwrite("thresh.jpg", thresh1)

rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)) #analyse de char (1, 5)

dilatation = cv2.dilate(thresh1, rect_kernel, iterations=1)

cv2.imwrite("dilatation.jpg", dilatation)

contours, hierarchy = cv2.findContours(dilatation, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

contoursRetained = [c for c in contours
                        if(65 < cv2.boundingRect(c)[2] < 110 and 65 < cv2.boundingRect(c)[3] < 110)]


dec = []
img_copy = img.copy()
for c in contoursRetained:
    # coordonées abscisse point haut/gauche, ordonnée point haut/gauche, largeur, hauteur
    x, y, w, h = cv2.boundingRect(c)

    rect = cv2.rectangle(img_copy, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    crop_img = img[y-5:y+h+5, x-5:x+w+5]
    datamatrix = decode(crop_img)
    if(datamatrix!=[]):
        dec.append(str(datamatrix[0][0], "utf-8"))

cv2.imwrite("detected.jpg", img_copy)

end_time = time.time()

print(dec)
print(f"{end_time - start_time} s.")
