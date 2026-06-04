// ZHub Course Center — Vanilla JS

document.addEventListener('DOMContentLoaded', function () {

    // Confirm dialogs for destructive actions
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(el.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Toggle all attendance checkboxes
    var toggleAll = document.getElementById('toggle-all-attendance');
    if (toggleAll) {
        toggleAll.addEventListener('change', function () {
            var checkboxes = document.querySelectorAll('.attendance-toggle');
            checkboxes.forEach(function (cb) {
                cb.checked = toggleAll.checked;
                // Also update corresponding hidden field
                var hiddenField = document.getElementById('status_' + cb.dataset.enrollmentId);
                if (hiddenField) {
                    hiddenField.value = toggleAll.checked ? 'present' : 'absent';
                }
            });
        });
    }

    // Attendance individual toggle — update hidden field
    document.querySelectorAll('.attendance-toggle').forEach(function (cb) {
        cb.addEventListener('change', function () {
            var hiddenField = document.getElementById('status_' + cb.dataset.enrollmentId);
            if (hiddenField) {
                hiddenField.value = cb.checked ? 'present' : 'absent';
            }
        });
    });

    // Role-dependent fields in user creation form
    var roleSelect = document.getElementById('role');
    if (roleSelect) {
        function toggleRoleFields() {
            var role = roleSelect.value;
            var studentFields = document.getElementById('student-fields');
            var instructorFields = document.getElementById('instructor-fields');
            if (studentFields) studentFields.style.display = role === 'student' ? 'block' : 'none';
            if (instructorFields) instructorFields.style.display = role === 'instructor' ? 'block' : 'none';
        }
        roleSelect.addEventListener('change', toggleRoleFields);
        toggleRoleFields(); // Run on page load
    }
});
