export default function ScriptEditor({ script, setScript, onConfirm }) {
    if (!script) {
        return (
            <div className="empty-state">
                <div className="icon">📋</div>
                <h3>台本がまだありません</h3>
                <p>ステップ1でチャットから台本を生成してください。</p>
            </div>
        )
    }

    const updateTitle = (value) => {
        setScript({ ...script, title: value })
    }

    const updateScene = (index, field, value) => {
        const updated = [...script.scenes]
        updated[index] = { ...updated[index], [field]: value }
        setScript({ ...script, scenes: updated })
    }

    const addScene = () => {
        const newId =
            script.scenes.length > 0
                ? Math.max(...script.scenes.map((s) => s.id)) + 1
                : 1
        setScript({
            ...script,
            scenes: [
                ...script.scenes,
                {
                    id: newId,
                    duration: 5,
                    narration: '',
                    visual_query: '',
                    overlay_text: '',
                },
            ],
        })
    }

    const removeScene = (index) => {
        const updated = script.scenes.filter((_, i) => i !== index)
        setScript({ ...script, scenes: updated })
    }

    return (
        <div>
            {/* Header */}
            <div className="script-header">
                <input
                    className="script-title-input"
                    value={script.title}
                    onChange={(e) => updateTitle(e.target.value)}
                    placeholder="動画タイトル"
                />
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-secondary" onClick={addScene}>
                        ＋ シーン追加
                    </button>
                    <button className="btn btn-success" onClick={onConfirm}>
                        ✓ 確定して次へ
                    </button>
                </div>
            </div>

            {/* Scene list */}
            <div className="scene-list">
                {script.scenes.map((scene, i) => (
                    <div key={scene.id} className="scene-card">
                        <div className="scene-card-header">
                            <span className="scene-badge">
                                🎬 Scene {scene.id}
                            </span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                <div className="scene-duration">
                                    ⏱
                                    <input
                                        type="number"
                                        min={1}
                                        max={30}
                                        value={scene.duration}
                                        onChange={(e) =>
                                            updateScene(i, 'duration', parseInt(e.target.value) || 5)
                                        }
                                    />
                                    秒
                                </div>
                                <button
                                    className="btn btn-secondary btn-icon"
                                    onClick={() => removeScene(i)}
                                    title="削除"
                                    style={{ padding: '4px 8px', fontSize: 12 }}
                                >
                                    ✕
                                </button>
                            </div>
                        </div>

                        <div className="scene-fields">
                            <div className="field-group">
                                <label className="field-label">🔍 画像検索クエリ (英語)</label>
                                <input
                                    className="field-input"
                                    value={scene.visual_query}
                                    onChange={(e) => updateScene(i, 'visual_query', e.target.value)}
                                    placeholder="e.g. snowy village japan winter"
                                />
                            </div>
                            <div className="field-group">
                                <label className="field-label">🗣 ナレーション</label>
                                <textarea
                                    className="field-input"
                                    rows={2}
                                    value={scene.narration}
                                    onChange={(e) => updateScene(i, 'narration', e.target.value)}
                                    placeholder="このシーンで読み上げるテキスト"
                                />
                            </div>
                            <div className="field-group">
                                <label className="field-label">💬 テロップ</label>
                                <input
                                    className="field-input"
                                    value={scene.overlay_text}
                                    onChange={(e) => updateScene(i, 'overlay_text', e.target.value)}
                                    placeholder="画面に表示する短いテキスト"
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
