import { useState, useEffect } from 'react'
import { fetchProjects, fetchProjectData, API_BASE } from '../api'

export default function ProjectList({ onSelectProject }) {
    const [projects, setProjects] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        loadProjects()
    }, [])

    const loadProjects = async () => {
        try {
            setLoading(true)
            const data = await fetchProjects()
            setProjects(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const handleSelect = async (slug) => {
        try {
            const data = await fetchProjectData(slug)
            onSelectProject(data)
        } catch (err) {
            alert("Failed to load project: " + err.message)
        }
    }

    if (loading) return <div className="render-status"><div className="spinner" /></div>
    if (error) return <div className="empty-state"><h3>Error</h3><p>{error}</p></div>

    return (
        <div className="project-list-container" style={{ padding: '20px' }}>
            <h2 style={{ marginBottom: '20px' }}>📁 プロジェクト履歴</h2>
            {projects.length === 0 ? (
                <div className="empty-state">
                    <p>プロジェクトが見つかりません。</p>
                </div>
            ) : (
                <div className="project-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    {projects.map(p => (
                        <div key={p.slug} className="project-card" style={{
                            border: '1px solid var(--border)',
                            borderRadius: '8px',
                            padding: '16px',
                            background: 'var(--bg-secondary)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '12px'
                        }}>
                            <h3 style={{ fontSize: '16px', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {p.title}
                            </h3>
                            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                                {new Date(p.created_at).toLocaleString()}
                            </div>

                            {p.has_video && (
                                <div style={{ height: '140px', background: '#000', borderRadius: '4px', overflow: 'hidden' }}>
                                    <video src={p.video_url?.startsWith('http') ? p.video_url : `${API_BASE}${p.video_url}`} width="100%" height="100%" />
                                </div>
                            )}

                            <button
                                className="btn btn-primary"
                                style={{ marginTop: 'auto', padding: '8px' }}
                                onClick={() => handleSelect(p.slug)}
                            >
                                編集を再開する
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
