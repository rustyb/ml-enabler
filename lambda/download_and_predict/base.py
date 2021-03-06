"""
Lambda for downloading images, packaging them for prediction, sending them
to a remote ML serving image, and saving them
@author:Development Seed
"""
import json
import affine
import geojson
import requests
import rasterio
import shapely

from shapely.geometry import box
from requests.auth import HTTPBasicAuth
from shapely import affinity, geometry
from enum import Enum
from functools import reduce
from io import BytesIO
from base64 import b64encode
from urllib.parse import urlparse
from typing import Dict, List, NamedTuple, Callable, Optional, Tuple, Any, Iterator
from rasterio.io import MemoryFile
from rasterio.windows import Window
from PIL import Image
import io

import mercantile
from mercantile import children
import numpy as np

from download_and_predict.custom_types import SQSEvent


class ModelType(Enum):
    OBJECT_DETECT = 1
    CLASSIFICATION = 2

class DownloadAndPredict(object):
    """
    base object DownloadAndPredict implementing all necessary methods to
    make machine learning predictions
    """

    def __init__(self, mlenabler_endpoint: str, prediction_endpoint: str):
        super(DownloadAndPredict, self).__init__()

        self.mlenabler_endpoint = mlenabler_endpoint
        self.prediction_endpoint = prediction_endpoint
        self.meta = {}

    def get_meta(self) -> ModelType:
        r = requests.get(self.prediction_endpoint + "/metadata")
        r.raise_for_status()

        self.meta = r.json()

        inputs = self.meta["metadata"]["signature_def"]["signature_def"]["serving_default"]["inputs"]

        # Object Detection Model
        if inputs.get("inputs") is not None:
            return ModelType.OBJECT_DETECT

        # Chip Classification Model
        else:
            return ModelType.CLASSIFICATION

    @staticmethod
    def get_chips(event: SQSEvent) -> List[str]:
        """
        Return the body of our incoming SQS messages as an array of dicts
        Expects events of the following format:

        { 'Records': [ { "body": '{ "url": "", "bounds": "" }' }] }

        """
        chips = []
        for record in event['Records']:
            chips.append(json.loads(record['body']))

        return chips

    @staticmethod
    def b64encode_image(image_binary:bytes) -> str:
        return b64encode(image_binary).decode('utf-8')

    def get_images(self, chips: List[dict]) -> Iterator[Tuple[dict, bytes]]:
        for chip in chips:
            print("IMAGE: " + chip.get('url'))
            r = requests.get(chip.get('url'))
            yield (chip, r.content)

    def get_prediction_payload(self, chips: List[dict], model_type: ModelType) -> Tuple[List[dict], Dict[str, Any]]:
        """
        chps: list image tilesk
        imagery: str an imagery API endpoint with three variables {z}/{x}/{y} to replace
        Return:
        - an array of b64 encoded images to send to our prediction endpoint
        These arrays are returned together because they are parallel operations: we
        need to match up the tile indicies with their corresponding images
        """

        tiles_and_images = self.get_images(chips)
        tile_indices, images = zip(*tiles_and_images)
        instances = []
        if model_type == ModelType.CLASSIFICATION:
            instances = [dict(image_bytes=dict(b64=self.b64encode_image(img))) for img in images]
        else:
            instances = [dict(inputs=dict(b64=self.b64encode_image(img))) for img in images]

        payload = {
            "instances": instances
        }

        return payload

    def cl_post_prediction(self, payload: Dict[str, Any], chips: List[dict], prediction_id: str, inferences: List[str]) -> Dict[str, Any]:
        payload = json.dumps(payload)
        r = requests.post(self.prediction_endpoint + ":predict", data=payload)
        r.raise_for_status()

        preds = r.json()["predictions"]
        pred_list = [];

        for i in range(len(chips)):
            pred_dict = {}

            for j in range(len(preds[i])):
                pred_dict[inferences[j]] = preds[i][j]

            body = {
                "geom": shapely.geometry.mapping(box(*chips[i].get('bounds'))),
                "predictions": pred_dict,
                "prediction_id": prediction_id
            }

            if chips[i].get('x') is not None and chips[i].get('y') is not None and chips[i].get('z') is not None:
                body['quadkey'] = mercantile.quadkey(chips[i].get('x'), chips[i].get('y'), chips[i].get('z'))

            pred_list.append(body)

        return {
            "predictionId": prediction_id,
            "predictions": pred_list
        }

    def od_post_prediction(self, payload: str, chips: List[dict], prediction_id: str) -> Dict[str, Any]:
        pred_list = [];

        for i in range(len(chips)):
            r = requests.post(self.prediction_endpoint + ":predict", data=json.dumps({
                "instances": [ payload["instances"][i] ]
            }))

            r.raise_for_status()

            # We only post a single chip for od detection
            preds = r.json()["predictions"][0]

            if preds["num_detections"] == 0.0:
                continue

            # Create lists of num_detections length
            scores = preds['detection_scores'][:int(preds["num_detections"])]
            bboxes = preds['detection_boxes'][:int(preds["num_detections"])]

            bboxes_256 = []
            for bbox in bboxes:
                bboxes_256.append([c * 256 for c in bbox])

            for j in range(len(bboxes_256)):
                bbox = geojson.Feature(
                    geometry=self.tf_bbox_geo(bboxes_256[j], chips[i].get('bounds')),
                    properties={}
                ).geometry

                score = preds["detection_scores"][j]

                body = {
                    "geom": bbox,
                    "predictions": {
                        "default": score
                    },
                    "prediction_id": prediction_id
                }

                if chips[i].get('x') is not None and chips[i].get('y') is not None and chips[i].get('z') is not None:
                    body['quadkey'] = mercantile.quadkey(chips[i].get('x'), chips[i].get('y'), chips[i].get('z'))

                pred_list.append(body)

        return {
            "predictionId": prediction_id,
            "predictions": pred_list
        }

    def save_prediction(self, prediction_id: str, payload, auth: str):
        url = self.mlenabler_endpoint + "/v1/model/prediction/" + prediction_id + "/tiles"
        r = requests.post(url, json=payload, auth=HTTPBasicAuth('machine', auth))

        print(r.text)

        r.raise_for_status()

        return True

    def tf_bbox_geo(self, bbox, chip_bounds):
        pred = [bbox[1], bbox[0], bbox[3], bbox[2]]
        # Affine Transform
        width = chip_bounds[2] - chip_bounds[0]
        height = chip_bounds[3] - chip_bounds[1]
        a = affine.Affine(width / 256, 0.0, chip_bounds[0], 0.0, (0 - height / 256), chip_bounds[3])
        a_lst = [a.a, a.b, a.d, a.e, a.xoff, a.yoff]
        geographic_bbox = affinity.affine_transform(geometry.box(*pred), a_lst)

        return geographic_bbox

