/**
 * Homophily Study - Frontend JavaScript
 * Modern, clean, with streaming support and counterbalancing.
 */

// State
let state = {
    participantId: null,
    group: null,           // A or B (counterbalance)
    isOutlier: false,      // Low E/Low A user (flipped assignment)
    assignment: null,      // Bot assignments from server
    phase: 0,              // 0=welcome, 1=profile, 2=chat1, 3=rating1, 4=chat2, 5=rating2, 7=done
    chatPhase: 1,          // 1 or 2
    messageCount: 0,
    messagesRequired: 6,
    config: null,
    isStreaming: false
};

// Elements (initialized in DOMContentLoaded)
let sections = {};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOM loaded, initializing...');
    
    // Cache DOM elements
    sections = {
        welcome: document.getElementById('welcome'),
        profile: document.getElementById('profile'),
        chat: document.getElementById('chat'),
        rating: document.getElementById('rating'),
        // preference removed
        complete: document.getElementById('complete')
    };
    
    console.log('Sections found:', Object.keys(sections).filter(k => sections[k]));
    
    // Load config
    try {
        const res = await fetch('/api/config');
        state.config = await res.json();
        state.messagesRequired = state.config.messages_per_bot;
        console.log('Config loaded:', state.config);
        
        // Build dynamic forms
        buildTIPIForm();
        buildRatingForm();
    } catch (e) {
        console.error('Failed to load config:', e);
    }
    
    // Ensure welcome section is visible
    showSection('welcome');
    console.log('Initialization complete');
});

// API helpers
async function api(endpoint, data = null) {
    const options = {
        method: data ? 'POST' : 'GET',
        headers: { 'Content-Type': 'application/json' }
    };
    if (data) options.body = JSON.stringify(data);
    const res = await fetch(`/api${endpoint}`, options);
    return res.json();
}

// Get current chat assignment
function getCurrentChat() {
    if (!state.assignment) return { bot_type: 'high_match', topic: { title: 'general', id: 'unknown' } };
    return state.chatPhase === 1 ? state.assignment.chat1 : state.assignment.chat2;
}

// Section management
function showSection(name) {
    Object.values(sections).forEach(el => {
        if (el) el.classList.remove('active');
    });
    if (sections[name]) {
        sections[name].classList.add('active');
        // Trigger reflow for animations
        sections[name].offsetHeight;
    }
    
    // Hide/show header and progress on welcome page
    const header = document.getElementById('main-header');
    const progress = document.getElementById('progress-container');
    if (header && progress) {
        if (name === 'welcome') {
            header.style.display = 'none';
            progress.style.display = 'none';
        } else {
            header.style.display = 'block';
            progress.style.display = 'block';
        }
    }
    
    updateProgress();
}

function updateProgress() {
    const progressMap = {
        welcome: 0,
        profile: 15,
        chat: state.chatPhase === 1 ? 35 : 65,
        rating: state.chatPhase === 1 ? 50 : 80,
        // preference removed
        complete: 100
    };
    
    const currentSection = Object.keys(sections).find(k => sections[k] && sections[k].classList.contains('active'));
    const percent = progressMap[currentSection] || 0;
    
    const progressFill = document.querySelector('.progress-fill');
    const progressText = document.querySelector('.progress-text');
    if (progressFill) progressFill.style.width = `${percent}%`;
    if (progressText) progressText.textContent = getProgressText();
}

function getProgressText() {
    const texts = {
        welcome: 'Welcome',
        profile: 'Step 1: your profile',
        chat: `Step ${state.chatPhase + 1}: conversation ${state.chatPhase}`,
        rating: `Step ${state.chatPhase + 2}: rate assistant ${state.chatPhase}`,
        // preference removed
        complete: 'Complete!'
    };
    const current = Object.keys(sections).find(k => sections[k] && sections[k].classList.contains('active'));
    return texts[current] || '';
}

// Welcome -> Start
async function startStudy() {
    console.log('startStudy called');
    const btn = document.getElementById('start-btn');
    if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
    }
    
    try {
        console.log('Calling /api/start...');
        const result = await api('/start', {});
        console.log('Got result:', result);
        state.participantId = result.participant_id;
        console.log('Calling showSection("profile")');
        showSection('profile');
    } catch (e) {
        console.error('Failed to start:', e);
        alert('Failed to start study. Please refresh and try again.');
        if (btn) {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }
}

// Build TIPI form dynamically
function buildTIPIForm() {
    const container = document.getElementById('tipi-items');
    if (!state.config || !container) return;
    
    container.innerHTML = '';
    state.config.tipi_items.forEach((item, idx) => {
        const num = idx + 1;
        container.innerHTML += `
            <div class="form-group">
                <label>${num}. ${item}</label>
                <div class="likert-scale">
                    ${[1,2,3,4,5,6,7].map(n => `
                        <div class="likert-option">
                            <input type="radio" name="tipi_${num}" id="tipi_${num}_${n}" value="${n}" required>
                            <label for="tipi_${num}_${n}">${n}</label>
                        </div>
                    `).join('')}
                </div>
                <div class="likert-labels">
                    <span>Disagree strongly</span>
                    <span>Agree strongly</span>
                </div>
            </div>
        `;
    });
}

