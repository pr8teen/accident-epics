// Global variables
let currentAccidentId = null;
const deploymentModal = new bootstrap.Modal(document.getElementById('deploymentModal'));

// Handle police deployment initiation
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('deploy-police')) {
        currentAccidentId = e.target.getAttribute('data-accident-id');
        const input = e.target.closest('.deploy-police-group').querySelector('.police-count-input');
        const policeCount = parseInt(input.value);
        
        if (policeCount < 1) {
            alert('Please enter a valid number of police units');
            return;
        }
        
        deployPolice(currentAccidentId, policeCount);
    }
    
    // Handle HQ confirmation
    else if (e.target.classList.contains('confirm-hq')) {
        const accidentId = e.target.getAttribute('data-accident-id');
        confirmHQResolution(accidentId);
    }
});

// Handle deployment modal confirmation
document.getElementById('confirmDeployment').addEventListener('click', function() {
    const policeCount = parseInt(document.getElementById('policeCountInput').value);
    if (policeCount < 1) {
        alert('Please enter a valid number of police units');
        return;
    }
    deployPolice(currentAccidentId, policeCount);
    deploymentModal.hide();
});

function deployPolice(accidentId, policeCount) {
    const btn = document.querySelector(`.deploy-police[data-accident-id="${accidentId}"]`);
    const accidentCard = document.getElementById(`accident-${accidentId}`);
    
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass"></i> Deploying...';
    
    fetch('/deploy_police', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `accident_id=${accidentId}&police_count=${policeCount}`
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Update button state
            const deployGroup = btn.closest('.deploy-police-group');
            if (deployGroup) {
                deployGroup.innerHTML = `
                    <button class="btn btn-sm btn-success" disabled>
                        <i class="bi bi-check-circle"></i> ${data.police_count} Police Deployed
                    </button>
                `;
            }
            
            // Show confirmation button
            const confirmBtn = accidentCard.querySelector('.confirm-hq');
            if (confirmBtn) confirmBtn.style.display = 'inline-block';
            
            // Update police count
            updatePoliceCount(data.available_police);
            
            // Add to deployment logs
            addDeploymentLog(data.camera_name, data.police_count, false);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(error.message || 'Failed to deploy police');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-megaphone"></i> Deploy';
    });
}

function confirmHQResolution(accidentId) {
    const btn = document.querySelector(`.confirm-hq[data-accident-id="${accidentId}"]`);
    const accidentCard = document.getElementById(`accident-${accidentId}`);
    
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass"></i> Confirming...';
    
    fetch('/confirm_hq', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `accident_id=${accidentId}`
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Animate and remove card
            accidentCard.classList.add('removing');
            setTimeout(() => {
                accidentCard.remove();
                
                // Update police count
                updatePoliceCount(data.available_police);
                
                // Update deployment logs
                addDeploymentLog(data.camera_name, data.police_freed, true);
                
                // Show empty message if needed
                if (document.querySelectorAll('.accident-card').length === 0) {
                    showNoAccidentsMessage();
                }
            }, 500);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(error.message || 'Failed to confirm resolution');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-building-check"></i> Confirm Resolution';
    });
}

function updatePoliceCount(available) {
    const total = parseInt(document.getElementById('available-police').textContent.split('/')[1]);
    document.getElementById('available-police').textContent = `${available}/${total}`;
    
    const progressBar = document.querySelector('.progress-bar');
    const newWidth = (available / total) * 100;
    progressBar.style.width = `${newWidth}%`;
    progressBar.setAttribute('aria-valuenow', available);
    
    // Update all police count inputs max value
    document.querySelectorAll('.police-count-input').forEach(input => {
        input.max = available;
    });
}

function addDeploymentLog(cameraName, count, completed) {
    const logsContainer = document.getElementById('deploymentLogs');
    const newLog = document.createElement('div');
    newLog.className = `list-group-item ${completed ? 'list-group-item-success' : ''}`;
    
    newLog.innerHTML = `
        <div class="d-flex justify-content-between">
            <strong>${cameraName}</strong>
            <small>${new Date().toLocaleTimeString()}</small>
        </div>
        <div>
            <span class="badge bg-primary">${count} Units</span>
            <span class="badge bg-success">Deployed</span>
            ${completed ? '<span class="badge bg-secondary">Completed</span>' : ''}
        </div>
    `;
    
    // Remove "No deployment logs" message if it exists
    const emptyMessage = logsContainer.querySelector('.text-muted');
    if (emptyMessage) {
        emptyMessage.closest('.list-group-item').remove();
    }
    
    logsContainer.prepend(newLog);
}

function showNoAccidentsMessage() {
    const container = document.getElementById('accidentsContainer');
    container.innerHTML = `
        <div class="alert alert-success m-3">
            <i class="bi bi-check-circle-fill"></i>
            No active accidents - all cases resolved!
        </div>
    `;
}