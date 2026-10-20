/**
 * Online Feedback Collector & Admin Dashboard
 * Client-side Logic & Interactions
 */

// Rating descriptive text dictionary
const ratingDescriptions = {
    1: { text: "1 Star - Poor Experience", class: "tag-1" },
    2: { text: "2 Stars - Fair / Needs Improvement", class: "tag-2" },
    3: { text: "3 Stars - Good / Met Expectations", class: "tag-3" },
    4: { text: "4 Stars - Very Good / Highly Satisfied", class: "tag-4" },
    5: { text: "5 Stars - Excellent / Outstanding!", class: "tag-5" }
};

let chartInstance = null;
let currentChartType = 'bar';

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Feedback Form Interactions if form exists on page
    initFeedbackForm();

    // 2. Initialize Admin Login Form if on login page
    initLoginForm();

    // 3. Initialize Flash Messages auto-dismiss
    initFlashAlerts();
});

/**
 * Setup Feedback Form validation, star rating widgets, and character counters.
 */
function initFeedbackForm() {
    const form = document.getElementById('feedbackForm');
    if (!form) return;

    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const commentsInput = document.getElementById('comments');
    const charCounter = document.getElementById('charCounter');
    const starLabels = document.querySelectorAll('.star-label');
    const ratingDescriptor = document.getElementById('ratingDescriptor');
    const submitBtn = document.getElementById('submitBtn');

    let selectedRating = null;

    // Check if any radio was pre-checked
    const checkedRadio = document.querySelector('input[name="rating"]:checked');
    if (checkedRadio) {
        selectedRating = parseInt(checkedRadio.value, 10);
        updateRatingDescriptor(selectedRating);
    }

    // Star hover & click interactions
    starLabels.forEach(label => {
        const val = parseInt(label.getAttribute('data-value'), 10);

        // Hover effect
        label.addEventListener('mouseenter', () => {
            updateRatingDescriptor(val, true);
        });

        // Click / Select effect
        label.addEventListener('click', () => {
            selectedRating = val;
            const radio = document.getElementById(`star${val}`);
            if (radio) {
                radio.checked = true;
            }
            updateRatingDescriptor(val, false);
            clearFieldError('ratingError');
        });
    });

    // Reset descriptor when mouse leaves star container
    const starContainer = document.getElementById('starRatingContainer');
    if (starContainer) {
        starContainer.addEventListener('mouseleave', () => {
            if (selectedRating) {
                updateRatingDescriptor(selectedRating, false);
            } else {
                ratingDescriptor.innerHTML = '<span class="rating-hint">Select a rating from 1 to 5</span>';
            }
        });
    }

    function updateRatingDescriptor(ratingVal, isHover = false) {
        if (!ratingDescriptor || !ratingDescriptions[ratingVal]) return;
        const info = ratingDescriptions[ratingVal];
        const prefix = isHover ? '<i class="fa-regular fa-hand-pointer"></i> ' : '<i class="fa-solid fa-check"></i> ';
        ratingDescriptor.innerHTML = `<span class="rating-pill-tag ${info.class}">${prefix}${info.text}</span>`;
    }

    // Comments character counter
    if (commentsInput && charCounter) {
        commentsInput.addEventListener('input', function () {
            const count = this.value.length;
            charCounter.textContent = `${count} / 1000 characters`;
            if (count > 0 && count < 5) {
                showFieldError('commentsError', 'Comments must be at least 5 characters long.');
            } else {
                clearFieldError('commentsError');
            }
        });
    }

    // Name live validation
    if (nameInput) {
        nameInput.addEventListener('blur', function () {
            validateNameField(this);
        });
    }

    // Email live validation
    if (emailInput) {
        emailInput.addEventListener('blur', function () {
            validateEmailField(this);
        });
    }

    // Form submission validation
    form.addEventListener('submit', function (e) {
        let isValid = true;

        // Validate Name
        if (!validateNameField(nameInput)) {
            isValid = false;
        }

        // Validate Email
        if (!validateEmailField(emailInput)) {
            isValid = false;
        }

        // Validate Rating
        const checkedRatingRadio = document.querySelector('input[name="rating"]:checked');
        if (!checkedRatingRadio || !checkedRatingRadio.value) {
            showFieldError('ratingError', 'Please select a rating star (1 to 5).');
            isValid = false;
        } else {
            clearFieldError('ratingError');
        }

        // Validate Comments
        if (!commentsInput || commentsInput.value.trim().length < 5) {
            showFieldError('commentsError', 'Please provide feedback comments (at least 5 characters).');
            if (commentsInput) commentsInput.classList.add('is-invalid');
            isValid = false;
        } else {
            clearFieldError('commentsError');
            if (commentsInput) {
                commentsInput.classList.remove('is-invalid');
                commentsInput.classList.add('is-valid');
            }
        }

        if (!isValid) {
            e.preventDefault();
            return false;
        }

        // Show spinner on button
        if (submitBtn) {
            submitBtn.disabled = true;
            const btnText = submitBtn.querySelector('.btn-text');
            const btnSpinner = submitBtn.querySelector('.btn-spinner');
            if (btnText) btnText.style.display = 'none';
            if (btnSpinner) btnSpinner.style.display = 'inline-flex';
        }
    });
}

function validateNameField(input) {
    if (!input) return false;
    const val = input.value.trim();
    if (val.length < 2) {
        showFieldError('nameError', 'Please enter your full name (at least 2 characters).');
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        return false;
    }
    clearFieldError('nameError');
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    return true;
}

function validateEmailField(input) {
    if (!input) return false;
    const val = input.value.trim();
    const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!emailRegex.test(val)) {
        showFieldError('emailError', 'Please enter a valid email address (e.g., name@example.com).');
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        return false;
    }
    clearFieldError('emailError');
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    return true;
}

