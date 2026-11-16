from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.dtos.slot_dto import ResetSlotsRequestDTO, SlotListResponseDTO
from src.repositories.slot_repository import SlotRepository
from src.services.slot_service import SlotService

router = APIRouter(tags=["Slots"])


@router.post("/reset", status_code=200)
def reset_slots(
    payload: ResetSlotsRequestDTO,
    db: Session = Depends(get_db),
):
    """Reset appointment slots: deletes existing bookings and replaces all slots."""
    slot_repo = SlotRepository(db)
    slot_service = SlotService(slot_repo)
    slots = slot_service.reset_slots(payload)
    return {"message": "Slots reset successfully", "count": len(slots)}


@router.get("/slots", response_model=SlotListResponseDTO, status_code=200)
def list_slots(
    provider: str | None = Query(None, description="Optional filter by healthcare provider"),
    db: Session = Depends(get_db),
):
    """Retrieve appointment slots in chronological order, with computed availability."""
    slot_repo = SlotRepository(db)
    slot_service = SlotService(slot_repo)
    slots = slot_service.list_slots(provider=provider)
    return SlotListResponseDTO(slots=slots)
