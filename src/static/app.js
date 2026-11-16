/**
 * CarePoint Clinic — Frontend Client Application
 * Communicates strictly with the backend-for-frontend routes (/frontend-api/*).
 * Never uses or requires any client-side API key.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const slotsContainer = document.getElementById("slots-container");
  const providerFilter = document.getElementById("provider-filter");
  const btnRefreshSlots = document.getElementById("btn-refresh-slots");
  const bookingForm = document.getElementById("booking-form");
  const slotSelect = document.getElementById("slot-select");
  const patientNameInput = document.getElementById("patient-name");
  const patientEmailInput = document.getElementById("patient-email");
  const btnSubmitBooking = document.getElementById("btn-submit-booking");

  const confirmationCard = document.getElementById("confirmation-card");
  const confId = document.getElementById("conf-id");
  const confName = document.getElementById("conf-name");
  const confEmail = document.getElementById("conf-email");
  const confSlot = document.getElementById("conf-slot");
  const confStatus = document.getElementById("conf-status");
  const confCreated = document.getElementById("conf-created");
  const btnCopyId = document.getElementById("btn-copy-id");
  const btnDismissConf = document.getElementById("btn-dismiss-confirmation");
  const btnTrackBooking = document.getElementById("btn-track-booking");

  const lookupInput = document.getElementById("lookup-id-input");
  const btnLookupBooking = document.getElementById("btn-lookup-booking");
  const bookingResult = document.getElementById("booking-result");
  const resultId = document.getElementById("result-id");
  const resultSlot = document.getElementById("result-slot");
  const resultName = document.getElementById("result-name");
  const resultEmail = document.getElementById("result-email");
  const resultCreated = document.getElementById("result-created");
  const resultStatusBadge = document.getElementById("result-status-badge");
  const btnCancelBooking = document.getElementById("btn-cancel-booking");

  const globalAlert = document.getElementById("global-alert");
  const alertIcon = document.getElementById("alert-icon");
  const alertMessage = document.getElementById("alert-message");
  const alertDismiss = document.getElementById("alert-dismiss");

  // Application State
  let currentSlots = [];
  let activeLookupBooking = null;
  let alertTimeout = null;

  // --- Alert System ---

  function showAlert(type, message) {
    if (alertTimeout) clearTimeout(alertTimeout);

    globalAlert.className = `alert ${type}`;
    alertMessage.textContent = message;

    if (type === "success") {
      alertIcon.textContent = "✓";
    } else if (type === "error") {
      alertIcon.textContent = "⚠";
    } else {
      alertIcon.textContent = "ℹ";
    }

    globalAlert.classList.remove("hidden");
    globalAlert.scrollIntoView({ behavior: "smooth", block: "start" });

    alertTimeout = setTimeout(() => {
      globalAlert.classList.add("hidden");
    }, 8000);
  }

  alertDismiss.addEventListener("click", () => {
    globalAlert.classList.add("hidden");
  });

  // --- Date & Time Formatters ---

  function formatDateTime(isoString) {
    try {
      const date = new Date(isoString);
      return date.toLocaleString(undefined, {
        weekday: "short",
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZoneName: "short",
      });
    } catch {
      return isoString;
    }
  }

  function formatTimeOnly(isoString) {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  }

  function formatDateOnly(isoString) {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        weekday: "short",
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return isoString;
    }
  }

  // --- Slot Listing & Rendering ---

  async function loadSlots(selectedProvider = null) {
    slotsContainer.innerHTML = `
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading clinic appointments...</p>
      </div>
    `;

    try {
      let url = "/frontend-api/slots";
      if (selectedProvider) {
        url += `?provider=${encodeURIComponent(selectedProvider)}`;
      }

      const response = await fetch(url, {
        headers: { "Accept": "application/json" },
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `Failed to fetch slots (Status ${response.status})`);
      }

      const data = await response.json();
      currentSlots = data.slots || [];

      // Update provider filter options if viewing all
      if (!selectedProvider) {
        updateProviderFilter(currentSlots);
      }

      renderSlots(currentSlots);
      updateBookingSelect(currentSlots);
    } catch (err) {
      slotsContainer.innerHTML = `
        <div class="empty-state">
          <p>Failed to load appointment slots.</p>
          <small>${err.message}</small>
        </div>
      `;
      showAlert("error", err.message);
    }
  }

  function updateProviderFilter(slots) {
    const previousSelection = providerFilter.value;
    const providers = Array.from(new Set(slots.map(s => s.provider))).sort();

    providerFilter.innerHTML = '<option value="">All Providers</option>';
    providers.forEach(p => {
      const option = document.createElement("option");
      option.value = p;
      option.textContent = p;
      if (p === previousSelection) {
        option.selected = true;
      }
      providerFilter.appendChild(option);
    });
  }

  function updateBookingSelect(slots) {
    const previousSelection = slotSelect.value;
    slotSelect.innerHTML = '<option value="">-- Choose an appointment slot --</option>';

    const availableSlots = slots.filter(s => s.available);
    if (availableSlots.length === 0) {
      slotSelect.innerHTML = '<option value="">No available slots remaining</option>';
      return;
    }

    availableSlots.forEach(slot => {
      const option = document.createElement("option");
      option.value = slot.id;
      const dateStr = formatDateOnly(slot.start);
      const startStr = formatTimeOnly(slot.start);
      const endStr = formatTimeOnly(slot.end);
      option.textContent = `[${slot.id}] ${slot.provider} — ${dateStr} (${startStr} - ${endStr})`;

      if (slot.id === previousSelection) {
        option.selected = true;
      }
      slotSelect.appendChild(option);
    });
  }

  function renderSlots(slots) {
    if (slots.length === 0) {
      slotsContainer.innerHTML = `
        <div class="empty-state">
          <p>No appointment slots found for the selected provider.</p>
        </div>
      `;
      return;
    }

    slotsContainer.innerHTML = "";
    slots.forEach(slot => {
      const card = document.createElement("div");
      card.className = `slot-card ${slot.available ? "available" : "booked"}`;
      card.id = `slot-card-${slot.id}`;

      const dateStr = formatDateOnly(slot.start);
      const startTime = formatTimeOnly(slot.start);
      const endTime = formatTimeOnly(slot.end);

      card.innerHTML = `
        <div>
          <div class="slot-provider">
            <span>👨‍⚕️</span>
            <span>${slot.provider}</span>
          </div>
          <div class="slot-time-block">
            <div class="slot-date">📅 ${dateStr}</div>
            <div>⏰ ${startTime} – ${endTime}</div>
          </div>
        </div>
        <div class="slot-footer">
          <span class="badge ${slot.available ? "badge-available" : "badge-booked"}">
            ${slot.available ? "Available" : "Booked"}
          </span>
          ${
            slot.available
              ? `<button class="btn btn-sm btn-primary btn-select-slot" data-slot-id="${slot.id}">Select</button>`
              : `<button class="btn btn-sm btn-secondary" disabled>Unavailable</button>`
          }
        </div>
      `;

      slotsContainer.appendChild(card);
    });

    // Attach click handlers to select buttons
    document.querySelectorAll(".btn-select-slot").forEach(button => {
      button.addEventListener("click", (e) => {
        const slotId = e.currentTarget.getAttribute("data-slot-id");
        selectSlotForBooking(slotId);
      });
    });
  }

  function selectSlotForBooking(slotId) {
    slotSelect.value = slotId;

    // Highlight card
    document.querySelectorAll(".slot-card").forEach(c => c.classList.remove("selected"));
    const targetCard = document.getElementById(`slot-card-${slotId}`);
    if (targetCard) targetCard.classList.add("selected");

    // Scroll to booking form
    document.getElementById("booking-section").scrollIntoView({ behavior: "smooth" });
    patientNameInput.focus();
  }

  // Filter change
  providerFilter.addEventListener("change", () => {
    loadSlots(providerFilter.value || null);
  });

  // Refresh button
  btnRefreshSlots.addEventListener("click", () => {
    loadSlots(providerFilter.value || null);
    showAlert("info", "Appointment slots refreshed.");
  });

  // --- Booking Form Submission ---

  bookingForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const slotId = slotSelect.value.trim();
    const name = patientNameInput.value.trim();
    const email = patientEmailInput.value.trim();

    // Client-side validation
    if (!slotId) {
      showAlert("error", "Please select an appointment slot to proceed.");
      slotSelect.focus();
      return;
    }
    if (!name) {
      showAlert("error", "Please provide the patient full name.");
      patientNameInput.focus();
      return;
    }
    if (!email || !email.includes("@")) {
      showAlert("error", "Please provide a valid email address.");
      patientEmailInput.focus();
      return;
    }

    // Submit state
    btnSubmitBooking.disabled = true;
    btnSubmitBooking.textContent = "Processing Booking...";

    try {
      const response = await fetch("/frontend-api/bookings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        body: JSON.stringify({
          slot_id: slotId,
          name: name,
          email: email,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMessage = data.error || "Unable to reserve appointment.";
        if (response.status === 409) {
          showAlert("error", `Double Booking Conflict: ${errorMessage}`);
        } else if (response.status === 400) {
          showAlert("error", `Validation Error: ${errorMessage}`);
        } else if (response.status === 404) {
          showAlert("error", `Not Found: ${errorMessage}`);
        } else {
          showAlert("error", errorMessage);
        }
        return;
      }

      // Success
      displayConfirmation(data);
      showAlert("success", `Appointment booked successfully! Booking Reference: ${data.id}`);

      // Reset form
      bookingForm.reset();

      // Refresh slots
      loadSlots(providerFilter.value || null);
    } catch (err) {
      showAlert("error", `Network Error: ${err.message}`);
    } finally {
      btnSubmitBooking.disabled = false;
      btnSubmitBooking.textContent = "Confirm & Book Appointment";
    }
  });

  function displayConfirmation(booking) {
    confId.textContent = booking.id;
    confName.textContent = booking.name;
    confEmail.textContent = booking.email;
    confSlot.textContent = booking.slot_id;
    confStatus.textContent = booking.status;
    confCreated.textContent = formatDateTime(booking.created_at);

    confirmationCard.classList.remove("hidden");
    confirmationCard.scrollIntoView({ behavior: "smooth" });
  }

  btnDismissConf.addEventListener("click", () => {
    confirmationCard.classList.add("hidden");
  });

  btnCopyId.addEventListener("click", () => {
    const id = confId.textContent;
    if (id && id !== "-") {
      navigator.clipboard.writeText(id).then(() => {
        btnCopyId.textContent = "Copied!";
        setTimeout(() => { btnCopyId.textContent = "Copy"; }, 2000);
      });
    }
  });

  btnTrackBooking.addEventListener("click", () => {
    const id = confId.textContent;
    lookupInput.value = id;
    document.getElementById("manage-section").scrollIntoView({ behavior: "smooth" });
    handleLookup();
  });

  // --- Booking Management & Cancellation ---

  async function handleLookup() {
    const bookingId = lookupInput.value.trim();
    if (!bookingId) {
      showAlert("error", "Please enter a valid Booking ID.");
      lookupInput.focus();
      return;
    }

    btnLookupBooking.disabled = true;
    btnLookupBooking.textContent = "Searching...";

    try {
      const response = await fetch(`/frontend-api/bookings/${encodeURIComponent(bookingId)}`, {
        headers: { "Accept": "application/json" },
      });

      const data = await response.json();

      if (!response.ok) {
        bookingResult.classList.add("hidden");
        const msg = data.error || "Booking not found.";
        showAlert("error", msg);
        return;
      }

      activeLookupBooking = data;
      renderBookingResult(data);
      showAlert("success", "Booking details retrieved successfully.");
    } catch (err) {
      showAlert("error", `Lookup error: ${err.message}`);
    } finally {
      btnLookupBooking.disabled = false;
      btnLookupBooking.textContent = "Lookup Booking";
    }
  }

  function renderBookingResult(booking) {
    resultId.textContent = booking.id;
    resultSlot.textContent = booking.slot_id;
    resultName.textContent = booking.name;
    resultEmail.textContent = booking.email;
    resultCreated.textContent = formatDateTime(booking.created_at);

    resultStatusBadge.textContent = booking.status.toUpperCase();
    if (booking.status === "confirmed") {
      resultStatusBadge.className = "badge badge-confirmed";
      btnCancelBooking.disabled = false;
      btnCancelBooking.classList.remove("hidden");
      btnCancelBooking.textContent = "Cancel This Booking";
    } else {
      resultStatusBadge.className = "badge badge-cancelled";
      btnCancelBooking.disabled = true;
      btnCancelBooking.textContent = "Booking Already Cancelled";
    }

    bookingResult.classList.remove("hidden");
    bookingResult.scrollIntoView({ behavior: "smooth" });
  }

  btnLookupBooking.addEventListener("click", handleLookup);
  lookupInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleLookup();
  });

  // Cancel Booking
  btnCancelBooking.addEventListener("click", async () => {
    if (!activeLookupBooking) return;

    if (!confirm(`Are you sure you want to cancel booking ${activeLookupBooking.id}? This will free the appointment slot.`)) {
      return;
    }

    btnCancelBooking.disabled = true;
    btnCancelBooking.textContent = "Cancelling...";

    try {
      const response = await fetch(`/frontend-api/bookings/${encodeURIComponent(activeLookupBooking.id)}`, {
        method: "DELETE",
        headers: { "Accept": "application/json" },
      });

      const data = await response.json();

      if (!response.ok) {
        const msg = data.error || "Failed to cancel booking.";
        showAlert("error", msg);
        return;
      }

      // Success
      activeLookupBooking = data;
      renderBookingResult(data);
      showAlert("success", `Booking ${data.id} has been cancelled. The appointment slot is now available again.`);

      // Refresh slots
      loadSlots(providerFilter.value || null);
    } catch (err) {
      showAlert("error", `Cancellation error: ${err.message}`);
    }
  });

  // Initial Load
  loadSlots();
});
