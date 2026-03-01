const API_BASE = '';  // Vite proxy handles /api → localhost:8000

export async function sendChat(messages) {
    const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function generateScript(topic, context = '') {
    const res = await fetch(`${API_BASE}/api/generate_script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, context }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function renderVideo(scriptData) {
    const res = await fetch(`${API_BASE}/api/render_video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scriptData),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}
