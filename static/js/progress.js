// static/js/progress.js

// Initialize variables
let overallChart = null;
let subjectChart = null;

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing progress tracking...');
    console.log('Resources data:', window.flaskResources);

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize statistics
    updateStatistics();

    // Initialize charts
    initializeCharts();

    // Initialize modal functionality
    initializeModal();

    // Initialize filter buttons
    initializeFilters();

    // Animate timeline items
    const timelineItems = document.querySelectorAll('.timeline-item');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('show');
            }
        });
    });

    timelineItems.forEach(item => observer.observe(item));

    console.log('Progress tracking initialization complete');
});

function updateStatistics() {
    const resources = window.flaskResources;
    const totalResources = resources.length;
    const completedResources = resources.filter(r => r.progress === 'completed').length;
    const inProgressResources = resources.filter(r => r.progress === 'in-progress').length;
    const notStartedResources = resources.filter(r => r.progress === 'not-started').length;
    
    // Update statistics display
    const totalElement = document.getElementById('total-resources');
    const completedElement = document.getElementById('completed-resources');
    const inProgressElement = document.getElementById('inprogress-resources');
    
    if (totalElement) {
        totalElement.textContent = totalResources;
        const totalProgressBar = totalElement.closest('.stat-card').querySelector('.progress-bar');
        if (totalProgressBar) {
            totalProgressBar.style.width = '100%';
        }
    }
    
    if (completedElement) {
        completedElement.textContent = completedResources;
        const completedProgressBar = completedElement.closest('.stat-card').querySelector('.progress-bar');
        if (completedProgressBar) {
            const completedPercentage = totalResources > 0 ? (completedResources / totalResources) * 100 : 0;
            completedProgressBar.style.width = `${completedPercentage}%`;
        }
    }
    
    if (inProgressElement) {
        inProgressElement.textContent = inProgressResources;
        const inProgressProgressBar = inProgressElement.closest('.stat-card').querySelector('.progress-bar');
        if (inProgressProgressBar) {
            const inProgressPercentage = totalResources > 0 ? (inProgressResources / totalResources) * 100 : 0;
            inProgressProgressBar.style.width = `${inProgressPercentage}%`;
        }
    }
    
    // Update overall progress bar
    const progressPercentage = totalResources > 0 ? (completedResources / totalResources) * 100 : 0;
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = `${progressPercentage}%`;
        progressBar.textContent = `${Math.round(progressPercentage)}%`;
    }
}

function initializeCharts() {
    const resources = window.flaskResources;
    
    // Prepare data for overall progress chart
    const completedCount = resources.filter(r => r.progress === 'completed').length;
    const inProgressCount = resources.filter(r => r.progress === 'in-progress').length;
    const notStartedCount = resources.filter(r => r.progress === 'not-started').length;
    
    // Create overall progress chart
    const overallCtx = document.getElementById('overallProgressChart');
    if (overallCtx) {
        if (overallChart) {
            overallChart.destroy();
        }
        overallChart = new Chart(overallCtx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'In Progress', 'Not Started'],
                datasets: [{
                    data: [completedCount, inProgressCount, notStartedCount],
                    backgroundColor: ['#28a745', '#ffc107', '#6c757d']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Prepare data for subject progress chart
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
        if (resource.progress === 'completed') {
            subjectData[subject].completed++;
        } else if (resource.progress === 'in-progress') {
            subjectData[subject].inProgress++;
        } else {
            subjectData[subject].notStarted++;
        }
    });
    
    // Create subject progress chart
    const subjectCtx = document.getElementById('progressBySubjectChart');
    if (subjectCtx) {
        if (subjectChart) {
            subjectChart.destroy();
        }
        subjectChart = new Chart(subjectCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(subjectData),
                datasets: [
                    {
                        label: 'Completed',
                        data: Object.values(subjectData).map(data => data.completed),
                        backgroundColor: '#28a745'
                    },
                    {
                        label: 'In Progress',
                        data: Object.values(subjectData).map(data => data.inProgress),
                        backgroundColor: '#ffc107'
                    },
                    {
                        label: 'Not Started',
                        data: Object.values(subjectData).map(data => data.notStarted),
                        backgroundColor: '#6c757d'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Subjects'
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Resources'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    }
                }
            }
        });
    }
}

