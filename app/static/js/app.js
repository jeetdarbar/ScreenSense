document.addEventListener('DOMContentLoaded', function () {
    loadDashboardData();
    setupEventListeners();
    loadCorrelationData();
});

let riskChart = null;

function setupEventListeners() {
    document.getElementById('checkInForm').addEventListener('submit', handleCheckIn);
    // Submit Feedback using the new Morning Report logic
    document.getElementById('submitFeedbackBtn').addEventListener('click', submitFeedback);

    // App Selector Logic
    document.querySelectorAll('.app-pill').forEach(btn => {
        btn.addEventListener('click', () => {
            // Toggle active state
            if (btn.classList.contains('bg-indigo-600')) {
                btn.classList.remove('bg-indigo-600', 'text-white', 'border-indigo-500');
                btn.classList.add('bg-zinc-900/40/10', 'text-gray-300', 'border-white/5');
            } else {
                // Optional: Remove active from others if single select
                document.querySelectorAll('.app-pill').forEach(b => {
                    b.classList.remove('bg-indigo-600', 'text-white', 'border-indigo-500');
                    b.classList.add('bg-zinc-900/40/10', 'text-gray-300', 'border-white/5');
                });

                btn.classList.remove('bg-zinc-900/40/10', 'text-gray-300', 'border-white/5');
                btn.classList.add('bg-indigo-600', 'text-white', 'border-indigo-500');
            }
        });
    });
}

