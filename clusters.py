import json
import shutil
from datetime import datetime
import face_recognition
import os
from PIL import Image, ImageDraw
import hashlib
import exifread
import time
import numpy as np
import csv
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN, Birch, OPTICS, AgglomerativeClustering, SpectralClustering, MeanShift, AffinityPropagation



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



def collect_vectors():
    """
    Looks through images, seek faces on them.
    For every face forms 128-dim vector
    writes result into csv
    :return:
    """


    dirname = input("enter name of directory with images:")
    start_time = time.time()
    files_number = 0
    files_size = 0
    faces_number = 0
    #ex_encodings = construct_encodings_of_examples(path)

    csv_file = "./csv_index.csv"

    # Prepare your data

    try:
        file = open(csv_file, mode='r+', newline='', encoding='utf-8')
        csv_reader = csv.DictReader(file, delimiter=";")
        list_of_dicts = [row for row in csv_reader]
        file.close()
    except:
        print("csv file is empty. It will be created")
        list_of_dicts = []

        header = ['Face_hash', 'Face_path', 'Face_encoding', 'Image_hash', 'Image_path', 'date_taken', 'geotag']
        data = []








    print(list_of_dicts)


    for root, dirs, files in os.walk(dirname):
        for filename in files:
            if any(x == "tmp" for x in root.split('/')) or any(x == "turned" for x in root.split('/')):
                continue
            if filename.lower().split(".")[-1] != "jpg":
                continue
            hash_value = hash_file(root +"/"+ filename)
            exif_data = get_exif_data(root + "/" + filename)
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
                        "\n"
                        )


            extracted_faces = extract_face(dirname,root, filename)
#            mark_face(root, filename)
            if not extracted_faces:
                print(f"no faces in {filename}")
                continue
            for e_face in extracted_faces:

                eface_dict = {}
                eface_dict["Face_hash"] = hash_file(root +"/"+ filename)
                eface_dict["Face_path"] = e_face[0]
                eface_dict["Face_encoding"] = e_face[1]
                eface_dict["Image_hash"] = hash_value
                eface_dict["Image_path"] = root +"/"+ filename
                eface_dict["date_taken"] = get_date_taken(exif_data)
                eface_dict["geotag"] = get_geotagging(exif_data)
                list_of_dicts.append(eface_dict)
                faces_number += 1
                print(f"Faces found in total: {faces_number}")
                print(f"Length of list_of_dicts: {len(list_of_dicts)}")



    """
    write list_of_dicts into csv

    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file, delimiter=";")

        # Write the header row
        csv_writer.writerow(header)

        # Write the data rows
        csv_writer.writerows(list_of_dicts)
    """
    end_time = time.time()
    print(f"Duration = {-(start_time - end_time)} sec")
    print(f"faces recorded = {faces_number}")
    return list_of_dicts

def extract_face(dirname,root,filename):
    answer = []
    try:
        face_img = face_recognition.load_image_file(root + "/" + filename)
        for turn in range(4):

            face_locations = face_recognition.face_locations((face_img))


            if len(face_locations) == 0:

                #Image.fromarray(face_img).rotate(90).save(dirname + "/turned/" + f"turn_{(turn+1)*90}_" + filename)
                #i = np.asarray(Image.fromarray(face_img).rotate(90))
                #face_img = face_recognition.load_image_file(dirname + "/turned/" + f"turn_{(turn+1)*90}_" + filename)
                face_img = np.asarray(Image.fromarray(face_img).rotate(90))
                print(f"No faces in image {root}/{filename} turned by {(turn) * 90}")
                continue

            print(f"found {len(face_locations)} faces in image {root}/{filename} turned by {(turn) * 90}")
            count = 0
            for (top, right, bottom, left) in face_locations:
                f_im = face_img[top:bottom, left:right]
                pil_img = Image.fromarray(f_im)
                if not os.path.exists(dirname + "/tmp"):
                    os.makedirs(dirname + "/tmp")
                pil_img.save(dirname + "/tmp" +f"/{count}_" + filename)
                face_encoding = face_recognition.face_encodings(np.asarray(pil_img))[0]
                    #face_recognition.load_image_file(root + "/" + filename))
                answer.append([dirname + "/tmp" +f"/{count}_" + filename, face_encoding])

                count += 1
            break
        return answer
    except:
        print(f"exception in extract_face() with {filename}")
        print(f"added only {count} faces of {len(face_locations)} founded")
        if answer: return answer
def compare_faces(example_encodings, img2_path):

    img2 = face_recognition.load_image_file(img2_path)
    img2_encodings = face_recognition.face_encodings(img2)
    if img2_encodings:
        img2_encoding = face_recognition.face_encodings(img2)[0]
        result = face_recognition.compare_faces(example_encodings,img2_encoding)
    else:
        result = [False]
    return result

def clusterize(list_of_dicts):
    """
    Using pandas clusterize list_of_dicts['Face_encoding'] into clusters.
    Use method of KMeans. Number of clusters is 10.
    Use method DBSCAN. Number of clusters is 10.
    :param list_of_dicts:
    :return:
    """
    df = pd.DataFrame(list_of_dicts)
    #df = df.drop(['Image_path','Image_hash','date_taken','geotag'], axis=1)

    print(df)
    X = np.array(df['Face_encoding'].tolist())
    kmeans = KMeans(n_clusters=10, random_state=0).fit(X)
    dbscan = DBSCAN(eps=0.3, min_samples=5).fit(X)
    aff = AffinityPropagation(random_state=0).fit(X)
    mean_shift = MeanShift().fit(X)
    spec_clust = SpectralClustering(n_clusters=10).fit(X)
    agglo = AgglomerativeClustering(n_clusters=10).fit(X)
    optics = OPTICS(min_samples=5).fit(X)
    birch = Birch(n_clusters=10).fit(X)
    df['cluster_birch'] = birch.labels_
    df['cluster_optics'] = optics.labels_
    df['cluster_agglo'] = agglo.labels_
    df['cluster_spec_clust'] = spec_clust.labels_
    df['cluster_mean_shift'] = mean_shift.labels_
    df['cluster_aff'] = aff.labels_
    df['cluster_kmeans'] = kmeans.labels_
    df['cluster_DBSCAN'] = dbscan.labels_
    df = df.drop(['Face_encoding'], axis=1)
    print(df)
    df.to_csv("clusters.csv", sep=";")
    return df


def create_subdirectories_for_clusters(clusters):
    for index, cl in clusters.iterrows():
        face_file = cl['Face_path']
        face_dir = os.path.dirname(face_file)
        face_filename = os.path.basename(face_file)
        for cluster_method in [
            'cluster_birch',
            'cluster_optics',
            'cluster_agglo',
            'cluster_spec_clust',
            'cluster_mean_shift',
            'cluster_aff',
            'cluster_kmeans',
            'cluster_DBSCAN']:
            face_cluster_method_path = face_dir + "/" +cluster_method + "/" + str(cl[cluster_method])
            if not os.path.exists(face_cluster_method_path):
                os.makedirs(face_cluster_method_path)
            shutil.copy(face_file, face_cluster_method_path + "/" + face_filename)



if __name__ == '__main__':
    list_of_dicts = collect_vectors()
    clusters = clusterize(list_of_dicts)
    create_subdirectories_for_clusters(clusters)
    print(f"result was saved in clusters.csv")






