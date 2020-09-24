from ml_enabler.models.aoi import AOI
from ml_enabler import db
from ml_enabler.models.utils import NotFound

class AOIService():
    @staticmethod
    def create(payload: dict) -> int:
        return AOI.create(payload)

    @staticmethod
    def list(model_id: int, pred_id: int):
        rawaois = AOI.list(model_id, pred_id)

        aois = []
        if (rawaois):
            for aoi in rawaois:
                aois.append(aoi.as_dto().to_primitive())

            return {
                'model_id': model_id,
                'pred_id': pred_id,
                'aois': aois
            }
        else:
            return {
                'model_id': model_id,
                'pred_id': pred_id,
                'aois': []
            }