// Submit profile
async function submitProfile() {
    const form = document.getElementById('profile-form');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const btn = form.querySelector('.btn-primary');
    btn.classList.add('loading');
    btn.disabled = true;
    
    const formData = new FormData(form);
    const profile = {};
    formData.forEach((value, key) => {
        profile[key] = value;
    });
    
    try {
        const result = await api('/profile', {
            participant_id: state.participantId,
            profile: profile
        });
        
        // Store assignment from server
        state.assignment = result.assignment;
        state.isOutlier = result.assignment.is_outlier;
        console.log('Assignment received:', state.assignment);
        
        state.chatPhase = 1;
        startChat();
    } catch (e) {
        console.error('Failed to save profile:', e);
        alert('Failed to save profile. Please try again.');
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// Chat functionality
function startChat() {
    state.messageCount = 0;
    state.isStreaming = false;
    
    const chatInfo = getCurrentChat();
    console.log('Starting chat:', state.chatPhase, chatInfo);
    
    updateChatHeader();
    document.getElementById('chat-messages').innerHTML = '';
    updateMessageCounter();
    showSection('chat');
    
    // Focus input after animation
    setTimeout(() => {
        document.getElementById('chat-input').focus();
    }, 300);
}

function updateChatHeader() {
    const chatInfo = getCurrentChat();
    const topicTitle = chatInfo.topic.title || 'Discussion';
    
    document.querySelector('.chat-header h2').textContent = `Conversation ${state.chatPhase} of 2`;
    document.querySelector('.chat-header .subtitle').textContent = `Come up with 3 arguments for an essay regarding the following question: ${topicTitle}`;
    
    // Update topic display if exists
    const topicDisplay = document.getElementById('chat-topic');
    if (topicDisplay) {
        topicDisplay.textContent = topicTitle;
    }
}

function updateMessageCounter() {
    const remaining = state.messagesRequired - state.messageCount;
    const counter = document.getElementById('message-counter');
    
    if (remaining > 0) {
        counter.textContent = `${remaining} more message${remaining !== 1 ? 's' : ''} to go`;
        counter.style.background = 'var(--primary-50)';
        counter.style.color = 'var(--primary-600)';
    } else {
        counter.textContent = '✓ Minimum reached - continue or proceed to rating';
        counter.style.background = 'rgba(16, 185, 129, 0.1)';
        counter.style.color = '#059669';
    }
    
    // Show/hide next button
    const nextBtn = document.getElementById('chat-next-btn');
    if (state.messageCount >= state.messagesRequired) {
        nextBtn.style.display = 'flex';
    } else {
        nextBtn.style.display = 'none';
    }
}

function addMessage(content, isUser) {
    const messages = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user' : 'bot'}`;
    div.textContent = content;
    messages.appendChild(div);
    scrollToBottom();
    return div;
}

function scrollToBottom() {
    const messages = document.getElementById('chat-messages');
    messages.scrollTo({
        top: messages.scrollHeight,
        behavior: 'smooth'
    });
}

function showTypingIndicator() {
    const messages = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'message bot typing';
    div.id = 'typing-indicator';
    div.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    messages.appendChild(div);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

async function sendMessage() {
    if (state.isStreaming) return;
    
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    
    state.isStreaming = true;
    input.value = '';
    input.disabled = true;
    document.getElementById('send-btn').disabled = true;
    
    addMessage(message, true);
    showTypingIndicator();
    
    // Get current chat assignment
    const chatInfo = getCurrentChat();
    
    try {
        // Use streaming endpoint
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                participant_id: state.participantId,
                phase: state.chatPhase,
                message: message,
                bot_type: chatInfo.bot_type,
                topic: chatInfo.topic
            })
        });
        
        removeTypingIndicator();
        
        // Create bot message element for streaming
        const messages = document.getElementById('chat-messages');
        const botDiv = document.createElement('div');
        botDiv.className = 'message bot';
        messages.appendChild(botDiv);
        
        // Read stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                
                try {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.content) {
                        botDiv.textContent += data.content;
                        scrollToBottom();
                    }
                    
                    if (data.done) {
                        state.messageCount = data.message_count;
                        updateMessageCounter();
                    }
                    
                    if (data.error) {
                        botDiv.textContent = `Error: ${data.error}`;
                        botDiv.style.color = 'var(--error)';
                    }
                } catch (parseError) {
                    console.error('Parse error:', parseError);
                }
            }
        }
    } catch (error) {
        console.error('Stream error:', error);
        removeTypingIndicator();
        addMessage('Sorry, something went wrong. Please try again.', false);
    } finally {
        state.isStreaming = false;
        input.disabled = false;
        document.getElementById('send-btn').disabled = false;
        input.focus();
    }
}

function handleChatKeypress(e) {
    if (e.key === 'Enter' && !e.shiftKey && !state.isStreaming) {
        e.preventDefault();
        sendMessage();
    }
}

