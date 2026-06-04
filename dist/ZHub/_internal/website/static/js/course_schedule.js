'use strict';

document.addEventListener('DOMContentLoaded', function() {
    const scheduleRows = document.getElementById('schedule-rows');
    const addScheduleRowBtn = document.getElementById('add-schedule-row');
    let rowIndex = document.querySelectorAll('.schedule-row').length;

    // Add Day button - clone last row
    addScheduleRowBtn.addEventListener('click', function() {
        const lastRow = scheduleRows.querySelector('.schedule-row:last-of-type');
        if (!lastRow) return;

        const newRow = lastRow.cloneNode(true);
        const weekdaySelect = newRow.querySelector('.schedule-weekday');
        const startTimeInput = newRow.querySelector('.schedule-start');
        const endTimeInput = newRow.querySelector('.schedule-end');

        // Clear values
        startTimeInput.value = '';
        endTimeInput.value = '';

        // Update name attributes
        const oldNamePrefix = startTimeInput.name.replace(/start_time$/, '');
        const newNamePrefix = 'schedules-' + rowIndex + '-';

        weekdaySelect.name = newNamePrefix + 'weekday';
        startTimeInput.name = newNamePrefix + 'start_time';
        endTimeInput.name = newNamePrefix + 'end_time';

        rowIndex++;
        scheduleRows.appendChild(newRow);

        recomputeHours();
    });

    // Remove button - event delegation
    scheduleRows.addEventListener('click', function(e) {
        const removeBtn = e.target.closest('.remove-schedule-row');
        if (!removeBtn) return;

        const row = removeBtn.closest('.schedule-row');
        const totalRows = scheduleRows.querySelectorAll('.schedule-row');

        if (totalRows.length > 1) {
            row.remove();
            reindexRows();
            recomputeHours();
        }
    });

    function reindexRows() {
        const rows = scheduleRows.querySelectorAll('.schedule-row');
        rows.forEach((row, index) => {
            const weekdaySelect = row.querySelector('.schedule-weekday');
            const startTimeInput = row.querySelector('.schedule-start');
            const endTimeInput = row.querySelector('.schedule-end');

            const newNamePrefix = 'schedules-' + index + '-';
            weekdaySelect.name = newNamePrefix + 'weekday';
            startTimeInput.name = newNamePrefix + 'start_time';
            endTimeInput.name = newNamePrefix + 'end_time';
        });
        rowIndex = rows.length;
    }

    function recomputeHours() {
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');
        const totalHoursInput = document.getElementById('total_hours');
        const computedDisplay = document.getElementById('computed-hours-display');
        const capDisplay = document.getElementById('cap-hours-display');
        const warningSpan = document.getElementById('hours-warning');
        const submitBtn = document.getElementById('submit-course-btn');

        const startDateStr = startDateInput.value;
        const endDateStr = endDateInput.value;
        const totalHours = parseFloat(totalHoursInput.value) || 0;

        if (!startDateStr || !endDateStr) {
            computedDisplay.textContent = '0.0';
            capDisplay.textContent = totalHours > 0 ? totalHours.toFixed(1) : '—';
            warningSpan.style.display = 'none';
            computedDisplay.style.color = '';
            if (submitBtn) submitBtn.disabled = false;
            return;
        }

        const start = new Date(startDateStr + 'T00:00:00');
        const end = new Date(endDateStr + 'T00:00:00');

        if (start > end) {
            computedDisplay.textContent = '—';
            capDisplay.textContent = totalHours > 0 ? totalHours.toFixed(1) : '—';
            warningSpan.style.display = 'none';
            computedDisplay.style.color = '';
            if (submitBtn) submitBtn.disabled = false;
            return;
        }

        const dayMap = {Sunday: 0, Monday: 1, Tuesday: 2, Wednesday: 3, Thursday: 4, Friday: 5, Saturday: 6};
        let computedHours = 0;

        const rows = scheduleRows.querySelectorAll('.schedule-row');
        rows.forEach(row => {
            const weekday = row.querySelector('.schedule-weekday').value;
            const startTimeStr = row.querySelector('.schedule-start').value.trim();
            const endTimeStr = row.querySelector('.schedule-end').value.trim();

            if (!startTimeStr || !endTimeStr) return;

            const startParts = startTimeStr.split(':');
            const endParts = endTimeStr.split(':');

            if (startParts.length !== 2 || endParts.length !== 2) return;

            const startHour = parseInt(startParts[0], 10);
            const startMin = parseInt(startParts[1], 10);
            const endHour = parseInt(endParts[0], 10);
            const endMin = parseInt(endParts[1], 10);

            if (isNaN(startHour) || isNaN(startMin) || isNaN(endHour) || isNaN(endMin)) return;

            const duration = (endHour * 60 + endMin - startHour * 60 - startMin) / 60.0;
            if (duration <= 0) return;

            const targetWeekdayInt = dayMap[weekday];
            if (targetWeekdayInt === undefined) return;

            let count = 0;
            let cur = new Date(start);
            while (cur <= end) {
                if (cur.getDay() === targetWeekdayInt) count++;
                cur.setDate(cur.getDate() + 1);
            }

            computedHours += count * duration;
        });

        computedDisplay.textContent = computedHours.toFixed(1);
        capDisplay.textContent = totalHours > 0 ? totalHours.toFixed(1) : '—';

        if (totalHours > 0 && computedHours > totalHours) {
            warningSpan.style.display = 'inline';
            computedDisplay.style.color = 'red';
            if (submitBtn) submitBtn.disabled = true;
        } else {
            warningSpan.style.display = 'none';
            computedDisplay.style.color = '';
            if (submitBtn) submitBtn.disabled = false;
        }
    }

    // Attach event listeners
    document.getElementById('start_date').addEventListener('change', recomputeHours);
    document.getElementById('start_date').addEventListener('input', recomputeHours);
    document.getElementById('end_date').addEventListener('change', recomputeHours);
    document.getElementById('end_date').addEventListener('input', recomputeHours);
    document.getElementById('total_hours').addEventListener('change', recomputeHours);
    document.getElementById('total_hours').addEventListener('input', recomputeHours);

    scheduleRows.addEventListener('change', function(e) {
        if (e.target.classList.contains('schedule-weekday') ||
            e.target.classList.contains('schedule-start') ||
            e.target.classList.contains('schedule-end')) {
            recomputeHours();
        }
    });

    scheduleRows.addEventListener('input', function(e) {
        if (e.target.classList.contains('schedule-weekday') ||
            e.target.classList.contains('schedule-start') ||
            e.target.classList.contains('schedule-end')) {
            recomputeHours();
        }
    });

    // Initial computation
    recomputeHours();
});
