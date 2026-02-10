
const API_BASE = '/api';

// State
// DOM Elements
const trackListEl = document.getElementById('track-list');
const audioPlayer = document.getElementById('audio-player');
const npTitle = document.getElementById('np-title');
const npArtist = document.getElementById('np-artist');
const btnPlay = document.getElementById('btn-play');
const btnNext = document.getElementById('btn-next');
const btnPrev = document.getElementById('btn-prev');
const btnShuffle = document.getElementById('btn-shuffle');
const btnRescan = document.getElementById('btn-rescan');
const commentListEl = document.getElementById('comment-list');
const commentForm = document.getElementById('comment-form');

// State
let library = [];
let queue = [];
let currentTrackIndex = -1;
let isShuffle = false;
// Ensure skippedTracks stores strings to avoid type mismatch
let skippedTracks = new Set(
    (JSON.parse(localStorage.getItem('skippedTracks') || '[]')).map(String)
);

// ...

// Initialization
async function init() {
    // Restore Guestbook State
    const isCollapsed = localStorage.getItem('guestbookCollapsed') === 'true';
    if (isCollapsed) {
        const guestbookSection = document.getElementById('guestbook-section');
        const librarySection = document.getElementById('library-section');
        if (guestbookSection) guestbookSection.classList.add('collapsed');
        if (librarySection) librarySection.classList.add('expanded');
    }

    await fetchLibrary();
    await fetchComments();
    setupEventListeners();
}

async function fetchLibrary() {
    try {
        const res = await fetch(`${API_BASE}/library`);
        library = await res.json();
        renderLibrary(searchInput.value);
    } catch (e) {
        console.error("Failed to fetch library", e);
    }
}

// Search Logic
const searchInput = document.getElementById('search-input');

function renderLibrary(filterText = '') {
    trackListEl.innerHTML = '';

    // Filter library
    const filtered = library.filter(track => {
        if (!filterText) return true;
        const term = filterText.toLowerCase();
        return (track.title && track.title.toLowerCase().includes(term)) ||
            (track.artist && track.artist.toLowerCase().includes(term)) ||
            (track.album && track.album.toLowerCase().includes(term));
    });

    filtered.forEach((track) => {
        const li = document.createElement('li');
        li.className = 'track-item';
        li.dataset.id = track.id;

        // Skip Checkbox
        const trackIdStr = String(track.id);
        const isSkipped = skippedTracks.has(trackIdStr);

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'track-checkbox';
        checkbox.checked = !isSkipped; // Checked means "Play", so if skipped, it's unchecked
        checkbox.title = "Uncheck to skip this track";

        checkbox.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent playing when clicking checkbox
        });

        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                skippedTracks.delete(trackIdStr);
            } else {
                skippedTracks.add(trackIdStr);
            }
            localStorage.setItem('skippedTracks', JSON.stringify([...skippedTracks]));
        });

        const trackContent = document.createElement('div');
        trackContent.className = 'track-content';
        trackContent.style.flex = '1';
        trackContent.innerHTML = `
            <div class="track-info">
                <span class="track-title">${track.title}</span>
                <span class="track-artist">${track.artist}</span>
            </div>
            <div class="track-stats" style="font-size: 0.8rem; color: #888;">
                <span title="Plays">▶️ ${track.play_count || 0}</span>
                <span title="Finishes" style="margin-left: 8px;">✅ ${track.finish_count || 0}</span>
            </div>
        `;

        li.appendChild(checkbox);
        li.appendChild(trackContent);

        li.addEventListener('click', (e) => {
            if (e.target !== checkbox) {
                playTrack(track);
            }
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

    // Increment Play Count
    fetch(`${API_BASE}/track/${track.id}/play`, { method: 'POST' }).catch(console.error);
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

    let nextIndex = currentTrackIndex;
    let attempts = 0;
    const maxAttempts = queue.length;

    do {
        if (isShuffle) {
            // For shuffle, simple random might pick a skipped one, so we just retry
            nextIndex = Math.floor(Math.random() * queue.length);
        } else {
            nextIndex = (nextIndex + 1) % queue.length;
        }
        attempts++;
    } while (skippedTracks.has(queue[nextIndex].id) && attempts < maxAttempts);

    // If all tracks are skipped, do nothing or stop
    if (attempts >= maxAttempts && skippedTracks.has(queue[nextIndex].id)) {
        console.log("All tracks skipped or queue empty");
        return;
    }

    currentTrackIndex = nextIndex;
    _loadAndPlay(queue[currentTrackIndex]);
}

function prevTrack() {
    if (queue.length === 0) return;

    if (audioPlayer.currentTime > 3) {
        audioPlayer.currentTime = 0;
        return;
    }

    let prevIndex = currentTrackIndex;
    let attempts = 0;
    const maxAttempts = queue.length;

    do {
        if (isShuffle) {
            prevIndex = Math.floor(Math.random() * queue.length);
        } else {
            prevIndex = (prevIndex - 1 + queue.length) % queue.length;
        }
        attempts++;
    } while (skippedTracks.has(queue[prevIndex].id) && attempts < maxAttempts);

    if (attempts >= maxAttempts && skippedTracks.has(queue[prevIndex].id)) {
        return;
    }

    currentTrackIndex = prevIndex;
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
        if (isShuffle) {
            btnShuffle.classList.add('active');
        } else {
            btnShuffle.classList.remove('active');
        }
    });

    btnRescan.addEventListener('click', async () => {
        btnRescan.disabled = true;
        btnRescan.textContent = "Scanning...";
        try {
            await fetch(`${API_BASE}/library/scan`, { method: 'POST' });
            await fetchLibrary();
        } catch (e) {
            console.error("Scan failed", e);
        } finally {
            btnRescan.disabled = false;
            btnRescan.textContent = "🔄 Rescan";
        }
    });

    searchInput.addEventListener('input', (e) => {
        renderLibrary(e.target.value);
    });

    audioPlayer.addEventListener('ended', () => {
        // Increment Finish Count
        const track = library[currentTrackIndex]; // Note: library/queue management is simple in this MVP
        if (track) {
            fetch(`${API_BASE}/track/${track.id}/finish`, { method: 'POST' }).catch(console.error);
        }
        nextTrack();
    });

    commentForm.addEventListener('submit', postComment);

    const btnRefreshComments = document.getElementById('btn-refresh-comments');
    if (btnRefreshComments) {
        btnRefreshComments.addEventListener('click', () => {
            // Animate button spin
            btnRefreshComments.style.transition = 'transform 0.5s';
            btnRefreshComments.style.transform = 'rotate(360deg)';
            fetchComments().then(() => {
                setTimeout(() => {
                    btnRefreshComments.style.transition = 'none';
                    btnRefreshComments.style.transform = 'rotate(0deg)';
                }, 500);
            });
        });
    }

    const btnToggleGb = document.getElementById('btn-toggle-gb');
    if (btnToggleGb) {
        btnToggleGb.addEventListener('click', () => {
            const guestbookSection = document.getElementById('guestbook-section');
            const librarySection = document.getElementById('library-section');

            guestbookSection.classList.toggle('collapsed');

            const isCollapsed = guestbookSection.classList.contains('collapsed');
            if (librarySection) {
                librarySection.classList.toggle('expanded', isCollapsed); // Sync with collapsed state
            }

            localStorage.setItem('guestbookCollapsed', isCollapsed);

            // Optional: Rotate arrow based on state (handled in CSS mostly, but logic check)
            // CSS handles rotation: .collapsed #btn-toggle-gb -> rotate(-90deg)
        });
    }
}

// Start
init();
