from sqlalchemy.orm import Session
from .. import models, schemas

def create_face_measurement(
    db: Session,
    face_measurement: schemas.FaceMeasurementCreate
) -> models.FaceMeasurement:
    db_face_measurement = models.FaceMeasurement(
        user_id=face_measurement.user_id,
        face_width=face_measurement.face_width,
        eye_distance=face_measurement.eye_distance,
        cheek_area=face_measurement.cheek_area,
        nose_height=face_measurement.nose_height,
        temple_position=face_measurement.temple_position
    )
    db.add(db_face_measurement)
    db.commit()
    db.refresh(db_face_measurement)
    return db_face_measurement

def get_face_measurements(
    db: Session,
    user_id: int
) -> list[models.FaceMeasurement]:
    return db.query(models.FaceMeasurement).filter(
        models.FaceMeasurement.user_id == user_id
    ).all()

def get_latest_face_measurement(
    db: Session,
    user_id: int
) -> models.FaceMeasurement:
    return db.query(models.FaceMeasurement).filter(
        models.FaceMeasurement.user_id == user_id
    ).order_by(models.FaceMeasurement.created_at.desc()).first() 