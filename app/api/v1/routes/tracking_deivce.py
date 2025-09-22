from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.models.database.base import get_db
from app.api.deps import get_current_admin_user
from app.services import tracking_device as tracking_device_service


router = APIRouter(prefix="/tracking-device", tags=["tracking-device"])


# # This would be to create a tracking device which can be linked to a trip later
# @router.post("/create-device", response_model=TrackingDeviceResponse)
# async def create_tracking_device(
#     device_data: TrackingDeviceCreate,
#     admin_user=Depends(get_current_admin_user),
#     db: Session = Depends(get_db),
# ):
#     """Create a new tracking device with a unique API key."""
#     try:
#         tracking_device = await tracking_device_service.create_tracking_device(
#             device_data, db
#         )
#         return tracking_device

#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to create tracking device: {str(e)}",
#         )


# @router.get("/list", response_model=TrackingDeviceListResponse)
# async def get_all_tracking_devices(
#     admin_user=Depends(get_current_admin_user),
#     db: Session = Depends(get_db),
# ):
#     """Get all tracking devices."""
#     try:
#         devices = await tracking_device_service.get_all_tracking_devices(db)
#         return TrackingDeviceListResponse(devices=devices, total=len(devices))

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to get tracking devices: {str(e)}",
#         )


# @router.get("/{device_id}/api-key", response_model=TrackingDeviceApiKeyResponse)
# async def get_device_api_key(
#     device_id: str,
#     admin_user=Depends(get_current_admin_user),
#     db: Session = Depends(get_db),
# ):
#     """Get the API key for a tracking device by device_id."""
#     try:
#         tracking_device = (
#             await tracking_device_service.get_tracking_device_by_device_id(
#                 device_id, db
#             )
#         )

#         if not tracking_device:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Tracking device not found",
#             )

#         return TrackingDeviceApiKeyResponse(
#             device_id=tracking_device.device_id, api_key=tracking_device.api_key
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to get device API key: {str(e)}",
#         )


# @router.patch("/{device_id}/status", response_model=TrackingDeviceResponse)
# async def update_device_status(
#     device_id: str,
#     status_update: TrackingDeviceStatusUpdate,
#     admin_user=Depends(get_current_admin_user),
#     db: Session = Depends(get_db),
# ):
#     """Update the status of a tracking device."""
#     try:
#         # First get the device by device_id
#         tracking_device = (
#             await tracking_device_service.get_tracking_device_by_device_id(
#                 device_id, db
#             )
#         )

#         if not tracking_device:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Tracking device not found",
#             )

#         # Update the device status
#         updated_device = await tracking_device_service.update_device_status(
#             tracking_device.id, status_update.status, db
#         )

#         return updated_device

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update device status: {str(e)}",
#         )


# @router.get("/{device_id}", response_model=TrackingDeviceResponse)
# async def get_tracking_device(
#     device_id: str,
#     admin_user=Depends(get_current_admin_user),
#     db: Session = Depends(get_db),
# ):
#     """Get tracking device details by device_id."""
#     try:
#         tracking_device = (
#             await tracking_device_service.get_tracking_device_by_device_id(
#                 device_id, db
#             )
#         )

#         if not tracking_device:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Tracking device not found",
#             )

#         return tracking_device

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to get tracking device: {str(e)}",
#         )


# @router.patch("/{device_id}", response_model=TrackingDeviceResponse)
# async def update_tracking_device(
#     device_id: str,
#     update_data: TrackingDeviceUpdateRequest,
#     admin_user=Depends(get_current_admin_user),
#     db: Session = Depends(get_db),
# ):
#     """Update tracking device details including trek_id, status, and other fields."""
#     try:
#         # First get the device by device_id
#         tracking_device = (
#             await tracking_device_service.get_tracking_device_by_device_id(
#                 device_id, db
#             )
#         )

#         if not tracking_device:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Tracking device not found",
#             )

#         # Update the device with the provided data
#         updated_device = await tracking_device_service.update_tracking_device(
#             tracking_device.id, update_data, db
#         )

#         if not updated_device:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Tracking device not found",
#             )

#         return updated_device

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update tracking device: {str(e)}",
#         )