async function loadDashboardData() {
    try {
        const response = await fetch('/dashboard-data');
        const data = await response.json();

        updateUI(data);
        renderChart(data);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function updateUI(data) {
    const stabilityEl = document.getElementById('stabilityIndex');
    stabilityEl.textContent = data.stability_index;

    if (data.stability_index >= 70) stabilityEl.className = 'text-3xl font-bold text-green-400 drop-shadow-[0_0_10px_rgba(74,222,128,0.5)]';
    else if (data.stability_index >= 40) stabilityEl.className = 'text-3xl font-bold text-orange-400 drop-shadow-[0_0_10px_rgba(251,146,60,0.5)]';
    else stabilityEl.className = 'text-3xl font-bold text-red-400 drop-shadow-[0_0_10px_rgba(248,113,113,0.5)]';

    // Update Risk Marker on Load
    updateRiskMarker(data.latest_risk_score);

    // Update Badge (if not already set by specific risk level logic, though risk_level handles color)
    const riskBadge = document.getElementById('riskBadge');
    const riskScoreValue = document.getElementById('riskScoreValue');
    if (data.latest_risk_score !== undefined) {
        riskScoreValue.textContent = data.latest_risk_score;
    }
    if (data.latest_risk_level) {
        riskBadge.textContent = data.latest_risk_level;
        if (data.latest_risk_level === 'Safe') {
            riskBadge.className = 'px-4 py-2 rounded-full text-sm font-bold bg-green-500/20 text-green-300 border border-green-500/30 shadow-[0_0_15px_rgba(74,222,128,0.2)]';
        } else if (data.latest_risk_level === 'Moderate') {
            riskBadge.className = 'px-4 py-2 rounded-full text-sm font-bold bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 shadow-[0_0_15px_rgba(250,204,21,0.2)]';
        } else {
            riskBadge.className = 'px-4 py-2 rounded-full text-sm font-bold bg-red-500/20 text-red-300 border border-red-500/30 shadow-[0_0_15px_rgba(248,113,113,0.3)]';
        }
    }

    // Phase 5: Dynamic Audio Prescription
    if (data.audio_prescription) {
        renderAudioPrescription(data.audio_prescription);
    }
}

function updateRiskMarker(score) {
    const marker = document.getElementById('riskMarker');
    if (marker) {
        // Clamp between 0 and 100
        const position = Math.max(0, Math.min(100, score || 0));
        marker.style.left = `${position}%`;

        // Color code border for extra flair
        if (position > 70) marker.className = marker.className.replace(/border-indigo-900|border-green-600|border-yellow-600/g, 'border-red-600');
        else if (position > 30) marker.className = marker.className.replace(/border-indigo-900|border-green-600|border-red-600/g, 'border-yellow-600');
        else marker.className = marker.className.replace(/border-indigo-900|border-yellow-600|border-red-600/g, 'border-green-600');
    }
}

function renderChart(data) {
    const ctx = document.getElementById('riskChart').getContext('2d');

    if (riskChart) {
        riskChart.destroy();
    }

    riskChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.chart_labels,
            datasets: [{
                label: 'Risk Score',
                data: data.chart_risk_data,
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

async function handleCheckIn(e) {
    e.preventDefault();

    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.textContent = "Calculating...";
    btn.disabled = true;

    const formData = {
        // total_screen_hours removed
        target_bedtime: document.getElementById('targetBedtime').value,
        // Platform Breakdown
        tiktok_ig_hours: document.getElementById('tiktokHours').value || 0,
        youtube_hours: document.getElementById('youtubeHours').value || 0,
        other_socials_hours: document.getElementById('otherSocialsHours').value || 0,
        gaming_hours: document.getElementById('gamingHours').value || 0,

        academic_hours_after_bedtime: document.getElementById('academicHours').value,
        pickups_after_bedtime: document.getElementById('pickups').value,

        // Phase 4: Caffeine
        caffeine_type: document.getElementById('caffeineType').value,
        caffeine_time: document.getElementById('caffeineTime').value,
        caffeine_modifiers: document.getElementById('caffeineModifiers').checked
    };

    try {
        const response = await fetch('/checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            handleRiskResponse(result);
            loadDashboardData();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Check-in failed:', error);
        alert('An unexpected error occurred. Please try again.');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

function handleRiskResponse(result) {
    const riskBadge = document.getElementById('riskBadge');
    const riskScoreValue = document.getElementById('riskScoreValue');
    const nudgeMessage = document.getElementById('nudgeMessage');

    riskScoreValue.textContent = result.risk_score;
    riskBadge.textContent = result.risk_level;

    // Update Risk Marker Position
    updateRiskMarker(result.risk_score);

    // Reset UI states
    document.body.classList.remove('wind-down-active');
    nudgeMessage.classList.add('hidden');
    document.getElementById('insightContainer').classList.add('hidden');

    if (result.risk_level === 'Safe') {
        riskBadge.className = 'px-4 py-2 rounded-full text-sm font-bold bg-green-500/20 text-green-300 border border-green-500/30 shadow-[0_0_15px_rgba(74,222,128,0.2)]';
        nudgeMessage.textContent = "Great job! Your focus is optimized.";
        nudgeMessage.classList.remove('hidden');

    } else if (result.risk_level === 'Moderate') {
        riskBadge.className = 'px-4 py-2 rounded-full text-sm font-bold bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 shadow-[0_0_15px_rgba(250,204,21,0.2)]';
        nudgeMessage.textContent = "Your sleep risk is rising. Try limiting social media.";
        nudgeMessage.classList.remove('hidden');

    } else if (result.risk_level === 'High') {
        riskBadge.className = 'px-4 py-2 rounded-full text-sm font-bold bg-red-500/20 text-red-300 border border-red-500/30 shadow-[0_0_15px_rgba(248,113,113,0.3)]';
        // Only trigger protocol if specifically requested, or just show insight.
        // For this phase, let's just show insight and maybe trigger protocol manually or via button?
        // Protocol trigger was removed in previous refactor step to focus on Insight?
        // Let's re-add simple trigger or just keep it active.
        // initiateWindDownProtocol(); // Optional based on user flow.
    }

    // Display Insight
    if (result.insight) {
        document.getElementById('insightContainer').classList.remove('hidden');
        document.getElementById('insightWhy').textContent = result.insight.why_impact;
        document.getElementById('insightHow').textContent = result.insight.how_action;
    }

    // Phase 5: Dynamic Audio Prescription
    if (result.audio_prescription) {
        renderAudioPrescription(result.audio_prescription);
    }
}

function renderAudioPrescription(prescription) {
    const audioContainer = document.getElementById('audioPrescriptionContainer');
    const reasoningEl = document.getElementById('audioReasoning');
    const audioPlayer = document.getElementById('windDownAudio');
    const audioSource = document.getElementById('audioSource');
    const trackListEl = document.getElementById('audioTrackList');

    // Custom Player Elements
    const trackNameEl = document.getElementById('currentTrackName');
    const trackDescEl = document.getElementById('currentTrackDesc');
    const playIcon = document.getElementById('playIcon');
    const pauseIcon = document.getElementById('pauseIcon');

    if (!audioContainer) return;

    audioContainer.classList.remove('hidden');
    reasoningEl.textContent = prescription.reasoning;

    // Load primary track
    const primary = prescription.primary_track;
    audioSource.src = primary.url;
    audioPlayer.load();

    // Set custom player UI
    trackNameEl.textContent = primary.name;
    trackDescEl.textContent = primary.desc;
    playIcon.classList.remove('hidden');
    pauseIcon.classList.add('hidden');

    // Make toggle function globally accessible
    window.toggleMainAudio = (e) => {
        if (e) e.preventDefault();
        if (audioPlayer.paused) {
            audioPlayer.play();
            playIcon.classList.add('hidden');
            pauseIcon.classList.remove('hidden');
        } else {
            audioPlayer.pause();
            playIcon.classList.remove('hidden');
            pauseIcon.classList.add('hidden');
        }
    };

    // Keep icons in sync if audio stops elsewhere
    audioPlayer.onpause = () => {
        playIcon.classList.remove('hidden');
        pauseIcon.classList.add('hidden');
    };
    audioPlayer.onplay = () => {
        playIcon.classList.add('hidden');
        pauseIcon.classList.remove('hidden');
    };

    // Build alternative tracks list
    trackListEl.innerHTML = '';
    prescription.all_tracks.forEach(track => {
        const btn = document.createElement('button');
        const isPrimary = track.id === primary.id;

        btn.className = `text-left px-4 py-3 rounded-xl border text-sm transition-all flex justify-between items-center ${isPrimary ? 'bg-indigo-600/30 border-indigo-500/50 text-indigo-100' : 'bg-zinc-900/40/5 border-white/10 text-gray-400 hover:bg-zinc-900/40/10 hover:text-white'}`;

        btn.innerHTML = `
            <div>
                <span class="font-bold block">${track.name}</span>
                <span class="text-xs opacity-70">${track.desc}</span>
            </div>
            ${isPrimary ? '<span class="text-amber-500 text-xs uppercase tracking-wider font-bold">Prescribed</span>' : '<span class="opacity-50 text-xs transition-colors hover:text-white">Play</span>'}
        `;

        btn.onclick = () => {
            // Update custom player banner
            trackNameEl.textContent = track.name;
            trackDescEl.textContent = track.desc;

            // Re-render button list to reset text/colors
            Array.from(trackListEl.children).forEach((childBtn, index) => {
                const t = prescription.all_tracks[index];
                const isSelected = t.id === track.id;

                if (isSelected) {
                    childBtn.className = 'text-left px-4 py-3 rounded-xl border text-sm transition-all flex justify-between items-center bg-indigo-600/30 border-indigo-500/50 text-indigo-100 scale-[1.02] shadow-lg shadow-indigo-500/20';
                    childBtn.innerHTML = `
                        <div>
                            <span class="font-bold block">${t.name}</span>
                            <span class="text-xs opacity-70">${t.desc}</span>
                        </div>
                        <span class="text-amber-500 text-xs uppercase tracking-wider font-bold">Playing</span>
                    `;
                } else {
                    const wasPrimary = t.id === primary.id;
                    childBtn.className = 'text-left px-4 py-3 rounded-xl border text-sm transition-all flex justify-between items-center bg-zinc-900/40/5 border-white/10 text-gray-400 hover:bg-zinc-900/40/10 hover:text-white';
                    childBtn.innerHTML = `
                        <div>
                            <span class="font-bold block">${t.name}</span>
                            <span class="text-xs opacity-70">${t.desc}</span>
                        </div>
                        ${wasPrimary ? '<span class="text-amber-500/50 text-xs uppercase tracking-wider font-bold">Prescribed</span>' : '<span class="opacity-50 text-xs transition-colors">Play</span>'}
                    `;
                }
            });

            audioSource.src = track.url;
            audioPlayer.load();
            audioPlayer.play();
        };

        trackListEl.appendChild(btn);
    });
}

async function submitFeedback() {
    const minutes = document.getElementById('feedbackMinutes').value;
    const btn = document.getElementById('submitFeedbackBtn');

    if (!minutes) {
        alert('Please enter time in minutes');
        return;
    }

    // Loading State
    const originalText = btn.textContent;
    btn.textContent = "Analyzing...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/morning_feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                time_to_fall_asleep_mins: minutes,
                morning_grogginess_score: document.getElementById('grogginessScore').value // Phase 4
            })
        });

        const result = await response.json();

        if (response.ok) {
            // Populate Report
            document.getElementById('reportReinforcement').textContent = result.reinforcement;

            // Format analysis text (maybe split if long?)
            document.getElementById('reportAnalysis').textContent = result.analysis;

            const planList = document.getElementById('reportActionPlan');
            planList.innerHTML = ''; // Clear previous

            if (result.action_plan && result.action_plan.length > 0) {
                result.action_plan.forEach((step, index) => {
                    const li = document.createElement('li');
                    li.className = 'flex items-start text-sm text-stone-300';
                    // Add a check icon or step number
                    li.innerHTML = `
                        <span class="flex-shrink-0 w-5 h-5 flex items-center justify-center bg-amber-500/20 text-amber-500 rounded-full text-xs font-bold mr-3 mt-0.5 border border-amber-500/30">
                            ${index + 1}
                        </span>
                        <span>${step}</span>
                    `;
                    planList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.className = 'text-stone-400 text-sm';
                li.textContent = "No specific actions needed. Keep it up!";
                planList.appendChild(li);
            }


            // Switch State UI
            document.getElementById('feedbackInputState').classList.add('hidden');
            const reportState = document.getElementById('feedbackReportState');
            reportState.classList.remove('hidden');
            reportState.classList.remove('block');
            reportState.classList.add('flex');

            loadDashboardData();
        } else {
            console.error('Server error:', result);
            alert(result.error || 'Failed to generate report.');
            btn.textContent = originalText;
            btn.disabled = false;
        }
    } catch (e) {
        console.error('Fetch error:', e);
        alert('Network error. Is the server running?');
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

let correlationChartInstance = null;

async function loadCorrelationData() {
    const loadingState = document.getElementById('correlationLoadingState');
    const container = document.getElementById('correlationContainer');
    const chartCanvas = document.getElementById('correlationPieChart');
    const legendContainer = document.getElementById('correlationLegend');

    loadingState.classList.remove('hidden');
    container.classList.add('hidden');

    try {
        const response = await fetch('/api/analytics/correlations');
        const data = await response.json();

        if (data.error) {
            loadingState.innerHTML = `<p class="text-yellow-400 bg-yellow-900/20 rounded-lg border border-yellow-500/20 p-3">${data.error}</p>`;
            return;
        }

        loadingState.classList.add('hidden');
        container.classList.remove('hidden');
        legendContainer.innerHTML = '';

        const keys = [
            'tiktok_hours', 'youtube_hours', 'other_socials_hours',
            'gaming_hours', 'academic_hours', 'pickups'
        ];

        const chartLabels = [];
        const chartData = [];
        const chartColors = [];
        const chartInsights = [];

        // Define color palette based on correlation risk score
        const getColor = (score, isBorder) => {
            const alpha = isBorder ? '1' : '0.85';
            if (score > 0.5) return `rgba(239, 68, 68, ${alpha})`; // Red
            if (score > 0.2) return `rgba(249, 115, 22, ${alpha})`; // Orange
            if (score > 0.05) return `rgba(234, 179, 8, ${alpha})`; // Yellow
            if (score < -0.2) return `rgba(16, 185, 129, ${alpha})`; // Emerald
            return `rgba(251, 191, 36, ${alpha})`; // Neutral Indigo
        };

        keys.forEach(key => {
            const item = data[key];
            if (!item) return;

            // Normalize 'pickups' (count limit 20) with 'hours' (limit 4) so slices scale uniformly.
            // 20 pickups = 4 hours -> 1 pickup = 0.2 hours (divide by 5)
            let sizeVal = item.avg_usage;
            if (key === 'pickups') {
                sizeVal = sizeVal / 5.0;
            }

            // Ensure minimum slice visibility even if usage is extremely low
            sizeVal = Math.max(sizeVal, 0.3);

            // Prepare chart arrays
            chartLabels.push(item.label);
            chartData.push(sizeVal.toFixed(2));
            chartColors.push(getColor(item.score, false));
            chartInsights.push(item.insight);

            // Generate Custom Legend item for the UI
            const unit = key === 'pickups' ? 'x' : 'hr';
            const legendHtml = `
                <div class="flex items-start space-x-3 p-2.5 rounded-xl bg-zinc-900/40/5 border border-white/5 hover:bg-zinc-900/40/10 transition-colors w-full group cursor-default">
                    <div class="w-3 h-3 rounded-full flex-shrink-0 mt-0.5 shadow-sm" style="background-color: ${getColor(item.score, true)}; box-shadow: 0 0 8px ${getColor(item.score, false)};"></div>
                    <div class="flex-1 min-w-0">
                        <div class="flex justify-between items-baseline mb-0.5">
                            <h4 class="text-xs font-bold text-gray-200 truncate pr-2 group-hover:text-white transition-colors">${item.label}</h4>
                            <span class="text-[10px] text-amber-400 font-mono tracking-wider">${item.avg_usage}${unit} avg</span>
                        </div>
                        <p class="text-[9px] text-stone-400 leading-tight hidden md:block opacity-60 group-hover:opacity-100 transition-opacity whitespace-normal">${item.insight.split(':')[0]}</p>
                    </div>
                </div>
            `;
            legendContainer.insertAdjacentHTML('beforeend', legendHtml);
        });

        // Destroy previous chart instance if re-rendering
        if (correlationChartInstance) {
            correlationChartInstance.destroy();
        }

        const ctx = chartCanvas.getContext('2d');
        correlationChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartLabels,
                datasets: [{
                    data: chartData,
                    backgroundColor: chartColors,
                    borderColor: 'rgba(15, 23, 42, 0.9)', // Deep slate background match
                    borderWidth: 2,
                    hoverOffset: 12,
                    hoverBorderColor: 'rgba(255, 255, 255, 0.5)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '55%',
                animation: {
                    animateScale: true,
                    animateRotate: true
                },
                layout: {
                    padding: 8
                },
                plugins: {
                    legend: {
                        display: false // Disabled native legend for our custom HTML one
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#a5b4fc', // Indigo 300
                        titleFont: { size: 14, weight: 'bold' },
                        bodyColor: '#f1f5f9',
                        bodyFont: { size: 12 },
                        borderColor: 'rgba(251, 191, 36, 0.4)',
                        borderWidth: 1,
                        padding: 14,
                        cornerRadius: 12,
                        displayColors: false,
                        callbacks: {
                            label: function (context) {
                                // Retrieve matching insight for tooltip body
                                return chartInsights[context.dataIndex];
                            }
                        }
                    }
                }
            }
        });

    } catch (e) {
        console.error("Failed to load correlations", e);
        loadingState.innerHTML = `<p class="text-red-500 text-sm bg-red-900/20 p-3 rounded border border-red-500/20">Failed to render chart data.</p>`;
    }
}

// --- Wind-Down Portal Logic ---
let breathInterval;
let breathCycleTimeout;

function openWindDown() {
    const portal = document.getElementById('windDownPortal');
    if (!portal) return;

    // Reset views to Selection Menu
    document.getElementById('windDownSelection').classList.remove('hidden', 'opacity-0');
    document.getElementById('windDownBreathingUI').classList.add('hidden', 'opacity-0');
    document.getElementById('windDownAudioUI').classList.add('hidden', 'opacity-0');

    // Show Portal
    portal.classList.remove('hidden');
    setTimeout(() => {
        portal.classList.remove('opacity-0');
    }, 10);
}

function startBreathingProtocol() {
    document.getElementById('windDownSelection').classList.add('opacity-0');
    setTimeout(() => {
        document.getElementById('windDownSelection').classList.add('hidden');
        document.getElementById('windDownBreathingUI').classList.remove('hidden');
        setTimeout(() => {
            document.getElementById('windDownBreathingUI').classList.remove('opacity-0');
        }, 50);

        const textElement = document.getElementById('breathText');
        runBreathCycle(textElement);
        breathInterval = setInterval(() => runBreathCycle(textElement), 19000);
    }, 300);
}

function startAudioProtocol() {
    document.getElementById('windDownSelection').classList.add('opacity-0');
    setTimeout(() => {
        document.getElementById('windDownSelection').classList.add('hidden');
        document.getElementById('windDownAudioUI').classList.remove('hidden');
        setTimeout(() => {
            document.getElementById('windDownAudioUI').classList.remove('opacity-0');
        }, 50);

        // Auto-play primary track if available
        const audioPlayer = document.getElementById('windDownAudio');
        if (audioPlayer && audioPlayer.src && !audioPlayer.src.endsWith(window.location.host + '/')) {
            audioPlayer.play().catch(e => console.log("Autoplay prevented:", e));
        }
    }, 300);
}

function backToWindDownMenu() {
    // Stop Breathing
    clearInterval(breathInterval);
    clearTimeout(breathCycleTimeout);
    const textElement = document.getElementById('breathText');
    if (textElement) textElement.innerText = "Ready?";

    // Stop Audio
    const audioPlayer = document.getElementById('windDownAudio');
    if (audioPlayer) {
        audioPlayer.pause();
    }

    // Hide sub-UIs
    document.getElementById('windDownBreathingUI').classList.add('opacity-0');
    document.getElementById('windDownAudioUI').classList.add('opacity-0');

    setTimeout(() => {
        document.getElementById('windDownBreathingUI').classList.add('hidden');
        document.getElementById('windDownAudioUI').classList.add('hidden');
        document.getElementById('windDownSelection').classList.remove('hidden');
        setTimeout(() => {
            document.getElementById('windDownSelection').classList.remove('opacity-0');
        }, 50);
    }, 300);
}

function closeWindDown() {
    const portal = document.getElementById('windDownPortal');
    portal.classList.add('opacity-0');

    setTimeout(() => {
        portal.classList.add('hidden');

        // Stop Everything
        clearInterval(breathInterval);
        clearTimeout(breathCycleTimeout);
        const textElement = document.getElementById('breathText');
        if (textElement) textElement.innerText = "Ready?";

        const audioPlayer = document.getElementById('windDownAudio');
        if (audioPlayer) {
            audioPlayer.pause();
        }
    }, 700);
}

function runBreathCycle(element) {
    // 0s - Start Inhale
    element.innerText = "Inhale...";

    // 4s - Start Hold
    breathCycleTimeout = setTimeout(() => {
        element.innerText = "Hold...";
    }, 4000);

    // 11s - Start Exhale (4s + 7s)
    setTimeout(() => {
        element.innerText = "Exhale...";
    }, 11000);
}

// --- Report Export Functions ---
// Phase 7: Dynamic Morning Action Plan & Export

async function downloadReportImage() {
    const reportElement = document.getElementById('reportExportCapture');
    if (!reportElement) return;

    // Optional: Visual user feedback button state
    const originalCursor = document.body.style.cursor;
    document.body.style.cursor = 'wait';

    try {
        const canvas = await html2canvas(reportElement, {
            scale: 2, // Higher resolution
            useCORS: true,
            backgroundColor: "#ffffff"
        });

        const image = canvas.toDataURL("image/png");
        const link = document.createElement('a');
        link.download = `Sleep_Sync_Report_${new Date().toISOString().split('T')[0]}.png`;
        link.href = image;
        link.click();
    } catch (e) {
        console.error("Failed to generate image:", e);
        alert("Failed to save image. Please try again.");
    } finally {
        document.body.style.cursor = originalCursor;
    }
}

async function downloadReportPDF() {
    const reportElement = document.getElementById('reportExportCapture');
    if (!reportElement) return;

    // Optional: Visual user feedback button state
    const originalCursor = document.body.style.cursor;
    document.body.style.cursor = 'wait';

    try {
        const canvas = await html2canvas(reportElement, {
            scale: 2,
            useCORS: true,
            backgroundColor: "#ffffff"
        });

        // Calculate aspect ratio for A4
        const imgWidth = 210; // A4 width in mm
        const pageHeight = 295; // A4 height in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;

        // Make sure jsPDF is loaded via window syntax for CJS/UMD imports
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF('p', 'mm', 'a4');

        // Add header
        pdf.setFontSize(16);
        pdf.setTextColor(79, 70, 229); // Indigo-600
        pdf.text("Sleep Sync - Morning Action Report", imgWidth / 2, 20, { align: "center" });

        // Add the captured image below header
        const imgData = canvas.toDataURL('image/png');
        pdf.addImage(imgData, 'PNG', 10, 30, imgWidth - 20, imgHeight - 20);

        pdf.save(`Sleep_Sync_Report_${new Date().toISOString().split('T')[0]}.pdf`);

    } catch (e) {
        console.error("Failed to generate PDF:", e);
        alert("Failed to save PDF. Please try again.");
    } finally {
        document.body.style.cursor = originalCursor;
    }
}