function showFieldError(elementId, message) {
    const errorElem = document.getElementById(elementId);
    if (errorElem) {
        errorElem.textContent = message;
    }
}

function clearFieldError(elementId) {
    const errorElem = document.getElementById(elementId);
    if (errorElem) {
        errorElem.textContent = '';
    }
}

/**
 * Auto-dismiss flash alert banners after 6 seconds.
 */
function initFlashAlerts() {
    const flashAlerts = document.querySelectorAll('.flash-alert');
    flashAlerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 500);
        }, 6000);
    });
}

/**
 * Initialize Chart.js rating chart in Admin Dashboard.
 */
function initRatingChart(stats) {
    const canvas = document.getElementById('ratingChart');
    if (!canvas || typeof Chart === 'undefined') return;

    const ctx = canvas.getContext('2d');
    const labels = ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'];
    const dataValues = [
        stats[1] || 0,
        stats[2] || 0,
        stats[3] || 0,
        stats[4] || 0,
        stats[5] || 0
    ];

    const backgroundColors = [
        'rgba(239, 68, 68, 0.85)',   // 1 Star - Red
        'rgba(249, 115, 22, 0.85)',  // 2 Stars - Orange
        'rgba(245, 158, 11, 0.85)',  // 3 Stars - Amber
        'rgba(16, 185, 129, 0.85)',  // 4 Stars - Emerald
        'rgba(79, 70, 229, 0.85)'    // 5 Stars - Indigo
    ];

    const borderColors = [
        '#ef4444',
        '#f97316',
        '#f59e0b',
        '#10b981',
        '#4f46e5'
    ];

    // Destroy existing instance if switching
    if (chartInstance) {
        chartInstance.destroy();
    }

    const config = {
        type: currentChartType,
        data: {
            labels: labels,
            datasets: [{
                label: 'Feedback Submissions',
                data: dataValues,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1.5,
                borderRadius: currentChartType === 'bar' ? 8 : 0,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: currentChartType === 'doughnut',
                    position: 'bottom',
                    labels: {
                        font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600' },
                        padding: 14
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleFont: { family: "'Plus Jakarta Sans', sans-serif", size: 13, weight: '700' },
                    bodyFont: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function (context) {
                            const val = context.raw || 0;
                            const total = dataValues.reduce((a, b) => a + b, 0);
                            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                            return ` ${val} submissions (${pct}%)`;
                        }
                    }
                }
            },
            scales: currentChartType === 'bar' ? {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color: '#64748b',
                        font: { family: "'Plus Jakarta Sans', sans-serif" }
                    },
                    grid: { color: '#f1f5f9' }
                },
                x: {
                    ticks: {
                        color: '#475569',
                        font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600' }
                    },
                    grid: { display: false }
                }
            } : {}
        }
    };

    chartInstance = new Chart(ctx, config);
}

/**
 * Switch Chart.js between Bar and Doughnut representations.
 */
function switchChartType(type) {
    if (type === currentChartType) return;
    currentChartType = type;

    const btnBar = document.getElementById('btnBarChart');
    const btnPie = document.getElementById('btnPieChart');

    if (btnBar && btnPie) {
        if (type === 'bar') {
            btnBar.classList.add('active');
            btnPie.classList.remove('active');
        } else {
            btnPie.classList.add('active');
            btnBar.classList.remove('active');
        }
    }

    if (typeof ratingStatsData !== 'undefined') {
        initRatingChart(ratingStatsData);
    }
}

/**
 * Filter Admin Feedback Table dynamically based on search text and rating dropdown.
 */
function filterFeedbackTable() {
    const searchInput = document.getElementById('tableSearchInput');
    const ratingFilter = document.getElementById('ratingFilterSelect');
    const tableBody = document.getElementById('feedbackTableBody');
    const noResults = document.getElementById('noResultsMessage');
    const countDisplay = document.getElementById('visibleCount');

    if (!tableBody) return;

    const rows = tableBody.querySelectorAll('tr.table-row');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const selectedRating = ratingFilter ? ratingFilter.value : 'all';

    let visibleCount = 0;

    rows.forEach(row => {
        const rating = row.getAttribute('data-rating');
        const textContent = row.textContent.toLowerCase();

        const matchesRating = (selectedRating === 'all' || rating === selectedRating);
        const matchesQuery = (!query || textContent.includes(query));

        if (matchesRating && matchesQuery) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    if (countDisplay) {
        countDisplay.textContent = visibleCount;
    }

    if (noResults) {
        noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    }
}

/**
 * Initialize Admin Login page password toggle and submission feedback.
 */
function initLoginForm() {
    const toggleBtn = document.getElementById('togglePasswordBtn');
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('togglePasswordIcon');
    const loginForm = document.getElementById('adminLoginForm');
    const loginSubmitBtn = document.getElementById('loginSubmitBtn');

    if (toggleBtn && passwordInput && toggleIcon) {
        toggleBtn.addEventListener('click', function () {
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggleIcon.classList.remove('fa-eye');
                toggleIcon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                toggleIcon.classList.remove('fa-eye-slash');
                toggleIcon.classList.add('fa-eye');
            }
        });
    }

    if (loginForm && loginSubmitBtn) {
        loginForm.addEventListener('submit', function () {
            const btnText = loginSubmitBtn.querySelector('.btn-text');
            const btnSpinner = loginSubmitBtn.querySelector('.btn-spinner');
            if (btnText && btnSpinner) {
                btnText.style.display = 'none';
                btnSpinner.style.display = 'inline-flex';
            }
        });
    }
}
