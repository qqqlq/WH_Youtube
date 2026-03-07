import { useState, useEffect } from 'react'
import { renderVideo, checkRenderStatus, API_BASE } from '../api'

export default function VideoPreview({ script, renderResult, setRenderResult }) {
    const [rendering, setRendering] = useState(false)
    const [error, setError] = useState(null)
    const [engine, setEngine] = useState('voicevox')

    const [pollTimer, setPollTimer] = useState(null)
    const [statusMessage, setStatusMessage] = useState("")

    // 進行中のジョブをポーリングで監視
    const startPolling = (jobId) => {
        const timer = setInterval(async () => {
            try {
                const job = await checkRenderStatus(jobId);
                setStatusMessage(job.message || "処理中...");

                if (job.status === "completed") {
                    clearInterval(timer);
                    setRendering(false);
                    setRenderResult(job.result);
                } else if (job.status === "failed") {
                    clearInterval(timer);
                    setRendering(false);
                    setError(job.message || "動画生成中にエラーが発生しました。");
                }
            } catch (err) {
                console.error("Polling error:", err);
                clearInterval(timer);
                setRendering(false);
                setError("サーバーとの通信が切断されました。");
            }
        }, 3000); // 3秒おき
        setPollTimer(timer);
    };

    const handleRender = async () => {
        if (!script || rendering) return
        setRendering(true)
        setError(null)
        setStatusMessage("準備中...")

        try {
            const startResp = await renderVideo({ ...script, engine })
            // バックグラウンドでジョブが開始されたら、ポーリング開始
            if (startResp.job_id) {
                startPolling(startResp.job_id)
            } else {
                // fallback if instant return
                setRendering(false)
                setRenderResult(startResp)
            }
        } catch (err) {
            setRendering(false)
            setError("ジョブの開始に失敗: " + err.message)
        }
    }

    // クリーンアップ
    useEffect(() => {
        return () => {
            if (pollTimer) clearInterval(pollTimer);
        }
    }, [pollTimer]);

    return (
        <div className="preview-container">
            {/* Render button (if not yet rendered) */}
            {!renderResult && !rendering && (
                <div className="empty-state">
                    <div className="icon">🎬</div>
                    <h3>動画をレンダリング</h3>
                    <p>台本の内容で素材収集→ナレーション→動画生成を実行します。</p>
                    <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 8 }}>
                        通常 2〜5 分かかります。
                    </p>

                    <div style={{ marginTop: 24, marginBottom: 8 }}>
                        <label style={{ marginRight: 12, fontSize: 14, fontWeight: 'bold' }}>🗣️ ナレーター音声:</label>
                        <select
                            value={engine}
                            onChange={(e) => setEngine(e.target.value)}
                            style={{ padding: '8px 12px', borderRadius: 4, border: '1px solid #ccc', fontSize: 14 }}
                        >
                            <option value="voicevox">VOICEVOX (ずんだもん・高品質)</option>
                            <option value="gtts">Google TTS (機械音声・標準)</option>
                        </select>
                    </div>

                    <button
                        className="btn btn-primary"
                        onClick={handleRender}
                        style={{ marginTop: 20, padding: '14px 32px', fontSize: 16 }}
                    >
                        🚀 動画を生成する
                    </button>
                </div>
            )}

            {/* Rendering in progress */}
            {rendering && (
                <div className="render-status">
                    <div className="spinner" />
                    <p>動画を生成中...</p>
                    <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
                        {statusMessage}
                    </p>
                </div>
            )}

            {/* Error */}
            {error && (
                <div className="empty-state">
                    <div className="icon">⚠️</div>
                    <h3>エラーが発生しました</h3>
                    <p style={{ color: 'var(--danger)' }}>{error}</p>
                    <button
                        className="btn btn-secondary"
                        onClick={handleRender}
                        style={{ marginTop: 16 }}
                    >
                        再試行
                    </button>
                </div>
            )}

            {/* Result */}
            {renderResult && (
                <>
                    <div className="video-player-wrap">
                        <video
                            controls
                            src={renderResult.video_url.startsWith('http') ? renderResult.video_url : `${API_BASE}${renderResult.video_url}`}
                            style={{ width: '100%' }}
                        />
                    </div>

                    <div style={{ textAlign: 'center' }}>
                        <a
                            href={renderResult.video_url.startsWith('http') ? renderResult.video_url : `${API_BASE}${renderResult.video_url}`}
                            download
                            className="btn btn-success"
                        >
                            ⬇ ダウンロード
                        </a>
                        <button
                            className="btn btn-secondary"
                            onClick={() => {
                                setRenderResult(null)
                                setError(null)
                            }}
                            style={{ marginLeft: 8 }}
                        >
                            🔄 再生成
                        </button>
                    </div>

                    {/* Source table */}
                    {renderResult.sources && renderResult.sources.length > 0 && (
                        <div style={{ width: '100%' }}>
                            <h3 style={{ fontSize: 15, marginBottom: 8, color: 'var(--text-secondary)' }}>
                                📸 素材ソース
                            </h3>
                            <table className="source-table">
                                <thead>
                                    <tr>
                                        <th>Scene</th>
                                        <th>検索クエリ</th>
                                        <th>提供元</th>
                                        <th>撮影者</th>
                                        <th>ソース</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {renderResult.sources.map((s) => (
                                        <tr key={s.scene_id}>
                                            <td>{s.scene_id}</td>
                                            <td>{s.query}</td>
                                            <td>{s.provider}</td>
                                            <td>{s.photographer}</td>
                                            <td>
                                                {s.source_url ? (
                                                    <a href={s.source_url} target="_blank" rel="noreferrer">
                                                        Link
                                                    </a>
                                                ) : (
                                                    '—'
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
