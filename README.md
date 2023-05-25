Pet_project: Photo archive indexing

Common problem is to find all appearences of family member on photos in family archive.
Here is a solution.

1. Scans images in specific directory (/dir) and its subdirectories and finds faces on them.
2. Saves found faces in separate directory (/dir/tmp)
3. Clusterizes faces using different methods (DBSCAN, OPTICS, HDBSCAN, KMeans, AgglomerativeClustering)
4. Saves clusterized faces in separate directories (/dir/tmp/method/cluster_number)
5. Results a saved in clusters.csv file including information about clusterization including images paths, faces and initial images hashes.
6. Result can be used afterward for:

  6.1. finding images with specific person;
  6.2. indexing and tagging images by predefined persons;
    6.3. finding similar images;

7. To run the script you need to run the following command in terminal:
    sudo apt-get install libboost-all-dev libgtk-3-dev build-essential cmake
    pip install face-recognition
8. Run file clusters.py


You can check results for some group photos of G20 leaders in dir ./stock/tmp
Looks like AffinityPropagation method gives the best result given that number of cluster is not known apriori.
