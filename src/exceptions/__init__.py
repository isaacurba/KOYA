from src.exceptions.domain import (
    BookingAlreadyCancelled,
    BookingAlreadyCancelledError,
    BookingNotFound,
    BookingNotFoundError,
    ClinicBookingException,
    SlotAlreadyBooked,
    SlotAlreadyBookedError,
    SlotInPast,
    SlotInPastError,
    SlotNotFound,
    SlotNotFoundError,
)
from src.exceptions.handlers import register_exception_handlers

__all__ = [
    "ClinicBookingException",
    "SlotNotFound",
    "SlotNotFoundError",
    "BookingNotFound",
    "BookingNotFoundError",
    "SlotAlreadyBooked",
    "SlotAlreadyBookedError",
    "BookingAlreadyCancelled",
    "BookingAlreadyCancelledError",
    "SlotInPast",
    "SlotInPastError",
    "register_exception_handlers",
]