function initializeModal() {
    const editButtons = document.querySelectorAll('.update-progress');
    const modal = document.getElementById('updateProgressModal');
    const progressSlider = document.getElementById('progressPercentage');
    const progressValue = document.getElementById('progressValue');
    const notesTextarea = document.getElementById('progressNotes');
    const saveButton = document.getElementById('saveProgress');
    let currentResourceId = null;
    
    // Handle radio button changes
    const radioButtons = document.querySelectorAll('input[name="status"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            if (progressSlider && progressValue) {
                if (this.value === 'completed') {
                    progressSlider.value = 100;
                    progressValue.textContent = '100%';
                } else if (this.value === 'not-started') {
                    progressSlider.value = 0;
                    progressValue.textContent = '0%';
                } else if (this.value === 'in-progress') {
                    // Keep current value if it's between 1-99, otherwise set to 50
                    const currentValue = parseInt(progressSlider.value);
                    if (currentValue === 0 || currentValue === 100) {
                        progressSlider.value = 50;
                        progressValue.textContent = '50%';
                    }
                }
            }
        });
    });
    
    // Handle progress slider
    if (progressSlider) {
        progressSlider.addEventListener('input', function() {
            progressValue.textContent = `${this.value}%`;
            // If slider is moved to 100%, automatically check completed
            if (this.value === '100') {
                document.getElementById('completed').checked = true;
            }
            // If slider is moved to 0%, automatically check not-started
            else if (this.value === '0') {
                document.getElementById('notStarted').checked = true;
            }
            // If slider is between 1-99, automatically check in-progress
            else {
                document.getElementById('inProgress').checked = true;
            }
        });
    }
    
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const resourceId = this.dataset.resourceId;
            const resource = window.flaskResources.find(r => r.id === parseInt(resourceId));
            
            if (resource) {
                currentResourceId = resourceId;
                document.getElementById('resourceId').value = resourceId;
                
                // Set radio button based on status
                const status = resource.progress.toLowerCase().replace(' ', '-');
                const radioButton = document.getElementById(status);
                if (radioButton) {
                    radioButton.checked = true;
                    // Trigger the change event to set the correct percentage
                    radioButton.dispatchEvent(new Event('change'));
                }
                
                // Set progress percentage
                if (progressSlider) {
                    progressSlider.value = resource.progress_percentage || 0;
                    progressValue.textContent = `${progressSlider.value}%`;
                }
                
                // Set notes
                if (notesTextarea) {
                    notesTextarea.value = resource.notes || '';
                }
                
                const modalInstance = new bootstrap.Modal(modal);
                modalInstance.show();
            }
        });
    });
    
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            if (!currentResourceId) return;
            
            const selectedStatus = document.querySelector('input[name="status"]:checked');
            if (!selectedStatus) {
                alert('Please select a status');
                return;
            }
            
            const status = selectedStatus.value;
            const progressPercentage = progressSlider ? progressSlider.value : 0;
            const notes = notesTextarea ? notesTextarea.value : '';
            
            // Show loading state
            saveButton.disabled = true;
            saveButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Saving...';
            
            fetch('/update_progress', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    resource_id: currentResourceId,
                    status: status,
                    progress_percentage: progressPercentage,
                    notes: notes
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Close the modal
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                    
                    // Reload the page immediately
                    window.location.reload();
                } else {
                    alert('Error updating progress: ' + data.message);
                    // Reset button state
                    saveButton.disabled = false;
                    saveButton.innerHTML = '<i class="fa-solid fa-save me-2"></i>Save Changes';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error updating progress. Please try again.');
                // Reset button state
                saveButton.disabled = false;
                saveButton.innerHTML = '<i class="fa-solid fa-save me-2"></i>Save Changes';
            });
        });
    }
}

function updateResourceRow(resourceId, status, progressPercentage, notes) {
    const row = document.querySelector(`tr[data-resource-id="${resourceId}"]`);
    if (!row) return;
    
    // Update status cell
    const statusCell = row.querySelector('.resource-status');
    if (statusCell) {
        statusCell.textContent = status;
    }
    
    // Update progress bar
    const progressBar = row.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.className = 'progress-bar';
        if (status === 'completed') {
            progressBar.classList.add('bg-success');
            progressBar.style.width = '100%';
        } else if (status === 'in-progress') {
            progressBar.classList.add('bg-warning');
            progressBar.style.width = `${progressPercentage}%`;
        } else {
            progressBar.classList.add('bg-secondary');
            progressBar.style.width = '0%';
        }
    }
    
    // Update last studied
    const lastStudiedCell = row.querySelector('td:nth-last-child(2)');
    if (lastStudiedCell) {
        lastStudiedCell.textContent = new Date().toLocaleString();
    }

    // Update row data-status attribute
    row.setAttribute('data-status', status);

    // Update recent activity
    updateRecentActivity(resourceId, status, notes);
}

function updateRecentActivity(resourceId, status, notes) {
    const resource = window.flaskResources.find(r => r.id === parseInt(resourceId));
    if (!resource) return;

    const timeline = document.querySelector('.timeline');
    if (!timeline) return;

    // Create new timeline item
    const timelineItem = document.createElement('div');
    timelineItem.className = 'timeline-item';
    
    // Set icon and color based on status
    let iconClass = 'fa-circle';
    let bgClass = 'bg-secondary';
    if (status === 'completed') {
        iconClass = 'fa-check';
        bgClass = 'bg-success';
    } else if (status === 'in-progress') {
        iconClass = 'fa-clock';
        bgClass = 'bg-warning';
    }

    // Format status text
    const statusText = status.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());

    // Create the HTML for the timeline item
    timelineItem.innerHTML = `
        <div class="card">
            <div class="card-body">
                <div class="d-flex align-items-center">
                    <div class="timeline-icon ${bgClass} text-white">
                        <i class="fa-solid ${iconClass}"></i>
                    </div>
                    <div class="ms-3 flex-grow-1">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="mb-1">${resource.title}</h5>
                            <span class="badge ${bgClass}">${statusText}</span>
                        </div>
                        <p class="text-muted mb-0">
                            <small>
                                <i class="fa-solid fa-clock me-1"></i>
                                ${new Date().toLocaleString()}
                            </small>
                        </p>
                        ${notes ? `
                        <p class="text-muted mt-2 mb-0 small">
                            <i class="fa-solid fa-note-sticky me-1"></i>
                            ${notes}
                        </p>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add animation class
    timelineItem.classList.add('animate-fadeInUp');

    // Insert at the beginning of the timeline
    timeline.insertBefore(timelineItem, timeline.firstChild);

    // Remove the last item if there are more than 5
    const items = timeline.querySelectorAll('.timeline-item');
    if (items.length > 5) {
        timeline.removeChild(items[items.length - 1]);
    }

    // Add show class after a small delay for animation
    setTimeout(() => {
        timelineItem.classList.add('show');
    }, 50);
}

function initializeFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const resourceRows = document.querySelectorAll('tbody tr');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const status = this.dataset.status;
            
            // Update active state of buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter rows
            resourceRows.forEach(row => {
                if (status === 'all' || row.dataset.status === status) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });
}