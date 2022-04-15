from pylibdmtx.pylibdmtx import decode
import cv2
import os
import time

import multiprocessing as mp
pool = mp.Pool(mp.cpu_count())

def findDataMat(image):
    '''SEUIL_THRESH = 222

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    ret, thresh1 = cv2.threshold(gray, SEUIL_THRESH, 255, cv2.THRESH_BINARY)
    
    contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    contoursRetained = [c for c in contours
                            if(130 < cv2.boundingRect(c)[2] < 160 and 130 < cv2.boundingRect(c)[3] < 160)]
    '''

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)) #analyse de char (1, 5)

    dilatation = cv2.dilate(thresh1, rect_kernel, iterations=1)

    contours, hierarchy = cv2.findContours(dilatation, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    contoursRetained = [c for c in contours
                            if(65 < cv2.boundingRect(c)[2] < 110 and 65 < cv2.boundingRect(c)[3] < 110)]


    dec = []
    for c in contoursRetained:
        # coordonées abscisse point haut/gauche, ordonnée point haut/gauche, largeur, hauteur
        x, y, w, h = cv2.boundingRect(c)

        #crop_img = image[y:y+h, x:x+w]
        crop_img = image[max(0,y-5):min(image.shape[0],y+h+5), max(0,x-5):min(image.shape[1],x+w+5)]
        datamatrix = decode(crop_img)
        if datamatrix != []:
            dec.append(str(datamatrix[0][0], "utf-8"))

    return dec


def box_name(file_path):
    return os.path.basename(file_path).split('.')[0].split('_')[0]

def detectLam(file_path, destination, increments):
    # Nom du fichier sans le path
    file_name = os.path.basename(file_path)

    # Extension du fichier
    file_extension = file_name.split('.')[-1]

    # Nom de la boîte sur laquelle on travaille
    box = box_name(file_path)

    print(f"Working on {file_name}")

    # Chargement de l'image
    img = cv2.imread(file_path)

    # Rotation de l'image de 90° sens horaire
    rotation = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    # Conversion de l'image en nuance de gris
    gray = cv2.cvtColor(rotation, cv2.COLOR_BGR2GRAY)

    # Calcul du seuil (noir ou blanc en fonction du seuil retenu automatiquement par OTSU threshold)
    ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)

    # Détection des contours
    contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Restrictions aux contours de la taille voulue
    # cv2.boundingRect(c)[2] == largeur du contour (w)
    # cv2.boundingRect(c)[3] == hauteur du contour (h)
    # !!! TAILLE ARBITRAIRE DEPENDANT DE LA RESOLUTION DE L'IMAGE !!!
    contoursRetained = [c for c in contours
                        if (1100 < cv2.boundingRect(c)[2] < 1300) and 300 < cv2.boundingRect(c)[3] < 500]

    # Création du répertoire s'il n'existe pas
    if not os.path.exists(f"{destination}/{box}"):
        os.makedirs(f"{destination}/{box}")

    incr_NF = increments[0]
    incr_multi = increments[1]
    for c in contoursRetained:
        # coordonées abscisse point haut/gauche, ordonnée point haut/gauche, largeur, hauteur
        x, y, w, h = cv2.boundingRect(c)

        # image découpée selon les coordonnées ci-dessus
        crop_img = rotation[y:y+h, x:x+w]

        dataMat = findDataMat(crop_img)
        if(dataMat == []):
            if not os.path.exists(f"datamatrix_NOT_FOUND"):
                os.makedirs(f"datamatrix_NOT_FOUND")
            cv2.imwrite(f"datamatrix_NOT_FOUND/{file_name.split('.')[0]}_{incr_NF:03}.{file_extension}", crop_img)
            incr_NF += 1
                
        elif(len(dataMat) > 1):
            if not os.path.exists(f"datamatrix_MULTI"):
                os.makedirs(f"datamatrix_MULTI")
            cv2.imwrite(f"datamatrix_MULTI/{box}_{file_name.split('.')[0]}.{file_extension}", crop_img)
            incr_multi += 1
            
        else:
            cv2.imwrite(f"{destination}/{box}/{box}_{dataMat[0]}.{file_extension}", crop_img)


    return (incr_NF, incr_multi)


def explore_directory(dir_name, extension):
    path_files = []
    for root, dirs, files in os.walk(dir_name):
        path_files += [root + "/" + f for f in files if f.endswith(extension)]
    return path_files

def count_slides():
    acc = 0
    for root, dirs, files in os.walk("./output"):
        for f in files:
            if f.endswith(".jpg"):
                acc += 1
    return acc



def procedure(input_directory, file_extension):
    files = explore_directory(input_directory, file_extension)

    curr_box = box_name(files[0])
    incr = (1,1)
    for f in files:
        if(curr_box != box_name(f)):
             incr = (1,1)
        destination = "./output"
        incr = detectLam(f, destination, incr)

    return len(files)

start_time = time.time() 
nb_files = procedure("./test", ".jpg")
end_time = time.time()

print(f"\n{count_slides()} slides created.")
print(f"{nb_files} files proceed in {round(end_time-start_time, 2)} s.")

