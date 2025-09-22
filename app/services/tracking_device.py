from app.models.database.tracking_device import TrackingDevice
from sqlmodel import select, Session
from app.utils.security import generate_api_key
import datetime
from typing import Optional, Union


# TODO: Fix timestamps to datetime


# async def create_tracking_device(
#     device_create_data: TrackingDeviceCreate, db: Session
# ) -> TrackingDevice:
#     """Create a new tracking device with a unique API key."""
#     try:
#         existing_device = db.exec(
#             select(TrackingDevice).where(
#                 TrackingDevice.device_id == device_create_data.device_id
#             )
#         ).first()

#         if existing_device:
#             raise ValueError("Device with this ID already exists")

#         api_key = generate_api_key()

#         tracking_device = TrackingDevice(
#             device_id=device_create_data.device_id,
#             api_key=api_key,
#             treck_id=device_create_data.treck_id,
#             status=TrackingDeviceStatusEnum.INACTIVE,
#             created_at=int(datetime.datetime.utcnow().timestamp()),
#             updated_at=int(datetime.datetime.utcnow().timestamp()),
#         )

#         db.add(tracking_device)
#         db.commit()
#         db.refresh(tracking_device)

#         return tracking_device

#     except Exception as e:
#         db.rollback()
#         raise e


# async def get_tracking_device_by_id(
#     device_id: int, db: Session
# ) -> Optional[TrackingDevice]:
#     """Get a tracking device by its ID."""
#     statement = select(TrackingDevice).where(TrackingDevice.id == device_id)
#     device = db.exec(statement).first()
#     return device


# async def get_tracking_device_by_device_id(
#     device_id: str, db: Session
# ) -> Optional[TrackingDevice]:
#     """Get a tracking device by its device_id."""
#     statement = select(TrackingDevice).where(TrackingDevice.device_id == device_id)
#     device = db.exec(statement).first()
#     return device


# async def update_tracking_device(
#     device_id: int,
#     device_update_data: Union[TrackingDeviceUpdate, TrackingDeviceUpdateRequest],
#     db: Session,
# ) -> Optional[TrackingDevice]:
#     """Update a tracking device."""
#     try:
#         # Get the existing device
#         statement = select(TrackingDevice).where(TrackingDevice.id == device_id)
#         device = db.exec(statement).first()

#         if not device:
#             return None

#         # Update only the fields that are provided (not None)
#         update_data = device_update_data.model_dump(exclude_unset=True)
#         for field, value in update_data.items():
#             setattr(device, field, value)

#         # Update the updated_at timestamp
#         device.updated_at = int(datetime.datetime.utcnow().timestamp())

#         db.add(device)
#         db.commit()
#         db.refresh(device)

#         return device

#     except Exception as e:
#         db.rollback()
#         raise e


# async def delete_tracking_device(device_id: int, db: Session) -> bool:
#     """Delete a tracking device."""
#     try:
#         statement = select(TrackingDevice).where(TrackingDevice.id == device_id)
#         device = db.exec(statement).first()

#         if not device:
#             return False

#         db.delete(device)
#         db.commit()
#         return True

#     except Exception as e:
#         db.rollback()
#         raise e


# async def get_all_tracking_devices(db: Session) -> list[TrackingDevice]:
#     """Get all tracking devices."""
#     statement = select(TrackingDevice)
#     devices = db.exec(statement).all()
#     return list(devices)


# async def activate_tracking_device(
#     device_id: int, db: Session
# ) -> Optional[TrackingDevice]:
#     """Activate a tracking device."""
#     try:
#         statement = select(TrackingDevice).where(TrackingDevice.id == device_id)
#         device = db.exec(statement).first()

#         if not device:
#             return None

#         device.status = TrackingDeviceStatusEnum.ACTIVE
#         device.activated_at = int(datetime.datetime.utcnow().timestamp())
#         device.updated_at = int(datetime.datetime.utcnow().timestamp())

#         db.add(device)
#         db.commit()
#         db.refresh(device)

#         return device

#     except Exception as e:
#         db.rollback()
#         raise e


# async def deactivate_tracking_device(
#     device_id: int, db: Session
# ) -> Optional[TrackingDevice]:
#     """Deactivate a tracking device."""
#     try:
#         statement = select(TrackingDevice).where(TrackingDevice.id == device_id)
#         device = db.exec(statement).first()

#         if not device:
#             return None

#         device.status = TrackingDeviceStatusEnum.INACTIVE
#         device.deactivated_at = int(datetime.datetime.utcnow().timestamp())
#         device.updated_at = int(datetime.datetime.utcnow().timestamp())

#         db.add(device)
#         db.commit()
#         db.refresh(device)

#         return device

#     except Exception as e:
#         db.rollback()
#         raise e


# async def update_device_status(
#     device_id: int, new_status: TrackingDeviceStatusEnum, db: Session
# ) -> Optional[TrackingDevice]:
#     """Update the status of a tracking device."""
#     try:
#         statement = select(TrackingDevice).where(TrackingDevice.id == device_id)
#         device = db.exec(statement).first()

#         if not device:
#             return None

#         # Update status and related timestamps
#         device.status = new_status
#         device.updated_at = int(datetime.datetime.utcnow().timestamp())

#         # Set activation/deactivation timestamps based on status
#         if new_status == TrackingDeviceStatusEnum.ACTIVE:
#             device.activated_at = int(datetime.datetime.utcnow().timestamp())
#         elif new_status == TrackingDeviceStatusEnum.INACTIVE:
#             device.deactivated_at = int(datetime.datetime.utcnow().timestamp())

#         db.add(device)
#         db.commit()
#         db.refresh(device)

#         return device

#     except Exception as e:
#         db.rollback()
#         raise e
