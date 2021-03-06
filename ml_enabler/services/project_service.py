from flask import current_app
from ml_enabler.models.ml_model import Project, ProjectAccess
from ml_enabler.models.dtos.dtos import ProjectDTO
from ml_enabler.models.utils import NotFound


class ProjectServiceError(Exception):
    """ Custom Exception to notify callers an error occurred when validating an ML Model """

    def __init__(self, message):
        if current_app:
            current_app.logger.error(message)


class ProjectService:
    @staticmethod
    def subscribe_ml_model(dto: ProjectDTO) -> int:
        """
        Subscribes an ML Model by saving it in the database
        :params dto

        :raises DataError
        :returns ID of the ml model
        """

        new_ml_model = Project()
        new_ml_model.create(dto)

        if dto.users:
            ProjectAccess.list_update(new_ml_model.id, [], dto.users)

        return new_ml_model.id

    @staticmethod
    def delete_ml_model(model_id: int):
        """
        Deletes ML model and associated predictions
        :params model_id
        """
        ml_model = Project.get(model_id)
        if ml_model:
            ml_model.delete()
        else:
            raise NotFound("Model does not exist")

    @staticmethod
    def get_ml_model_by_id(model_id: int):
        """
        Get an ML Model for a given ID
        :params model_id

        :raises NotFound
        :returns ML Model
        """

        ml_model = Project.get(model_id)
        users = ProjectAccess.list(model_id)

        if ml_model:
            model = ml_model.as_dto(users=users)
            return model
        else:
            raise NotFound("Model does not exist")

    @staticmethod
    def get_all(uid: int, model_filter: str, model_archived: bool):
        """
        Get all ML Models

        :raises NotFound
        :returns array of ML Models
        """

        ml_models = Project.get_all(uid, model_filter, model_archived)
        if ml_models:
            model_collection = []
            for model in ml_models:
                model_collection.append(model.as_dto().to_primitive())
            return model_collection
        else:
            raise NotFound("No models exist")

    @staticmethod
    def update_ml_model(dto: ProjectDTO) -> int:
        """
        Update an existing ML Model
        :params model_id

        :raises NotFound
        :returns model_id
        """

        ml_model = Project.get(dto.model_id)

        if ml_model:
            ml_model.update(dto)

            if dto.users:
                users = ProjectAccess.list(dto.model_id)
                ProjectAccess.list_update(dto.model_id, users, dto.users)

            return dto.model_id
        else:
            raise NotFound("Model does not exist")
