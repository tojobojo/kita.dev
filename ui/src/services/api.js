/**
 * Kita.dev API Service
 * Centralized API client with error handling and configuration
 */

// API base URL - configurable via environment
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    };

    // Add API key if available
    const apiKey = import.meta.env.VITE_API_KEY;
    if (apiKey) {
        config.headers['X-API-Key'] = apiKey;
    }

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

// ============ Agent API ============

export async function submitTask(task, repoPath) {
    return apiFetch('/agent/run', {
        method: 'POST',
        body: JSON.stringify({ task, repo_path: repoPath }),
    });
}

export async function getJobStatus(jobId) {
    return apiFetch(`/agent/status/${jobId}`);
}

// ============ Dashboard API ============

export async function getHealth() {
    return apiFetch('/api/health');
}

export async function getTasks(limit = 50) {
    return apiFetch(`/api/tasks?limit=${limit}`);
}

export async function getMetrics() {
    return apiFetch('/api/metrics');
}

export async function getConfig() {
    return apiFetch('/api/config');
}

export async function updateConfig(key, value) {
    return apiFetch('/api/config', {
        method: 'PUT',
        body: JSON.stringify({ key, value }),
    });
}

// ============ Utilities ============

export function formatDate(isoString) {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleString();
}

export function formatDuration(seconds) {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

export function getStateColor(state) {
    const colors = {
        COMPLETED: 'var(--success-color)',
        STOPPED_SAFE: 'var(--warning-color)',
        STOPPED_ERROR: 'var(--error-color)',
        TESTS_PASSED: 'var(--success-color)',
        TESTS_FAILED: 'var(--error-color)',
        IDLE: 'var(--text-secondary)',
    };
    return colors[state] || 'var(--accent-color)';
}

// ============ WebSocket (for real-time updates) ============

export function createTaskWebSocket(jobId, onMessage, onError) {
    const wsUrl = import.meta.env.VITE_WS_URL ||
        `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;

    const ws = new WebSocket(`${wsUrl}/ws/task/${jobId}`);

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            onMessage(data);
        } catch (e) {
            console.error('WebSocket parse error:', e);
        }
    };

    ws.onerror = onError;

    return ws;
}
