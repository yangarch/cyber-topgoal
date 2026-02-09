
const API_BASE = '/api';

// State
let library = [];
let queue = [];
let currentTrackIndex = -1;
let isShuffle = false;

// DOM Elements
const trackListEl = document.getElementById('track-list');
const audioPlayer = document.getElementById('audio-player');
const npTitle = document.getElementById('np-title');
const npArtist = document.getElementById('np-artist');
const btnPlay = document.getElementById('btn-play');
const btnPrev = document.getElementById('btn-prev');
const btnNext = document.getElementById('btn-next');
const btnShuffle = document.getElementById('btn-shuffle');
const commentListEl = document.getElementById('comment-list');
const commentForm = document.getElementById('comment-form');

// Initialization
async function init() {
    await fetchLibrary();
    await fetchComments();
    setupEventListeners();
}

// Library Logic
async function fetchLibrary() {
    try {
        const res = await fetch(`${API_BASE}/library`);
        library = await res.json();
        renderLibrary();
    } catch (e) {
        console.error("Failed to fetch library:", e);
    }
}

function renderLibrary() {
    trackListEl.innerHTML = '';
    library.forEach((track) => {
        const li = document.createElement('li');
        li.className = 'track-item';
        li.dataset.id = track.id;
        
        li.innerHTML = `
            <div class="track-info">
                <span class="track-title">${track.title}</span>
                <span class="track-artist">${track.artist}</span>
            </div>
        `;
        
        li.addEventListener('click', () => {
             playTrack(track);
        });
        
        trackListEl.appendChild(li);
    });
}

function updateActiveTrackUI(trackId) {
    document.querySelectorAll('.track-item').forEach(li => {
        li.classList.remove('active');
        if (li.dataset.id === trackId) {
            li.classList.add('active');
        }
    });
}

// Player Logic
function playTrack(track) {
    if (!track) return;
    
    // Update queue if not playing from queue
    // For MVP, simplistic queue: just play the clicked track
    // Ideally, we'd have a smarter queue system. 
    // Here we find the index of this track in the library to enable next/prev
    queue = library; 
    currentTrackIndex = library.findIndex(t => t.id === track.id);
    
    _loadAndPlay(track);
}

function _loadAndPlay(track) {
    audioPlayer.src = `${API_BASE}/stream/${track.id}`;
    audioPlayer.play().catch(e => console.error("Play failed:", e));
    
    npTitle.textContent = track.title;
    npArtist.textContent = track.artist;
    updateActiveTrackUI(track.id);
    updatePlayButton(true);

    if ('mediaSession' in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({
            title: track.title,
            artist: track.artist,
            album: track.album,
            artwork: [
                { src: `${API_BASE}/cover/${track.id}`, sizes: '512x512', type: 'image/png' }
            ]
        });
    }
}

function togglePlay() {
    if (audioPlayer.paused) {
        audioPlayer.play();
        updatePlayButton(true);
    } else {
        audioPlayer.pause();
        updatePlayButton(false);
    }
}

function updatePlayButton(isPlaying) {
    btnPlay.textContent = isPlaying ? "⏸" : "▶";
}

function nextTrack() {
    if (queue.length === 0) return;
    
    if (isShuffle) {
        currentTrackIndex = Math.floor(Math.random() * queue.length);
    } else {
        currentTrackIndex = (currentTrackIndex + 1) % queue.length;
    }
    _loadAndPlay(queue[currentTrackIndex]);
}

function prevTrack() {
    if (queue.length === 0) return;
    
    if (audioPlayer.currentTime > 3) {
        audioPlayer.currentTime = 0;
        return;
    }
    
    if (isShuffle) {
         currentTrackIndex = Math.floor(Math.random() * queue.length);
    } else {
         currentTrackIndex = (currentTrackIndex - 1 + queue.length) % queue.length;
    }
    _loadAndPlay(queue[currentTrackIndex]);
}

// Guestbook Logic
async function fetchComments() {
    try {
        const res = await fetch(`${API_BASE}/comments`);
        const comments = await res.json();
        renderComments(comments);
    } catch (e) {
        console.error("Failed to fetch comments", e);
    }
}

function renderComments(comments) {
    commentListEl.innerHTML = '';
    comments.forEach(c => {
        const div = document.createElement('div');
        div.className = 'comment-item';
        div.innerHTML = `
            <div class="comment-header">
                <strong>${c.nickname}</strong>
                <span>${new Date(c.created_at).toLocaleString()}</span>
            </div>
            <div class="comment-content">${c.content}</div>
        `;
        commentListEl.appendChild(div);
    });
}

async function postComment(e) {
    e.preventDefault();
    const nickname = document.getElementById('nickname').value;
    const content = document.getElementById('content').value;
    
    if (!nickname || !content) return;
    
    try {
        const res = await fetch(`${API_BASE}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nickname, content })
        });
        
        if (res.ok) {
            document.getElementById('content').value = ''; // Clear content only
            fetchComments();
        }
    } catch (e) {
        console.error("Failed to post comment", e);
    }
}

// Event Listeners
function setupEventListeners() {
    btnPlay.addEventListener('click', togglePlay);
    btnNext.addEventListener('click', nextTrack);
    btnPrev.addEventListener('click', prevTrack);
    
    btnShuffle.addEventListener('click', () => {
        isShuffle = !isShuffle;
        btnShuffle.style.color = isShuffle ? '#1db954' : '#fff';
    });
    
    audioPlayer.addEventListener('ended', nextTrack);
    
    commentForm.addEventListener('submit', postComment);
}

// Start
init();
