import json
from datetime import datetime
import face_recognition
import os
from PIL import Image, ImageDraw
import hashlib
import exifread
import time

def convert_tags_to_json_serializable(tags):
    tags_json_serializable = {}
    try:
        for tag, value in tags.items():
            tags_json_serializable[tag] = str(value)
    except:
        pass
    return tags_json_serializable
def get_exif_data(file_path):
    with open(file_path, "rb") as f:
        try:
            tags = exifread.process_file(f)
        except:
            tags = None
    return tags

def get_date_taken(exif_data):
    date_tag = "EXIF DateTimeOriginal"
    try:
        if date_tag in exif_data:
            date_taken = exif_data[date_tag].values
            return date_taken
    except:
        pass
    return None

def get_geotagging(exif_data):
    gps_latitude = _get_if_exist(exif_data, "GPS GPSLatitude")
    gps_latitude_ref = _get_if_exist(exif_data, "GPS GPSLatitudeRef")
    gps_longitude = _get_if_exist(exif_data, "GPS GPSLongitude")
    gps_longitude_ref = _get_if_exist(exif_data, "GPS GPSLongitudeRef")

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = _convert_to_degrees(gps_latitude)
        lon = _convert_to_degrees(gps_longitude)
        if gps_latitude_ref.values != "N":
            lat = -lat
        if gps_longitude_ref.values != "E":
            lon = -lon
        return [lat, lon]
    return None

def _get_if_exist(data, key):
    try:
        if key in data:
            return data[key]
    except:
        pass
    return None

def _convert_to_degrees(value):
    try:
        d = float(value.values[0].num) / float(value.values[0].den)
    except:
        d = 0.
    try:
        m = float(value.values[1].num) / float(value.values[1].den)
    except:
        m = 0.
    try:
        s = float(value.values[2].num) / float(value.values[2].den)
    except:
        s = 0.

    return d + (m / 60.0) + (s / 3600.0)
def hash_file(filename, algorithm='sha256'):
    """Compute the hash of a file using the specified algorithm."""
    hasher = hashlib.new(algorithm)

    with open(filename, 'rb') as file:
        while True:
            chunk = file.read(8192)
            if not chunk:
                break
            hasher.update(chunk)

    return hasher.hexdigest()

def count_files_in_directory(path):
    total_files = 0
    for root, dirs, files in os.walk(path):
        total_files += len(files)
    return total_files

def construct_encodings_of_examples(path):
    ex_encodings = {}

    for root, dirs, files in os.walk(path):
        dir = root.split('/')[-1]
        for filename in files:
            img1_encodings = []
            try:
                img1_encodings = face_recognition.face_encodings(face_recognition.load_image_file(root +"/"+ filename))
            except:
                print(f"Encoding of the file {root}/{filename} was not calculated. Probably it is not an image")
            if not img1_encodings:
                print(f"example file  {root}/{filename} cannot be embedded")
                continue
            img1_encoding = img1_encodings[0]


            if dir in ex_encodings.keys():
                ex_encodings[dir].append(img1_encoding)
            else:
                ex_encodings[dir] = [img1_encoding]
    return ex_encodings




