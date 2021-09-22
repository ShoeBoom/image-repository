import unittest

from ImageSearch import ImageSearch
import cv2


class ImageSearchTests(unittest.TestCase):

    def test_search(self):
        image_search = ImageSearch(kmeans_clusters=1)
        image_search.batch_index_images(["images/1.jpg", "images/2.jpg"])

        image = cv2.imread("3.jpg")
        self.assertEqual(['1.jpg', '2.jpg'], image_search.search(image, n=2))

        image = cv2.imread("4.jpg")
        self.assertEqual(['2.jpg', '1.jpg'], image_search.search(image, n=2))

        image_search.index_image("4.jpg")
        self.assertEqual(['4.jpg', '2.jpg', '1.jpg'], image_search.search(image, n=3))

    def test_index_image(self):
        image_search = ImageSearch(kmeans_clusters=1)
        image_search.index_image("3.jpg")
        self.assertEqual(len(image_search._ImageSearch__histograms), 1)

    def test_delete_image(self):
        image_search = ImageSearch(kmeans_clusters=1)
        image_search.batch_index_images(["images/1.jpg", "images/2.jpg"])
        image_search.delete_image("1.jpg")
        image = cv2.imread("3.jpg")
        self.assertEqual(['2.jpg'], image_search.search(image))
        image_search.delete_image("2.jpg")
        image = cv2.imread("3.jpg")
        self.assertEqual([], image_search.search(image))

if __name__ == '__main__':
    unittest.main()
