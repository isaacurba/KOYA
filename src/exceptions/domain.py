from __future__ import annotations


class ClinicBookingException(Exception):
    """Base domain exception for clinic booking application."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SlotNotFound(ClinicBookingException):
    """Raised when an appointment slot does not exist."""

    def __init__(self, message: str = "Appointment slot does not exist.") -> None:
        super().__init__(message, status_code=404)


class BookingNotFound(ClinicBookingException):
    """Raised when a booking record does not exist."""

    def __init__(self, message: str = "Booking does not exist.") -> None:
        super().__init__(message, status_code=404)


class SlotAlreadyBooked(ClinicBookingException):
    """Raised when an appointment slot already has a confirmed booking."""

    def __init__(self, message: str = "Appointment slot is already booked.") -> None:
        super().__init__(message, status_code=409)


class BookingAlreadyCancelled(ClinicBookingException):
    """Raised when attempting to cancel a booking that has already been cancelled."""

    def __init__(self, message: str = "Booking has already been cancelled.") -> None:
        super().__init__(message, status_code=409)


class SlotInPast(ClinicBookingException):
    """Raised when attempting to book a slot that has already started."""

    def __init__(self, message: str = "Cannot book an appointment slot that has already started.") -> None:
        super().__init__(message, status_code=400)


# Aliases for Error naming convention
SlotNotFoundError = SlotNotFound
BookingNotFoundError = BookingNotFound
SlotAlreadyBookedError = SlotAlreadyBooked
BookingAlreadyCancelledError = BookingAlreadyCancelled
SlotInPastError = SlotInPast