def main(name):
    index = {}

    dirname = input("enter name of directory with images:")
    start_time = time.time()
    files_number = 0
    files_size = 0
    path = "./persons"
    persons_number = len([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
    examples_number = count_files_in_directory(path) - 1
    print(persons_number)
    ex_encodings = construct_encodings_of_examples(path)
    # Use a breakpoint in the code line below to debug your script.
    print(dirname)
    try:
        with open("./persons/fc_index.json", 'r') as file:
            index = json.load(file)
            #print(index)
            #timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S.%f")
        #print (f"Old fc_index.json exists. It will be renamed to fc_index_{timestamp}")
        #os.rename("./persons/fc_index.json", f"./persons/fc_index_{timestamp}.json")


    except:
        print("fc_index.json not found. New file will be created.")
        index = {}



    for root, dirs, files in os.walk(dirname):
        for filename in files:
            if any(x == "tmp" for x in root.split('/')) or any(x == "turned" for x in root.split('/')):
                continue
            if filename.lower().split(".")[-1] != "jpg":
                continue
            hash_value = hash_file(root +"/"+ filename)
            if "all" in index.keys() and "files" in index["all"].keys() and hash_value in index["all"]["files"].keys():
                print(f"File with Hash : {hash_value} explored earlier.")
                continue
            print(f"Hash : {hash_value}")
            print(f"Exploring file : {root}/{filename}")
            files_size += os.path.getsize(root +"/"+ filename)
            files_number += 1
            print(f"Files explored:{files_number}, files size {files_size/1000000} MB")
            if files_number % 10 == 0:
                end_time = time.time()
                time_passed = - start_time + end_time

                print(f"Time passed: {time_passed} === {end_time} - {start_time}")
                print(f" Average time: {time_passed / files_number} sec per image,  {1000000 * time_passed / files_size} sec per MB")
                print(f" Average time: {time_passed / (files_number * examples_number)} sec per image * example,"
                      f"  {time_passed / (files_number * persons_number)} sec per image * example")
                with open("./persons/statistics_", 'a') as stat:
                    stat.write(
                        str(files_number)+
                        ";"+
                        str(files_size/1000000)+
                        ";"+
                        str(time_passed / files_number)+
                        ";"+
                        str(time_passed / files_size)+
                        ";"+
                        str(time_passed / (files_number * examples_number))+
                        ";"+
                        str(time_passed / (files_number * persons_number))+
                        "\n"
                        )

            # insert file data into "all" entry
            #=========================================================================
            name = "all"
            if name not in index.keys():
                index[name] = {}
            if "files" not in index[name].keys():
                index[name]["files"] = {}
            index[name]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if hash_value not in index[name]["files"].keys():
                index[name]["files"][hash_value] = {}
                index[name]["files"][hash_value]["paths"] = [root + "/" + filename]
                exif_data = get_exif_data(root + "/" + filename)
                index[name]["files"][hash_value]["exif"] = convert_tags_to_json_serializable(exif_data)
                if "JPEGThumbnail" in index[name]["files"][hash_value]["exif"].keys():
                    del index[name]["files"][hash_value]["exif"]["JPEGThumbnail"]
                index[name]["files"][hash_value]["date_taken"] = get_date_taken(exif_data)
                gt = get_geotagging(exif_data)
                index[name]["files"][hash_value]["geotag"] = gt if gt else [0., 0.]
            else:
                index[name]["files"][hash_value]["paths"].append(root + "/" + filename)
            #=========================================================================

            extracted_faces = extract_face(dirname,root, filename)
#            mark_face(root, filename)
            if not extracted_faces: continue
            for e_face in extracted_faces:
                for name  in ex_encodings.keys():

                    c_faces = compare_faces(ex_encodings[name], e_face)
                    if c_faces and sum(c_faces) / len(c_faces) > 0.5:
                        if name not in index.keys():
                            index[name] = {}
                        if "files" not in index[name].keys():
                            index[name]["files"] = {}
                        index[name]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        if hash_value not in index[name]["files"].keys():
                            index[name]["files"][hash_value] = {}
                            index[name]["files"][hash_value]["paths"] = [root +"/"+ filename]
                            exif_data = get_exif_data(root + "/" + filename)
                            index[name]["files"][hash_value]["exif"] = convert_tags_to_json_serializable(exif_data)
                            if "JPEGThumbnail" in index[name]["files"][hash_value]["exif"].keys():
                                del index[name]["files"][hash_value]["exif"]["JPEGThumbnail"]
                            index[name]["files"][hash_value]["date_taken"] = get_date_taken(exif_data)
                            gt = get_geotagging(exif_data)
                            index[name]["files"][hash_value]["geotag"] = gt if gt else [0., 0.]
                        else:
                            index[name]["files"][hash_value]["paths"].append(root + "/" + filename)
            with open("./persons/fc_index.json", 'w') as file:
                json.dump(index, file)



    end_time = time.time()
    print(f"Duration = {-(start_time - end_time)} sec")

def extract_face(dirname,root,filename):
    answer = []
    try:
        face_img = face_recognition.load_image_file(root + "/" + filename)
        for turn in range(3):

            face_locations = face_recognition.face_locations((face_img))


            if len(face_locations) == 0:
                if not os.path.exists(dirname + "/turned"):
                    os.makedirs(dirname + "/turned")
                #Image.fromarray(face_img).rotate(90*(turn+1)).save(dirname + "/turned/" + f"turn_{(turn+1)*90}_" + filename)
                #face_img = face_recognition.load_image_file(dirname + "/turned/" + f"turn_{(turn+1)*90}_" + filename)
                face_img = Image.fromarray(face_img).rotate(90)
                print(f"No faces in image {root}/{filename} turned by {(turn) * 90}")
                continue

            print(f"found {len(face_locations)} faces in image {root}/{filename} turned by {(turn) * 90}")
            count = 1
            for (top, right, bottom, left) in face_locations:
                f_im = face_img[top:bottom, left:right]
                pil_img = Image.fromarray(f_im)
                if not os.path.exists(dirname + "/tmp"):
                    os.makedirs(dirname + "/tmp")
                pil_img.save(dirname + "/tmp" +f"/{count}_" + filename)
                answer.append(dirname + "/tmp" +f"/{count}_" + filename)
                count += 1
            break
        return answer
    except:
        print(Exception())
def compare_faces(example_encodings, img2_path):

    img2 = face_recognition.load_image_file(img2_path)
    img2_encodings = face_recognition.face_encodings(img2)
    if img2_encodings:
        img2_encoding = face_recognition.face_encodings(img2)[0]
        result = face_recognition.compare_faces(example_encodings,img2_encoding)
    else:
        result = [False]
    return result
def mark_face(dirname,root, filename):
    try:
        face_img = face_recognition.load_image_file(root + "/" + filename)
        for turn in range(3):

            face_locations = face_recognition.face_locations((face_img))

            print(f"found {len(face_locations)} faces in image {filename}")
            if len(face_locations) == 0:
                if not os.path.exists(dirname + "/turned"):
                    os.makedirs(dirname + "/turned")
                Image.fromarray(face_img).rotate(90*(turn+1)).save(dirname + "/turned/" + f"turn_{(turn+1)*90}_" + filename)
                face_img = face_recognition.load_image_file(dirname + "/turned/" + f"turn_{(turn+1)*90}_" + filename)
                continue
            pil_img = Image.fromarray(face_img)
            draw = ImageDraw.Draw(pil_img)
            for (top, right, bottom, left) in face_locations:
                draw.rectangle(((left, top),(right, bottom)), outline=(255, 255, 0), width=5 )
            del draw
            if not os.path.exists(dirname + "/marked"):
                os.makedirs(dirname + "/marked")
            pil_img.save(dirname + "/marked/marked_" + filename)
            break
    except:
        print(Exception())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main('PyCharm')



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
# where from
