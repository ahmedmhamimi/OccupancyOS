// OccupancyOS - Frontend Logic

window.addEventListener('load', function() {
    console.log('🚀 Page fully loaded');
    
    const auditForm = document.getElementById('audit-form');
    if (auditForm) {
        auditForm.addEventListener('submit', handleAuditSubmit);
        updateButtonState();
    }
});

async function handleAuditSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = document.getElementById('analyze-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoading = document.getElementById('btn-loading');
    const formError = document.getElementById('form-error');
    const formErrorText = document.getElementById('form-error-text');
    
    if (formError) formError.classList.add('hidden');
    
    // Credit check (only for logged-in users)
    const creditsDisplay = document.getElementById('credits-display');
    if (creditsDisplay) {
        const currentCredits = parseInt(creditsDisplay.textContent.trim()) || 0;
        console.log('💳 Pre-submit credits:', currentCredits);
        
        if (currentCredits <= 0) {
            console.log('❌ Blocking - no credits');
            if (formErrorText) {
                formErrorText.innerHTML = '<p class="font-semibold mb-1">Out of credits!</p><p class="text-sm mb-2">Get 100 more for $4.99</p><a href="https://occupancyos.gumroad.com/l/credits" target="_blank" class="inline-block bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700">Buy Now</a>';
            }
            if (formError) {
                formError.classList.remove('hidden');
                formError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            return;
        }
    }
    
    // Validate property type
    const propertyType = form.property_type.value;
    if (!propertyType) {
        if (formErrorText) formErrorText.textContent = 'Please select a property type';
        if (formError) formError.classList.remove('hidden');
        form.property_type.focus();
        return;
    }
    
    // Prepare data
    const amenityCheckboxes = document.querySelectorAll('.amenity-checkbox:checked');
    const amenities = Array.from(amenityCheckboxes).map(cb => cb.value).join(', ');
    
    const formData = new FormData();
    formData.append('title', form.title.value);
    formData.append('description', form.description.value);
    formData.append('property_type', propertyType);
    formData.append('target_audience', form.target_audience.value || 'All Audiences');
    formData.append('amenities', amenities);
    
    // Loading state
    submitBtn.disabled = true;
    btnText.classList.add('hidden');
    btnLoading.classList.remove('hidden');
    
    try {
        console.log('🚀 Submitting audit...');
        
        const response = await fetch('/api/audit', {
            method: 'POST',
            body: formData
        });
        
        console.log('📡 Response status:', response.status);
        
        const data = await response.json();
        console.log('📦 Full response data:', data);
        
        if (response.ok) {
            console.log('✅ Audit successful!');
            
            // Display results
            displayResults(data);
            
            // Update credits (only for logged-in users)
            if (data.credits_remaining !== undefined && data.credits_remaining !== null && creditsDisplay) {
                const oldCredits = creditsDisplay.textContent.trim();
                console.log('💳 Updating credits:', oldCredits, '→', data.credits_remaining);
                
                creditsDisplay.textContent = data.credits_remaining;
                creditsDisplay.style.color = 'red';
                creditsDisplay.style.fontWeight = 'bold';
                
                setTimeout(() => {
                    creditsDisplay.style.color = '';
                    creditsDisplay.style.fontWeight = '';
                }, 1000);
                
                console.log('✓ Credits now:', creditsDisplay.textContent);
                
                setTimeout(() => updateButtonState(), 300);
                
                if (data.credits_remaining === 0) {
                    setTimeout(() => showNotification('Last credit used!'), 1500);
                }
            }
            
            // Scroll to results
            setTimeout(() => {
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 500);
            
        } else {
            console.error('❌ Audit failed:', data);
            
            let errorMsg = data.error || 'Analysis failed';
            
            if (data.login_required) {
                errorMsg = '<p>Please log in. <a href="/signup" class="underline">Sign up</a> or <a href="/login" class="underline">Log in</a></p>';
            } else if (data.upgrade_required) {
                errorMsg = '<p>Out of credits! <a href="https://occupancyos.gumroad.com/l/credits" target="_blank" class="underline font-semibold">Buy 100 for $4.99 →</a></p>';
            }
            
            if (formErrorText) formErrorText.innerHTML = errorMsg;
            if (formError) formError.classList.remove('hidden');
        }
        
    } catch (error) {
        console.error('❌ Network error:', error);
        if (formErrorText) formErrorText.textContent = 'Network error. Please try again.';
        if (formError) formError.classList.remove('hidden');
    } finally {
        submitBtn.disabled = false;
        btnText.classList.remove('hidden');
        btnLoading.classList.add('hidden');
        setTimeout(() => updateButtonState(), 300);
    }
}

function updateButtonState() {
    const creditsDisplay = document.getElementById('credits-display');
    const submitBtn = document.getElementById('analyze-btn');
    const btnText = document.getElementById('btn-text');
    
    if (!creditsDisplay || !submitBtn || !btnText) return;
    
    const credits = parseInt(creditsDisplay.textContent.trim()) || 0;
    console.log('🔄 Button state update. Credits:', credits);
    
    if (credits <= 0) {
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        btnText.textContent = '⚠️ Out of Credits';
        
        let warningDiv = document.getElementById('credits-warning');
        if (!warningDiv) {
            warningDiv = document.createElement('p');
            warningDiv.id = 'credits-warning';
            warningDiv.className = 'mt-3 text-center';
            warningDiv.innerHTML = '<span class="text-red-600 font-semibold">No credits</span> • <a href="https://occupancyos.gumroad.com/l/credits" target="_blank" class="text-indigo-600 underline font-semibold">Get 100 for $4.99</a>';
            submitBtn.parentElement.appendChild(warningDiv);
        }
    } else {
        submitBtn.disabled = false;
        submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        btnText.textContent = '🚀 Analyze My Listing';
        
        const warningDiv = document.getElementById('credits-warning');
        if (warningDiv) warningDiv.remove();
    }
}

function displayResults(data) {
    console.log('🎨 Displaying results');
    
    const resultsContainer = document.getElementById('results-container');
    if (!resultsContainer) {
        console.error('❌ Results container not found');
        return;
    }
    
    resultsContainer.classList.remove('hidden');
    
    const isPreview = data.is_preview || false;
    console.log('🔒 Preview mode:', isPreview);
    
    // Display all sections
    if (data.overall_score !== undefined) {
        displayOverallScore(data.overall_score, data.overall_explanation);
    }
    
    if (data.detailed_scores) {
        displayDetailedScores(data.detailed_scores);
    }
    
    if (data.optimized_titles) {
        displayOptimizedTitles(data.optimized_titles, isPreview);
    }
    
    if (data.description_rewrite) {
        displayDescriptionRewrite(data.description_rewrite, isPreview);
    }
    
    if (data.amenity_analysis) {
        displayAmenityAnalysis(data.amenity_analysis, isPreview);
    }
    
    if (data.immediate_action_items) {
        displayActionItems(data.immediate_action_items, isPreview);
    }
    
    if (data.critical_warnings && data.critical_warnings.length > 0) {
        displayWarnings(data.critical_warnings);
    }
    
    // Show unlock CTA for preview users
    if (isPreview) {
        showUnlockCTA();
    }
    
    // Animate cards
    const cardIds = [
        'overall-score-card', 'detailed-scores-card', 'titles-card',
        'description-card', 'amenities-card', 'action-items-card'
    ];
    
    cardIds.forEach((id, i) => {
        setTimeout(() => {
            const card = document.getElementById(id);
            if (card) {
                card.classList.remove('opacity-0');
                card.classList.add('fade-in-up');
            }
        }, 100 * (i + 1));
    });
}

function showUnlockCTA() {
    const existingCTA = document.getElementById('unlock-cta');
    if (existingCTA) return;
    
    const cta = document.createElement('div');
    cta.id = 'unlock-cta';
    cta.className = 'fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50 animate-bounce';
    cta.innerHTML = `
        <div class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-8 py-4 rounded-full shadow-2xl flex items-center gap-3 max-w-2xl">
            <svg class="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
            <div>
                <div class="font-bold text-lg">Unlock Full Analysis</div>
                <div class="text-sm opacity-90">Sign up free to see optimized titles & description</div>
            </div>
            <a href="/signup" class="ml-4 bg-white text-indigo-600 px-6 py-2 rounded-full font-bold hover:bg-indigo-50 transition whitespace-nowrap">
                Sign Up Free →
            </a>
        </div>
    `;
    document.body.appendChild(cta);
}

function displayOverallScore(score, explanation) {
    const scoreNumber = document.getElementById('overall-score-number');
    const scoreLabel = document.getElementById('overall-score-label');
    const scoreCircle = document.getElementById('overall-score-circle');
    const scoreExplanation = document.getElementById('overall-score-explanation');
    
    if (!scoreNumber || !scoreLabel || !scoreCircle || !scoreExplanation) return;
    
    let color, label;
    if (score < 40) {
        color = '#dc2626'; label = 'Critical';
    } else if (score < 60) {
        color = '#ea580c'; label = 'Below Average';
    } else if (score < 75) {
        color = '#f59e0b'; label = 'Average';
    } else if (score < 85) {
        color = '#10b981'; label = 'Good';
    } else if (score < 95) {
        color = '#6366f1'; label = 'Excellent';
    } else {
        color = '#8b5cf6'; label = 'Exceptional';
    }
    
    animateNumber(scoreNumber, 0, score, 1500);
    scoreLabel.textContent = label;
    scoreLabel.style.color = color;
    
    const circumference = 439.6;
    const offset = circumference - (score / 100) * circumference;
    scoreCircle.style.stroke = color;
    setTimeout(() => {
        scoreCircle.style.strokeDashoffset = offset;
        scoreCircle.style.transition = 'stroke-dashoffset 2s ease-out';
    }, 100);
    
    scoreExplanation.textContent = explanation;
}

function displayDetailedScores(scores) {
    const grid = document.getElementById('detailed-scores-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    const categories = [
        { key: 'seo_optimization', icon: '🔍', name: 'SEO' },
        { key: 'emotional_appeal', icon: '❤️', name: 'Emotional Appeal' },
        { key: 'description_quality', icon: '📝', name: 'Description' },
        { key: 'amenity_coverage', icon: '✨', name: 'Amenities' },
        { key: 'target_audience_alignment', icon: '🎯', name: 'Audience Fit' },
        { key: 'booking_conversion_potential', icon: '💰', name: 'Conversion' }
    ];
    
    categories.forEach(cat => {
        const data = scores[cat.key];
        if (!data) return;
        
        const color = data.score >= 75 ? 'green' : data.score >= 50 ? 'amber' : 'red';
        
        grid.innerHTML += `
            <div class="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xl">${cat.icon}</span>
                    <span class="text-2xl font-bold text-${color}-600">${data.score}</span>
                </div>
                <h3 class="font-semibold text-sm mb-1">${cat.name}</h3>
                <p class="text-xs text-slate-600">${data.explanation}</p>
            </div>
        `;
    });
}

function displayOptimizedTitles(titles, isPreview = false) {
    const list = document.getElementById('titles-list');
    if (!list) return;
    
    list.innerHTML = '';
    
    const types = [
        { key: 'seo_focused', label: 'SEO', icon: '🔍', color: 'indigo' },
        { key: 'emotional_focused', label: 'Emotional', icon: '❤️', color: 'rose' },
        { key: 'click_optimized', label: 'Curiosity', icon: '⚡', color: 'amber' },
        { key: 'audience_specific', label: 'Targeted', icon: '🎯', color: 'purple' }
    ];
    
    types.forEach(type => {
        const title = titles[type.key];
        if (!title) return;
        
        list.innerHTML += `
            <div class="border-2 border-${type.color}-200 bg-${type.color}-50 rounded-lg p-4 ${isPreview ? 'relative overflow-hidden' : ''}">
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-2">
                        <span class="text-xl">${type.icon}</span>
                        <span class="font-semibold">${type.label}</span>
                    </div>
                    ${!isPreview ? `<button onclick="copyText('${title.replace(/'/g, "\\'")}')' class="text-${type.color}-600 text-sm font-semibold hover:underline">Copy</button>` : ''}
                </div>
                <p class="text-slate-700 ${isPreview ? 'blur-sm select-none' : ''}">${title}</p>
                ${isPreview ? `
                    <div class="absolute inset-0 bg-gradient-to-t from-white via-white/80 to-transparent flex items-end justify-center pb-3">
                        <a href="/signup" class="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 flex items-center gap-1 shadow-lg">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"/></svg>
                            Unlock
                        </a>
                    </div>
                ` : ''}
            </div>
        `;
    });
}

function displayDescriptionRewrite(desc, isPreview = false) {
    const el = document.getElementById('new-description');
    const hookEl = document.getElementById('hook-section');
    const improvementsEl = document.getElementById('key-improvements');
    
    if (el && desc.full_rewrite) {
        // Clean markdown
        let cleanedText = desc.full_rewrite
            .replace(/\*\*(.+?)\*\*/g, '$1')
            .replace(/\*(.+?)\*/g, '$1')
            .replace(/^\* /gm, '• ')
            .replace(/^###? /gm, '')
            .replace(/\[Placeholder[^\]]*\]/gi, '')
            .replace(/\n{3,}/g, '\n\n')
            .trim();
        
        const paragraphs = cleanedText.split('\n\n');
        el.innerHTML = paragraphs.map(p => {
            p = p.trim();
            if (!p) return '';
            
            if (p.includes('• ')) {
                const items = p.split('\n').filter(line => line.trim());
                return '<ul class="list-disc list-inside space-y-1 my-3">' + 
                       items.map(item => `<li>${item.replace(/^[•\-\*]\s*/, '')}</li>`).join('') + 
                       '</ul>';
            }
            
            return `<p class="mb-4">${p}</p>`;
        }).join('');
        
        if (isPreview) {
            el.classList.add('blur-sm', 'select-none');
            el.style.maxHeight = '200px';
            el.style.overflow = 'hidden';
            
            const overlay = document.createElement('div');
            overlay.className = 'absolute inset-0 bg-gradient-to-b from-transparent via-white/60 to-white flex items-end justify-center pb-8';
            overlay.innerHTML = `
                <a href="/signup" class="bg-indigo-600 text-white px-8 py-3 rounded-lg font-bold text-lg hover:bg-indigo-700 shadow-xl flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"/></svg>
                    Sign Up Free to Unlock
                </a>
            `;
            el.parentElement.classList.add('relative');
            el.parentElement.appendChild(overlay);
        }
    }
    
    if (hookEl && desc.hook_section) {
        hookEl.textContent = desc.hook_section
            .replace(/\*\*(.+?)\*\*/g, '$1')
            .replace(/\*(.+?)\*/g, '$1')
            .replace(/\[Placeholder[^\]]*\]/gi, '')
            .trim();
        
        if (isPreview) {
            hookEl.classList.add('blur-sm', 'select-none');
        }
    }
    
    if (improvementsEl && desc.key_improvements) {
        improvementsEl.innerHTML = desc.key_improvements.map(imp => 
            `<li class="${isPreview ? 'blur-sm select-none' : ''}">${imp.replace(/\*\*(.+?)\*\*/g, '$1').replace(/\*(.+?)\*/g, '$1')}</li>`
        ).join('');
    }
}

function displayAmenityAnalysis(data, isPreview = false) {
    const list = document.getElementById('amenities-list');
    if (!list) return;
    
    list.innerHTML = '';
    
    if (data.high_roi_additions && data.high_roi_additions.length > 0) {
        data.high_roi_additions.forEach(item => {
            const priorityColor = item.priority === 'high' ? 'amber' : 'blue';
            
            list.innerHTML += `
                <div class="border-l-4 border-${priorityColor}-500 bg-slate-50 p-4 rounded-r-lg ${isPreview ? 'relative overflow-hidden' : ''}">
                    <div class="flex items-start justify-between mb-2">
                        <h3 class="font-bold text-lg ${isPreview ? 'blur-sm' : ''}">${item.amenity}</h3>
                        <span class="bg-green-100 text-green-800 px-3 py-1 rounded text-sm font-bold ${isPreview ? 'blur-sm' : ''}">${item.estimated_roi}</span>
                    </div>
                    <p class="text-slate-700 text-sm ${isPreview ? 'blur-sm select-none' : ''}">${item.reasoning}</p>
                    ${isPreview ? `
                        <div class="absolute inset-0 bg-white/90 flex items-center justify-center">
                            <a href="/signup" class="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 shadow-lg">
                                Sign Up to See Recommendations
                            </a>
                        </div>
                    ` : ''}
                </div>
            `;
        });
    } else {
        list.innerHTML = '<p class="text-slate-600">✅ Your amenity coverage is excellent!</p>';
    }
}

function displayActionItems(items, isPreview = false) {
    const list = document.getElementById('action-items-list');
    if (!list) return;
    
    list.innerHTML = items.map((item, i) => {
        const impactColor = item.impact === 'high' ? 'green' : 'blue';
        
        return `
            <div class="flex gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200 ${isPreview ? 'relative overflow-hidden' : ''}">
                <div class="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold">${i + 1}</div>
                <div class="flex-1">
                    <h3 class="font-bold mb-1 ${isPreview ? 'blur-sm' : ''}">${item.action}</h3>
                    <p class="text-sm text-slate-600 mb-2 ${isPreview ? 'blur-sm select-none' : ''}">${item.why}</p>
                    <div class="flex gap-2 text-xs ${isPreview ? 'blur-sm' : ''}">
                        <span class="px-2 py-1 bg-${impactColor}-100 text-${impactColor}-800 rounded font-semibold">${item.impact.toUpperCase()} IMPACT</span>
                        <span class="px-2 py-1 bg-slate-200 text-slate-700 rounded font-semibold">${item.effort}</span>
                    </div>
                </div>
                ${isPreview ? `
                    <div class="absolute inset-0 bg-white/90 flex items-center justify-center">
                        <a href="/signup" class="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700">
                            Unlock Action Plan
                        </a>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function displayWarnings(warnings) {
    const card = document.getElementById('warnings-card');
    const list = document.getElementById('warnings-list');
    
    if (!card || !list) return;
    
    if (warnings && warnings.length > 0) {
        card.classList.remove('hidden');
        list.innerHTML = warnings.map(w => `<li>⚠️ ${w}</li>`).join('');
    }
}

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied!');
    }).catch(() => {
        alert('Copy failed. Please copy manually.');
    });
}

function copyToClipboard(elementId) {
    const el = document.getElementById(elementId);
    if (!el) {
        console.error('Element not found:', elementId);
        return;
    }
    
    const text = el.innerText || el.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!');
        
        const originalBg = el.style.backgroundColor;
        el.style.backgroundColor = '#10b981';
        el.style.transition = 'background-color 0.3s';
        
        setTimeout(() => {
            el.style.backgroundColor = originalBg;
        }, 500);
    }).catch(err => {
        console.error('Copy failed:', err);
        alert('Copy failed. Please select and copy manually.');
    });
}

function animateNumber(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current);
    }, 16);
}

function showNotification(message) {
    const notif = document.createElement('div');
    notif.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    notif.textContent = message;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.style.opacity = '0';
        notif.style.transition = 'opacity 0.3s';
        setTimeout(() => document.body.removeChild(notif), 300);
    }, 2000);
}