class SuperTileDownloader(DownloadAndPredict):
    def __init__(self, mlenabler_endpoint: str, prediction_endpoint: str):
    # type annotatation error ignored, re: https://github.com/python/mypy/issues/5887
        super(DownloadAndPredict, self).__init__()
        self.mlenabler_endpoint = mlenabler_endpoint
        self.prediction_endpoint = prediction_endpoint

    def get_images(self, chips: List[dict]) -> Iterator[Tuple[dict, bytes]]:
        """return bounds of original tile filled with the 4 child chips 1 zoom level up in bytes"""
        for chip in chips:
            w_lst = []
            for i in range(2):
                for j in range(2):
                    window = Window(i * 256, j * 256, 256, 256)
                    w_lst.append(window)

            child_tiles = children(chip.get('x'), chip.get('y'), chip.get('z')) #get this from database (tile_zoom)
            child_tiles.sort()

            with MemoryFile() as memfile:
                with memfile.open(driver='jpeg', height=512, width=512, count=3, dtype=rasterio.uint8) as dataset:
                    for num, t in enumerate(child_tiles):
                        url = chip.get('url').replace(str(chip.get('x')), str(t.x), 1).replace(str(chip.get('y')), str(t.y), 1).replace(str(chip.get('z')), str(t.z), 1)

                        r = requests.get(url)
                        img = np.array(Image.open(io.BytesIO(r.content)), dtype=np.uint8)
                        try:
                            img = img.reshape((256, 256, 3)) # 4 channels returned from some endpoints, but not all
                        except ValueError:
                            img = img.reshape((256, 256, 4))
                        img = img[:, :, :3]
                        img = np.rollaxis(img, 2, 0)
                        dataset.write(img, window=w_lst[num])
                dataset_b = memfile.read() #but this fails
                yield(
                    chip,
                    dataset_b)

