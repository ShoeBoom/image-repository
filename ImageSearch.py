import ntpath
import os
from typing import List

import cv2
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
import numpy as np


# TODO: make implementation that works with external database

class ImageSearch:

    def __init__(self, kmeans_clusters=10):
        """

        :param kmeans_clusters: size  of kmeans clusters
        """
        self.__flat_descriptors_list = []
        self.__histograms = []
        self.__images_names = []
        self.__kmeans = None

        self.kmeans_clusters = kmeans_clusters

        # initialize feature extractor
        self.extractor = cv2.SIFT_create()

    def batch_index_images(self, image_paths: List[str]):
        """
        indexes all files in a specified folder
        :param image_paths: list containing image paths
        """
        if len(image_paths) == 0:
            return

        temp_des = []
        for path in image_paths:
            # fetch image
            image = cv2.imread(path)

            descriptor = self.__extract_descriptors(image)

            self.__flat_descriptors_list.extend(descriptor)
            self.__images_names.append(ntpath.basename(path))

            temp_des.append(descriptor)

        self.__reset_kmeans()

        # create histogram
        for des in temp_des:
            histogram = self.__create_histogram(des)
            self.__histograms.append(histogram)

    def index_image(self, img_path):
        """
        index a single image give a path
        :param img_path: path of image (absolute or from the working directory)
        """
        self.__images_names.append(ntpath.basename(img_path))

        # fetch image and extract descriptor
        image = cv2.imread(img_path)
        descriptor = self.__extract_descriptors(image)

        self.__flat_descriptors_list.extend(descriptor)
        self.__reset_kmeans()

        histogram = self.__create_histogram(descriptor)
        self.__histograms.append(histogram)

    def search(self, image, n=10):
        """
        search indexed images

        :param image: image to search against
        :param n: number of images to search
        :return: name of matching files
        """
        if len(self.__histograms) == 0 and len(self.__images_names) == 0:
            return []

        descriptor = self.__extract_descriptors(image)
        histogram = self.__create_histogram(descriptor)
        neighbor = NearestNeighbors(n_neighbors=min(n, len(self.__histograms)))
        neighbor.fit(self.__histograms)

        indices = neighbor.kneighbors([histogram])[1][0]
        return [self.__images_names[i] for i in indices]

    def __create_histogram(self, descriptor):
        histogram = np.zeros(len(self.__kmeans.cluster_centers_))

        result = self.__kmeans.predict(descriptor.astype(float))
        for i in result:
            histogram[i] += 1.0
        return histogram

    def __reset_kmeans(self):
        # re init kmeans
        self.__kmeans = KMeans(self.kmeans_clusters)
        self.__kmeans.fit(self.__flat_descriptors_list)

    def __extract_descriptors(self, image):
        # convert image to gray
        cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # return descriptions of image
        return self.extractor.detectAndCompute(image, None)[1]

    def delete_image(self, image_name):
        i = self.__images_names.index(image_name)
        self.__images_names.pop(i)
        self.__histograms.pop(i)