function proceedToRating() {
    // Always show the rating questionnaire after each assistant
    buildRatingForm();
    showSection('rating');
}

async function finalizeStudy() {
    const chatInfo = getCurrentChat();
    try {
        await api('/complete', {
            participant_id: state.participantId,
            phase: state.chatPhase,
            bot_type: chatInfo.bot_type,
            topic_id: chatInfo.topic.id
        });

        showSection('complete');
    } catch (e) {
        console.error('Failed to finalize study:', e);
        alert('Failed to finalize study. Please try again.');
    }
}

// Rating form
function buildRatingForm() {
    const container = document.getElementById('rating-questions');
    if (!state.config || !container) return;

    // Update title
    const title = document.querySelector('#rating .card h2');
    if (title) title.textContent = `Rate assistant ${state.chatPhase}`;

    const trustQuestions = [
        'I am confident in the AI assistant.',
        'The AI assistant is reliable.',
        'I can trust the AI assistant.'
    ];

    const engagementQuestions = [
        'I lost myself in the conversation.',
        'The time spent with the agent just slipped away.',
        'I was absorbed in the conversation.',
        'I would recommend this agent.',
        'The conversation with the agent was rewarding.',
        'I felt involved in this experience.'
    ];

    let html = '';

    // Render trust (first 3) then engagement (next 6) as plain sequential questions
    trustQuestions.forEach((q, idx) => {
        const num = idx + 1;
        html += `<div class="form-group"><label>${num}. ${q}</label><div class="likert-scale">`;
        for (let n = 1; n <= 7; n++) {
            html += `<div class="likert-option"><input type="radio" name="trust_${num}" id="trust_${num}_${n}" value="${n}" required><label for="trust_${num}_${n}">${n}</label></div>`;
        }
        html += `</div></div>`;
    });

    engagementQuestions.forEach((q, idx) => {
        const num = idx + 1; // 1..6
        const displayNum = trustQuestions.length + num; // continue numbering
        html += `<div class="form-group"><label>${displayNum}. ${q}</label><div class="likert-scale">`;
        for (let n = 1; n <= 7; n++) {
            html += `<div class="likert-option"><input type="radio" name="engagement_${num}" id="engagement_${num}_${n}" value="${n}" required><label for="engagement_${num}_${n}">${n}</label></div>`;
        }
        html += `</div></div>`;
    });

    html += `<div class="form-group"><label>What stood out about this assistant? (optional)</label><textarea name="open_response" placeholder="Share your thoughts about this conversation..."></textarea></div>`;

    container.innerHTML = html;
}

async function submitRating() {
    const form = document.getElementById('rating-form');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const btn = form.querySelector('.btn-primary');
    btn.classList.add('loading');
    btn.disabled = true;
    
    // Collect and compute trust & engagement aggregates
    const fd = new FormData(form);
    const rating = {};

    // Trust items (1-3)
    const trust_vals = [1,2,3].map(i => parseInt(fd.get(`trust_${i}`), 10));
    const trust_score = trust_vals.reduce((a,b)=>a+b,0)/trust_vals.length;
    rating.trust_item1 = trust_vals[0];
    rating.trust_item2 = trust_vals[1];
    rating.trust_item3 = trust_vals[2];
    rating.trust = trust_score.toFixed(3);

    // Engagement items (1-6). Items 1-3 = FA, 4-6 = RW
    const eng_vals = [1,2,3,4,5,6].map(i => parseInt(fd.get(`engagement_${i}`), 10));
    const fa_vals = eng_vals.slice(0,3);
    const rw_vals = eng_vals.slice(3,6);
    const fa_score = fa_vals.reduce((a,b)=>a+b,0)/fa_vals.length;
    const rw_score = rw_vals.reduce((a,b)=>a+b,0)/rw_vals.length;
    const engagement_score = eng_vals.reduce((a,b)=>a+b,0)/eng_vals.length;

    rating.fa_item1 = fa_vals[0];
    rating.fa_item2 = fa_vals[1];
    rating.fa_item3 = fa_vals[2];
    rating.rw_item1 = rw_vals[0];
    rating.rw_item2 = rw_vals[1];
    rating.rw_item3 = rw_vals[2];
    rating.fa = fa_score.toFixed(3);
    rating.rw = rw_score.toFixed(3);
    rating.engagement = engagement_score.toFixed(3);

    // Open response
    rating.open_response = fd.get('open_response') || '';

    // Get current chat info for metadata
    const chatInfo = getCurrentChat();

    try {
        await api('/rating', {
            participant_id: state.participantId,
            phase: state.chatPhase,
            bot_type: chatInfo.bot_type,
            topic_id: chatInfo.topic.id,
            rating: rating
        });
        
        // Reset form
        form.reset();
        
        if (state.chatPhase === 1) {
            // Move to chat 2
            state.chatPhase = 2;
            startChat();
        } else {
            // After rating the second chat, finalize the study
            finalizeStudy();
        }
    } catch (e) {
        console.error('Failed to submit rating:', e);
        alert('Failed to submit rating. Please try again.');
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// Preference step removed; study finalizes after second chat instead
