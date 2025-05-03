// static/js/progress.js

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Get resources data from Flask
    const resources = window.flaskResources || [];
    console.log('Resources:', resources); // Debug log

    // Calculate statistics
    const stats = {
        total: resources.length,
        completed: resources.filter(r => r.status === 'Completed').length,
        inProgress: resources.filter(r => r.status === 'In Progress').length,
        notStarted: resources.filter(r => r.status === 'Not Started').length
    };
    console.log('Stats:', stats); // Debug log

    // Update summary cards
    document.getElementById('completed-resources').textContent = stats.completed;
    document.getElementById('inprogress-resources').textContent = stats.inProgress;
    document.getElementById('total-resources').textContent = stats.total;

    // Initialize charts
    initializeCharts(stats);

    // Initialize flash cards
    initializeFlashCards();

    // Initialize activity timeline
    initializeActivityTimeline();

    // Filter Resources
    const filterButtons = document.querySelectorAll('[data-filter]');
    const tableRows = document.querySelectorAll('tbody tr');

    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.dataset.filter;
            
            // Update button states
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter rows with animation
            tableRows.forEach(row => {
                const status = row.dataset.status;
                if (filter === 'all' || status === filter) {
                    row.style.display = '';
                    row.style.animation = 'fadeIn 0.3s ease-out';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });

    // Progress Modal
    const progressSlider = document.getElementById('progressSlider');
    const progressValue = document.getElementById('progressValue');
    const statusSelect = document.getElementById('status');
    const updateButtons = document.querySelectorAll('.update-progress');
    const modal = new bootstrap.Modal(document.getElementById('updateProgressModal'));

    // Update progress value display when slider changes
    if (progressSlider) {
    progressSlider.addEventListener('input', function() {
        progressValue.textContent = this.value + '%';
        progressValue.style.color = getProgressColor(this.value);
        
        // Automatically update status based on progress
        if (this.value == 100) {
            statusSelect.value = 'completed';
        } else if (this.value > 0) {
            statusSelect.value = 'in-progress';
        } else {
            statusSelect.value = 'not-started';
        }
    });
    }

    // Update slider when status changes
    statusSelect.addEventListener('change', function() {
        switch(this.value) {
            case 'completed':
                progressSlider.value = 100;
                break;
            case 'in-progress':
                if (progressSlider.value == 0 || progressSlider.value == 100) {
                    progressSlider.value = 50;
                }
                break;
            case 'not-started':
                progressSlider.value = 0;
                break;
        }
        progressValue.textContent = progressSlider.value + '%';
        progressValue.style.color = getProgressColor(progressSlider.value);
    });

    // Initialize modal with resource data when opened
    updateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const resourceId = this.dataset.resourceId;
            const resource = resources.find(r => r.id == resourceId);
            
            if (resource) {
                // Set the resource ID
            document.getElementById('resourceId').value = resourceId;
                
                // Set the progress slider and value
                progressSlider.value = resource.progress || 0;
                progressValue.textContent = (resource.progress || 0) + '%';
                progressValue.style.color = getProgressColor(resource.progress || 0);
                
                // Set the status
                statusSelect.value = resource.status.toLowerCase().replace(' ', '-');
                
                // Set notes if they exist
                const notesTextarea = document.getElementById('notes');
                if (notesTextarea) {
                    notesTextarea.value = resource.notes || '';
                }
            }
            
            modal.show();
        });
    });

    // Helper function to get color based on progress
    function getProgressColor(value) {
        if (value == 100) return '#28a745';
        if (value > 0) return '#ffc107';
        return '#6c757d';
    }

    document.getElementById('saveProgress').addEventListener('click', function() {
        const resourceId = document.getElementById('resourceId').value;
        const progress = progressSlider.value;
        const status = statusSelect.value;
        const notes = document.getElementById('notes').value;

        // Show loading state
        const saveButton = this;
        const originalText = saveButton.innerHTML;
        saveButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        saveButton.disabled = true;

        // Send progress update to server
        fetch('/update_progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                resource_id: resourceId,
                progress: progress,
                status: status,
                notes: notes
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success toast
                showToast('Progress updated successfully!', 'success');
                modal.hide();
                setTimeout(() => location.reload(), 1000); // Refresh after toast
                
                // Show motivational message after successful save
                setTimeout(showMotivationalMessage, 1000);
            } else {
                showToast('Error updating progress: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error updating progress. Please try again.', 'error');
        })
        .finally(() => {
            // Restore button state
            saveButton.innerHTML = originalText;
            saveButton.disabled = false;
        });
    });

    // Initialize Charts
    function initializeCharts(stats) {
        console.log('Initializing charts with stats:', stats); // Debug log

        // Overall Progress Chart
        const overallProgressCtx = document.getElementById('overallProgressChart');
        if (overallProgressCtx) {
            console.log('Creating overall progress chart'); // Debug log
            new Chart(overallProgressCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Completed', 'In Progress', 'Not Started'],
                    datasets: [{
                        data: [stats.completed, stats.inProgress, stats.notStarted],
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',  // Success green
                            'rgba(255, 193, 7, 0.8)',  // Warning yellow
                            'rgba(108, 117, 125, 0.8)' // Secondary gray
                        ],
                        borderColor: [
                            'rgba(40, 167, 69, 1)',
                            'rgba(255, 193, 7, 1)',
                            'rgba(108, 117, 125, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const value = context.raw;
                                    const percentage = Math.round((value / total) * 100);
                                    return `${context.label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        }

        // Progress by Subject Chart
        const subjectProgressCtx = document.getElementById('progressBySubjectChart');
        if (subjectProgressCtx) {
            console.log('Creating subject progress chart'); // Debug log
            
            // Group resources by subject
            const subjectData = {};
            resources.forEach(resource => {
                const subject = resource.subject || 'Uncategorized';
                if (!subjectData[subject]) {
                    subjectData[subject] = {
                        completed: 0,
                        inProgress: 0,
                        notStarted: 0
                    };
                }
                const status = resource.status.toLowerCase().replace(' ', '');
                if (status === 'completed') subjectData[subject].completed++;
                else if (status === 'inprogress') subjectData[subject].inProgress++;
                else subjectData[subject].notStarted++;
            });

            const subjects = Object.keys(subjectData);
            const completedData = subjects.map(subject => subjectData[subject].completed);
            const inProgressData = subjects.map(subject => subjectData[subject].inProgress);
            const notStartedData = subjects.map(subject => subjectData[subject].notStarted);

            new Chart(subjectProgressCtx, {
                type: 'bar',
                data: {
                    labels: subjects,
                    datasets: [
                        {
                            label: 'Completed',
                            data: completedData,
                            backgroundColor: 'rgba(40, 167, 69, 0.8)',
                            borderColor: 'rgba(40, 167, 69, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'In Progress',
                            data: inProgressData,
                            backgroundColor: 'rgba(255, 193, 7, 0.8)',
                            borderColor: 'rgba(255, 193, 7, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Not Started',
                            data: notStartedData,
                            backgroundColor: 'rgba(108, 117, 125, 0.8)',
                            borderColor: 'rgba(108, 117, 125, 1)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            stacked: true,
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.raw}`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // Initialize Flash Cards
    function initializeFlashCards() {
        const flashCards = document.querySelectorAll('.flash-card');
        flashCards.forEach(card => {
            card.addEventListener('click', function() {
                this.classList.toggle('flipped');
            });
        });
    }

    // Initialize Activity Timeline
    function initializeActivityTimeline() {
        const timelineItems = document.querySelectorAll('.timeline-item');
        timelineItems.forEach((item, index) => {
            setTimeout(() => {
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    // Toast notification function
    function showToast(message, type = 'success') {
        const toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toastContainer.remove();
        });
    }

    const suggestionsList = document.getElementById('suggestions-list');
    if (!suggestionsList) {
        console.error("Suggestions list element not found.");
        return;
    }
    suggestionsList.innerHTML = '';

    // Check if resources exist and handle empty state
    if (!resources || resources.length === 0) {
        suggestionsList.innerHTML = '<li>Add some resources to start tracking your progress!</li>';
        const chartsSection = document.querySelector('.charts-section');
        const summarySection = document.querySelector('.progress-summary');
        if (chartsSection) chartsSection.style.display = 'none';
        if (summarySection) summarySection.style.display = 'none';
        return;
    }

    // Process Data
    let totalResources = resources.length;
    let completedCount = 0;
    let inProgressCount = 0;
    let notStartedCount = 0;
    const progressBySubject = {};
    const progressByDifficulty = {};

    resources.forEach(res => {
        const status = (res.progress || 'Not Started').toLowerCase();
        const subject = res.subject || 'Uncategorized';
        const difficulty = res.difficulty || 'Uncategorized';

        if (status === 'completed') completedCount++;
        else if (status === 'in progress') inProgressCount++;
        else notStartedCount++;

        if (!progressBySubject[subject]) {
            progressBySubject[subject] = { total: 0, completed: 0, inProgress: 0 };
        }
        progressBySubject[subject].total++;
        if (status === 'completed') progressBySubject[subject].completed++;
        if (status === 'in progress') progressBySubject[subject].inProgress++;

         if (!progressByDifficulty[difficulty]) {
            progressByDifficulty[difficulty] = { total: 0, completed: 0, inProgress: 0 };
        }
        progressByDifficulty[difficulty].total++;
        if (status === 'completed') progressByDifficulty[difficulty].completed++;
        if (status === 'in progress') progressByDifficulty[difficulty].inProgress++;
    });

    const completionRate = totalResources > 0 ? Math.round((completedCount / totalResources) * 100) : 0;

    // Generate Suggestions
    const suggestions = [];
    if (completionRate < 30 && totalResources > 0) {
        suggestions.push("Focus on completing resources marked 'In Progress' before starting too many new ones.");
    }
    if (notStartedCount > completedCount + inProgressCount && totalResources > 2) {
         suggestions.push("You have several resources not started. Try picking one that seems interesting or easy to begin!");
    }
    if (completionRate > 75) {
        suggestions.push("Great progress! Consider adding resources on new subjects or increasing the difficulty.");
    }
    for (const subject in progressBySubject) {
        const subjData = progressBySubject[subject];
        if (subjData.total > 1 && (subjData.completed / subjData.total) < 0.4) {
            suggestions.push(`Consider revisiting resources in the '${subject}' subject to boost completion.`);
            break;
        }
    }
     if (progressByDifficulty['Hard'] && progressByDifficulty['Easy'] &&
         (progressByDifficulty['Hard'].total - progressByDifficulty['Hard'].completed) > 2 &&
        progressByDifficulty['Easy'].total > 0 &&
         (progressByDifficulty['Easy'].completed / progressByDifficulty['Easy'].total) < 0.6) {
         suggestions.push("Try tackling some 'Easy' or 'Medium' resources if you're finding 'Hard' ones challenging right now.");
     }
    if (suggestions.length === 0 && totalResources > 0) {
         suggestions.push("Keep up the great work organizing and tracking your studies!");
     }

    suggestions.forEach(text => {
        const li = document.createElement('li');
        li.textContent = text;
        suggestionsList.appendChild(li);
    });

    // Add motivational messages
    const motivationalMessages = [
        "Every step forward is progress, no matter how small!",
        "You're doing great! Keep up the good work!",
        "Learning is a journey, and you're making amazing progress!",
        "Your dedication to learning is inspiring!",
        "Remember: Rome wasn't built in a day. Keep going!",
        "You're building knowledge one resource at a time!",
        "Progress is progress, no matter the pace!",
        "Your commitment to learning is commendable!",
        "Every completed resource is a step closer to mastery!",
        "You're creating a brighter future through learning!"
    ];

    function showMotivationalMessage() {
        const message = motivationalMessages[Math.floor(Math.random() * motivationalMessages.length)];
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-primary border-0';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-lightbulb me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        const toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toastContainer.remove();
        });
    }

    // Show initial motivational message
    setTimeout(showMotivationalMessage, 2000);
});