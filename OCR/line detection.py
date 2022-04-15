#import des packages requis
import cv2
import os

# Donne l'ordonnée du barycentre d'une zone 
def y_middle_contour(contour):
    return cv2.boundingRect(contour)[1] + cv2.boundingRect(contour)[3]//2

# Donne l'ordonnée du barycentre d'un ensemble de zones
def y_middle_setcontour(list_contours):
    list_y = [y_middle_contour(c) for c in list_contours]
    return sum(list_y)//len(list_y)

# Cherche les zones qui intersectionnent en ordonnées la position "position"
def find_on_same_line(position, list_contours):
    output = []
    for cnt in list_contours:
        if cv2.boundingRect(cnt)[1] > position:
            break
        else:
            output.append(cnt)

    
    return output

# Fait la détection à proprement dite des lignes
def extract_sequence(list_contours):
    working_list = [contour for contour in list_contours]
    working_list.reverse()
    output = []
    line = []
    while working_list != []:
        first_elmt = working_list[0]
        line = [first_elmt]
        working_list.remove(first_elmt)

        # On prend la première zone détectée, on retient toutes les zones contenant l'ordonnée de son barycentre
        other_elmts = find_on_same_line(y_middle_setcontour(line), working_list)
        line += other_elmts
        for elmt in other_elmts:
            working_list.remove(elmt)

        # On calcule la moyenne de l'ordonnée des barycentre
        # Avec ce nouveau barycentre, on cherche si de nouvelles zones sont concernées
        while(other_elmts != []):
            other_elmts = find_on_same_line(y_middle_setcontour(line), working_list)
            line += other_elmts
            for elmt in other_elmts:
                working_list.remove(elmt)
                
        output.append(line)
    return output

def clean_lines(list_lines):
    # On ne considère pas la 1re ligne qui est le n° du 1er échantillon
    list_temp = [list_lines[0]] # liste de sortie regroupant les lignes proches 
    i = 1
    
    while i < len(list_lines)-1:
        if len(list_lines[i]) == 1:
            # ligne étudiée
            curr = y_middle_setcontour(list_lines[i])
            # ligne précédente
            prec = y_middle_setcontour(list_lines[i-1])
            # ligne suivante
            succ = y_middle_setcontour(list_lines[i+1])

            # si la ligne courante est plus proche de la précédente
            if curr-prec < succ-curr:
                list_temp[-1] += list_lines[i]
                i+=1
            else:
                list_temp.append(list_lines[i] + list_lines[i+1])
                i+=2
        else:
            list_temp.append(list_lines[i])
            i+=1

    # traitement de la dernière ligne  
    if len(list_lines[-1]) == 1:
        list_temp[-1] += list_lines[-1]
    else:
        list_temp.append(list_lines[-1])
        
    return list_temp  



def detect_text_zones(file_path, output_dir):
    print('Parsing image "' + file_path + '"')
    
    # Chargement de l'image
    img = cv2.imread(file_path)

    # Rotation de l'image de 90° sens anti-horaire
    imgRotate = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Conversion de l'image en nuance de gris
    gray = cv2.cvtColor(imgRotate, cv2.COLOR_BGR2GRAY)

    # Image floutée, améliore la qualité du seuil (threshold ligne suivante)
    blur = cv2.GaussianBlur(gray,(9,9),0)
    
    # Calcul du seuil (noir ou blanc en fonction du seuil retenu automatiquement par OTSU threshold)
    ret, thresh1 = cv2.threshold(blur, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

    # Spécifie la taille minimale des rectangles de détection
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 1)) #analyse de char (1, 5)

    # Applique une dilatation de l'image threshold
    dilation = cv2.dilate(thresh1, rect_kernel, iterations=1)

    # Détection des contours
    contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Restrictions aux contours de la taille voulue
    # cv2.boundingRect(c)[2] == largeur du contour (w)
    # cv2.boundingRect(c)[3] == hauteur du contour (h)
    # !!! TAILLE ARBITRAIRE DEPENDANT DE LA RESOLUTION DE L'IMAGE ET DE LA TAILLE DU TEXTE !!!
    contoursRetained = [c for c in contours
                        if (cv2.boundingRect(c)[2] > 24 and 26 < cv2.boundingRect(c)[3] < 60)]
    
    '''for i in range(len(contoursRetained)):
        # coordonées abscisse point haut/gauche, ordonnée point haut/gauche, largeur, hauteur
        x, y, w, h = cv2.boundingRect(contoursRetained[i])
        
        # Dessine un rectangle sur l'image copiée
        rect = cv2.rectangle(im_contoursDetected, (x, y), (x+w, y+h), (0, 255, 0), 2)
    '''
    list_lines = extract_sequence(contoursRetained)
    list_lines = clean_lines(list_lines)
    
    file_name = file_path.split('\\')[-1].split('.')
    if not os.path.exists(f"{output_dir}\\{file_name[0]}"):
        os.makedirs(f"{output_dir}\\{file_name[0]}")
    
    for i in range(len(list_lines)):
        #TODO: créer une méthode qui recherche min/max en hauteur parmi liste de contours
        
        x_left = 0
        x_right = imgRotate.shape[1]
        y_top = cv2.boundingRect(list_lines[i][0])[1]
        y_bottom = cv2.boundingRect(list_lines[i][-1])[1] + cv2.boundingRect(list_lines[i][-1])[3]

        # Enregistrement de l'image avec les zones de texte détectées
        # file_name[0] == nom fichier
        # file_name[1] == extension fichier
        file_output = f"{output_dir}\\{file_name[0]}\\{file_name[0]}_{i:02}.{file_name[1]}"
        cv2.imwrite(file_output, imgRotate[max(0,y_top-3):min(y_bottom+3, imgRotate.shape[0]), x_left:x_right])
      
    # Chaque ligne a ses éléments triés de gauche à droite
    #list_lines = [sorted(line, key=lambda x: cv2.boundingRect(x)[0]) for line in list_lines]

    #copies de l'image pour visualisation
    im_contoursDetected = imgRotate.copy()
    for line in list_lines:
        y = y_middle_setcontour(line)
        lineTrace = cv2.line(im_contoursDetected, (0,y), (3400,y), (0, 0, 255), 2)

        x, y, w, h = cv2.boundingRect(line[0])
        rect = cv2.rectangle(im_contoursDetected, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        x, y, w, h = cv2.boundingRect(line[-1])
        rect = cv2.rectangle(im_contoursDetected, (x, y), (x+w, y+h), (255, 0, 0), 2)
    
    # Enregistrement de l'image avec les zones de texte détectées
    # file_name[0] == nom fichier
    # file_name[1] == extension fichier
    file_name = file_path.split('\\')[-1].split('.') 
    new_path = output_dir + '\\' + file_name[0] + "_contours." + file_name[1]
    cv2.imwrite(new_path, im_contoursDetected)
    
    #print(new_path + " successfully wroten.\n")



    
# Explore un répertoire et tous ses sous-répertoires
# Retient uniquement les fichiers d'une même extension
def explore_directory(dir_name, extension):
    path_files = []
    for root, dirs, files in os.walk(dir_name):
        path_files += [root + "\\" + f for f in files if f.endswith(extension)]
    return path_files


# Procédure d'appel de nos méthodes et d'exploration
def procedure(input_directory, file_extension):
    dir_name = input_directory.split("\\")[-1]
    output_dir = ".\\output_line_"+dir_name
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    files = explore_directory(input_directory, file_extension)
    for f in files:
        detect_text_zones(f, output_dir)


procedure(".\\test", ".jpg")
