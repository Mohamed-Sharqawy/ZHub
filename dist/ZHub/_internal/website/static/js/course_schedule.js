'use strict';

document.addEventListener('DOMContentLoaded', function () {

    var scheduleRows      = document.getElementById('schedule-rows');
    var addScheduleRowBtn = document.getElementById('add-schedule-row');
    var rowIndex = document.querySelectorAll('.schedule-row').length;

    // ─────────────────────────────────────────────────────────────────────────
    // TIME CONVERSION HELPERS
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Convert 12-hour components to a 24-hour "HH:MM" string.
     *
     * Parameters:
     *   hourStr  — string or number, 1–12
     *   minStr   — string or number, 0–59
     *   ampm     — "AM" or "PM"
     *
     * Returns "HH:MM" (e.g. "14:30") or "" if inputs are invalid.
     */
    function convertToHHMM(hourStr, minStr, ampm) {
        var hour = parseInt(hourStr, 10);
        var min  = parseInt(minStr,  10);
        if (isNaN(hour) || hour < 1 || hour > 12) return '';
        if (isNaN(min)  || min  < 0 || min  > 59) return '';
        if (ampm === 'PM' && hour !== 12) { hour += 12; }
        if (ampm === 'AM' && hour === 12) { hour  =  0; }
        return ('0' + hour).slice(-2) + ':' + ('0' + min).slice(-2);
    }

    /**
     * Parse a 24-hour "HH:MM" string into 12-hour display components.
     *
     * Returns { hour12: Number, min: Number, ampm: "AM"|"PM" }
     * or null if the string is absent or malformed.
     */
    function parseHHMM(timeStr) {
        if (!timeStr || typeof timeStr !== 'string') return null;
        var parts = timeStr.trim().split(':');
        if (parts.length !== 2) return null;
        var h24 = parseInt(parts[0], 10);
        var m   = parseInt(parts[1], 10);
        if (isNaN(h24) || h24 < 0 || h24 > 23) return null;
        if (isNaN(m)   || m   < 0 || m  > 59)  return null;
        var ampm = (h24 >= 12) ? 'PM' : 'AM';
        var h12  = h24 % 12;
        if (h12 === 0) h12 = 12;
        return { hour12: h12, min: m, ampm: ampm };
    }

    // ─────────────────────────────────────────────────────────────────────────
    // SYNC VISIBLE INPUTS → HIDDEN FIELD
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Read the three visible controls (.schedule-hour-{type},
     * .schedule-min-{type}, .schedule-ampm-{type}) inside the given row,
     * convert to HH:MM 24-hour format, and write the result into the
     * hidden field (.schedule-{type}). Then triggers recomputeHours().
     *
     * Parameters:
     *   row  — a DOM element with class "schedule-row"
     *   type — "start" or "end"
     */
    function syncHiddenField(row, type) {
        var hourInput   = row.querySelector('.schedule-hour-' + type);
        var minSelect   = row.querySelector('.schedule-min-'  + type);
        var ampmSelect  = row.querySelector('.schedule-ampm-' + type);
        var hiddenInput = row.querySelector('.schedule-'      + type);
        if (!hourInput || !minSelect || !ampmSelect || !hiddenInput) return;
        var hhMM = convertToHHMM(
            hourInput.value,
            minSelect.value,
            ampmSelect.value
        );
        hiddenInput.value = hhMM;
        recomputeHours();
    }

    // ─────────────────────────────────────────────────────────────────────────
    // SYNC HIDDEN FIELD → VISIBLE INPUTS
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Read the HH:MM value from the hidden field (.schedule-{type}) inside
     * the given row and populate the three visible controls accordingly.
     * Used on page load (Edit Course) and after form re-render on error.
     *
     * Parameters:
     *   row  — a DOM element with class "schedule-row"
     *   type — "start" or "end"
     */
    function populateVisibleInputs(row, type) {
        var hiddenInput = row.querySelector('.schedule-' + type);
        if (!hiddenInput || !hiddenInput.value) return;
        var parsed = parseHHMM(hiddenInput.value);
        if (!parsed) return;

        var hourInput  = row.querySelector('.schedule-hour-' + type);
        var minSelect  = row.querySelector('.schedule-min-'  + type);
        var ampmSelect = row.querySelector('.schedule-ampm-' + type);

        if (hourInput)  hourInput.value  = parsed.hour12;
        if (ampmSelect) ampmSelect.value = parsed.ampm;

        // Select the closest available minute option
        if (minSelect) {
            var opts    = minSelect.options;
            var bestIdx = 0;
            var bestDiff = 999;
            for (var i = 0; i < opts.length; i++) {
                var diff = Math.abs(parseInt(opts[i].value, 10) - parsed.min);
                if (diff < bestDiff) { bestDiff = diff; bestIdx = i; }
            }
            minSelect.selectedIndex = bestIdx;
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // PAGE LOAD: populate visible inputs from any existing hidden values
    // (Edit Course page has saved HH:MM values; Create Course page after
    //  a failed submit may also have values to restore)
    // ─────────────────────────────────────────────────────────────────────────

    document.querySelectorAll('.schedule-row').forEach(function (row) {
        populateVisibleInputs(row, 'start');
        populateVisibleInputs(row, 'end');
    });

    // ─────────────────────────────────────────────────────────────────────────
    // "ADD DAY" BUTTON
    // ─────────────────────────────────────────────────────────────────────────

    addScheduleRowBtn.addEventListener('click', function () {
        var lastRow = scheduleRows.querySelector('.schedule-row:last-of-type');
        if (!lastRow) return;

        var newRow = lastRow.cloneNode(true);

        // Clear all visible inputs in the cloned row
        newRow.querySelectorAll(
            '.schedule-hour-start, .schedule-hour-end'
        ).forEach(function (inp) { inp.value = ''; });

        newRow.querySelectorAll(
            '.schedule-min-start, .schedule-min-end'
        ).forEach(function (sel) { sel.selectedIndex = 0; });

        newRow.querySelectorAll(
            '.schedule-ampm-start, .schedule-ampm-end'
        ).forEach(function (sel) { sel.selectedIndex = 0; });

        // Clear hidden fields and assign new WTForms name attributes
        var newNamePrefix = 'schedules-' + rowIndex + '-';

        var weekdaySelect = newRow.querySelector('.schedule-weekday');
        var startHidden   = newRow.querySelector('.schedule-start');
        var endHidden     = newRow.querySelector('.schedule-end');

        if (startHidden) { startHidden.value = ''; startHidden.name = newNamePrefix + 'start_time'; }
        if (endHidden)   { endHidden.value   = ''; endHidden.name   = newNamePrefix + 'end_time';   }
        if (weekdaySelect)               weekdaySelect.name = newNamePrefix + 'weekday';

        rowIndex++;
        scheduleRows.appendChild(newRow);
        recomputeHours();
    });

    // ─────────────────────────────────────────────────────────────────────────
    // "REMOVE" BUTTON — event delegation
    // ─────────────────────────────────────────────────────────────────────────

    scheduleRows.addEventListener('click', function (e) {
        var removeBtn = e.target.closest('.remove-schedule-row');
        if (!removeBtn) return;
        var row = removeBtn.closest('.schedule-row');
        var totalRows = scheduleRows.querySelectorAll('.schedule-row');
        if (totalRows.length > 1) {
            row.remove();
            reindexRows();
            recomputeHours();
        }
    });

    // ─────────────────────────────────────────────────────────────────────────
    // RE-INDEX name ATTRIBUTES AFTER ROW REMOVAL
    // Only updates .schedule-weekday, .schedule-start, .schedule-end
    // which are the three WTForms-submitted fields.
    // ─────────────────────────────────────────────────────────────────────────

    function reindexRows() {
        var rows = scheduleRows.querySelectorAll('.schedule-row');
        rows.forEach(function (row, index) {
            var newNamePrefix = 'schedules-' + index + '-';
            var weekdaySelect = row.querySelector('.schedule-weekday');
            var startHidden   = row.querySelector('.schedule-start');
            var endHidden     = row.querySelector('.schedule-end');
            if (weekdaySelect) weekdaySelect.name = newNamePrefix + 'weekday';
            if (startHidden)   startHidden.name   = newNamePrefix + 'start_time';
            if (endHidden)     endHidden.name     = newNamePrefix + 'end_time';
        });
        rowIndex = rows.length;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RECOMPUTE SCHEDULED HOURS (live cap display)
    // Reads from .schedule-start and .schedule-end hidden fields (HH:MM).
    // This function is identical in logic to the original but explicitly
    // reads from the hidden fields, not from visible text inputs.
    // ─────────────────────────────────────────────────────────────────────────

    function recomputeHours() {
        var startDateInput  = document.getElementById('start_date');
        var endDateInput    = document.getElementById('end_date');
        var totalHoursInput = document.getElementById('total_hours');
        var computedDisplay = document.getElementById('computed-hours-display');
        var capDisplay      = document.getElementById('cap-hours-display');
        var warningSpan     = document.getElementById('hours-warning');
        var submitBtn       = document.getElementById('submit-course-btn');

        var startDateStr = startDateInput.value;
        var endDateStr   = endDateInput.value;
        var totalHours   = parseFloat(totalHoursInput.value) || 0;

        if (!startDateStr || !endDateStr) {
            computedDisplay.textContent    = '0.0';
            capDisplay.textContent         = totalHours > 0 ? totalHours.toFixed(1) : '—';
            warningSpan.style.display      = 'none';
            computedDisplay.style.color    = '';
            if (submitBtn) submitBtn.disabled = false;
            return;
        }

        var start = new Date(startDateStr + 'T00:00:00');
        var end   = new Date(endDateStr   + 'T00:00:00');

        if (start > end) {
            computedDisplay.textContent = '—';
            capDisplay.textContent      = totalHours > 0 ? totalHours.toFixed(1) : '—';
            warningSpan.style.display   = 'none';
            computedDisplay.style.color = '';
            if (submitBtn) submitBtn.disabled = false;
            return;
        }

        var dayMap = {
            Sunday: 0, Monday: 1, Tuesday: 2, Wednesday: 3,
            Thursday: 4, Friday: 5, Saturday: 6
        };
        var computedHours = 0;

        scheduleRows.querySelectorAll('.schedule-row').forEach(function (row) {
            var weekdayEl   = row.querySelector('.schedule-weekday');
            var startHidden = row.querySelector('.schedule-start');
            var endHidden   = row.querySelector('.schedule-end');

            if (!weekdayEl || !startHidden || !endHidden) return;

            var weekday      = weekdayEl.value;
            var startTimeStr = startHidden.value.trim();
            var endTimeStr   = endHidden.value.trim();
            if (!startTimeStr || !endTimeStr) return;

            var startParts = startTimeStr.split(':');
            var endParts   = endTimeStr.split(':');
            if (startParts.length !== 2 || endParts.length !== 2) return;

            var startHour = parseInt(startParts[0], 10);
            var startMin  = parseInt(startParts[1], 10);
            var endHour   = parseInt(endParts[0],   10);
            var endMin    = parseInt(endParts[1],   10);

            if (isNaN(startHour) || isNaN(startMin) ||
                isNaN(endHour)   || isNaN(endMin))   return;

            var duration = (endHour * 60 + endMin - startHour * 60 - startMin) / 60.0;
            if (duration <= 0) return;

            var targetWeekdayInt = dayMap[weekday];
            if (targetWeekdayInt === undefined) return;

            var count = 0;
            var cur   = new Date(start);
            while (cur <= end) {
                if (cur.getDay() === targetWeekdayInt) count++;
                cur.setDate(cur.getDate() + 1);
            }
            computedHours += count * duration;
        });

        computedDisplay.textContent = computedHours.toFixed(1);
        capDisplay.textContent      = totalHours > 0 ? totalHours.toFixed(1) : '—';

        if (totalHours > 0 && computedHours > totalHours) {
            warningSpan.style.display      = 'inline';
            computedDisplay.style.color    = 'red';
            if (submitBtn) submitBtn.disabled = true;
        } else {
            warningSpan.style.display      = 'none';
            computedDisplay.style.color    = '';
            if (submitBtn) submitBtn.disabled = false;
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // EVENT LISTENERS — date and hours cap inputs (unchanged from original)
    // ─────────────────────────────────────────────────────────────────────────

    document.getElementById('start_date').addEventListener('change', recomputeHours);
    document.getElementById('start_date').addEventListener('input',  recomputeHours);
    document.getElementById('end_date').addEventListener('change',   recomputeHours);
    document.getElementById('end_date').addEventListener('input',    recomputeHours);
    document.getElementById('total_hours').addEventListener('change', recomputeHours);
    document.getElementById('total_hours').addEventListener('input',  recomputeHours);

    // ─────────────────────────────────────────────────────────────────────────
    // EVENT DELEGATION — schedule row interactions
    //
    // 'change' fires on <select> elements when the user picks a new option.
    // 'input'  fires on <input type="number"> as the user types.
    // Both are needed because number inputs don't fire 'change' until blur.
    //
    // When a visible time control changes → syncHiddenField() converts the
    // three 12-hour controls into HH:MM and writes it to the hidden field,
    // then calls recomputeHours() automatically.
    //
    // .schedule-weekday changes only need recomputeHours().
    // .schedule-start / .schedule-end are hidden fields; they are never
    // directly edited by the user so they do not need listeners here.
    // ─────────────────────────────────────────────────────────────────────────

    scheduleRows.addEventListener('change', function (e) {
        var t   = e.target;
        var row = t.closest('.schedule-row');
        if (!row) return;

        if (t.classList.contains('schedule-weekday')) {
            recomputeHours();
            return;
        }
        if (t.classList.contains('schedule-hour-start') ||
            t.classList.contains('schedule-min-start')  ||
            t.classList.contains('schedule-ampm-start')) {
            syncHiddenField(row, 'start');
            return;
        }
        if (t.classList.contains('schedule-hour-end') ||
            t.classList.contains('schedule-min-end')  ||
            t.classList.contains('schedule-ampm-end')) {
            syncHiddenField(row, 'end');
            return;
        }
    });

    scheduleRows.addEventListener('input', function (e) {
        var t   = e.target;
        var row = t.closest('.schedule-row');
        if (!row) return;

        if (t.classList.contains('schedule-hour-start') ||
            t.classList.contains('schedule-min-start')) {
            syncHiddenField(row, 'start');
            return;
        }
        if (t.classList.contains('schedule-hour-end') ||
            t.classList.contains('schedule-min-end')) {
            syncHiddenField(row, 'end');
            return;
        }
    });

    // ─────────────────────────────────────────────────────────────────────────
    // INITIAL COMPUTATION
    // ─────────────────────────────────────────────────────────────────────────

    recomputeHours();
});
