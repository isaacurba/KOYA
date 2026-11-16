from __future__ import annotations

from typing import Sequence
from src.dtos.slot_dto import (
    ResetSlotsRequestDTO,
    SlotCreateDTO,
    SlotResponseDTO,
)
from src.models.booking import BookingStatus
from src.models.slot import Slot
from src.repositories.slot_repository import SlotRepository


class SlotService:
    """Service implementing business rules for clinic appointment slots."""

    def __init__(self, slot_repo: SlotRepository) -> None:
        self.slot_repo = slot_repo

    def list_slots(self, provider: str | None = None) -> list[SlotResponseDTO]:
        """List appointment slots ordered chronologically by earliest start time.

        Calculates dynamic availability:
        - Unavailable if the slot currently has a confirmed booking.
        - Available if there are no bookings or all historical bookings are cancelled.
        """
        slots = self.slot_repo.list_all(provider=provider)
        results: list[SlotResponseDTO] = []
        for slot in slots:
            is_available = not any(
                b.status == BookingStatus.CONFIRMED.value for b in slot.bookings
            )
            results.append(
                SlotResponseDTO(
                    id=slot.id,
                    provider=slot.provider,
                    start=slot.start,
                    end=slot.end,
                    available=is_available,
                )
            )
        return results

    def reset_slots(
        self, slots_data: ResetSlotsRequestDTO | list[SlotCreateDTO] | list[dict]
    ) -> list[SlotResponseDTO]:
        """Transactionally replace all existing appointment slots and bookings with new slots."""
        if isinstance(slots_data, ResetSlotsRequestDTO):
            items = slots_data.slots
        elif isinstance(slots_data, list):
            items = slots_data
        else:
            raise ValueError("Unsupported slots data format for reset.")

        slot_models: list[Slot] = []
        for item in items:
            if isinstance(item, dict):
                dto = SlotCreateDTO(**item)
            elif isinstance(item, SlotCreateDTO):
                dto = item
            else:
                dto = SlotCreateDTO.model_validate(item)

            slot_models.append(
                Slot(
                    id=dto.id,
                    provider=dto.provider,
                    start=dto.start,
                    end=dto.end,
                )
            )

        saved_slots = self.slot_repo.reset_slots(slot_models)
        return [
            SlotResponseDTO(
                id=s.id,
                provider=s.provider,
                start=s.start,
                end=s.end,
                available=True,
            )
            for s in saved_slots
        ]
