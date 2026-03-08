import { useState, useRef } from 'react'
import { uploadImage, API_BASE } from '../api'

export default function ScriptEditor({ script, setScript, onConfirm }) {
    const fileInputRefs = useRef({})
    const [uploading, setUploading] = useState({}) // track logic per scene.id
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

    const handleUpload = async (sceneIndex, file) => {
        if (!file) return
        const scene = script.scenes[sceneIndex]

        try {
            setUploading(prev => ({ ...prev, [scene.id]: true }))
            const result = await uploadImage(script.title, scene.id, file)
            updateScene(sceneIndex, 'manual_image_url', result.url)
        } catch (err) {
            alert("画像アップロードに失敗しました: " + err.message)
        } finally {
            setUploading(prev => ({ ...prev, [scene.id]: false }))
        }
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
                <div>
                    <input
                        className="script-title-input"
                        value={script.title}
                        onChange={(e) => updateTitle(e.target.value)}
                        placeholder="動画タイトル"
                        style={{ display: 'block', marginBottom: '8px', width: '300px' }}
                    />
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>🎵 BGM:</span>
                        <select
                            className="field-input"
                            style={{ width: '150px', padding: '4px 8px' }}
                            value={script.bgm_keyword || 'lofi'}
                            onChange={(e) => setScript({ ...script, bgm_keyword: e.target.value })}
                        >
                            <option value="lofi">lofi (ゆったり)</option>
                            <option value="cinematic">cinematic (映画風)</option>
                            <option value="cyberpunk">cyberpunk (近未来)</option>
                            <option value="upbeat">upbeat (明るい)</option>
                            <option value="horror">horror (ホラー)</option>
                            <option value="comical">comical (コミカル)</option>
                        </select>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
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
                                <label className="field-label" style={{ color: 'var(--primary)' }}>✨ 高画質AI画像用プロンプト (英語)</label>
                                <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px', marginTop: '-4px' }}>
                                    Midjourney等で綺麗な画像を生成するのにお使いください。
                                </p>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                                    <textarea
                                        className="field-input"
                                        rows={2}
                                        value={scene.image_prompt_en || ''}
                                        onChange={(e) => updateScene(i, 'image_prompt_en', e.target.value)}
                                        placeholder="Detailed English prompt for high-quality AI images"
                                        style={{ flex: 1, fontSize: '12px', lineHeight: '1.4' }}
                                    />
                                    <button
                                        className="btn btn-secondary"
                                        style={{ padding: '8px 12px', fontSize: '13px', whiteSpace: 'nowrap', height: 'fit-content' }}
                                        onClick={() => {
                                            navigator.clipboard.writeText(scene.image_prompt_en || '')
                                            alert('プロンプトをコピーしました！画像生成AIに貼り付けてください。')
                                        }}
                                        title="プロンプトをコピー"
                                    >
                                        📋 コピー
                                    </button>
                                </div>

                                <div style={{ marginTop: '12px', padding: '12px', border: '1px dashed var(--border)', borderRadius: '4px', background: 'var(--bg-secondary)' }}>
                                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', fontWeight: 'bold' }}>
                                        🎨 差し替え用画像のアップロード (任意)
                                    </label>
                                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                                        他のAIで生成した画像や自前の写真をここでアップロードすると、自動検索（検索クエリ）より優先して動画に使われます。
                                    </p>
                                    <input
                                        type="file"
                                        accept="image/*"
                                        style={{ display: 'none' }}
                                        ref={el => fileInputRefs.current[scene.id] = el}
                                        onChange={(e) => handleUpload(i, e.target.files[0])}
                                    />
                                    <button
                                        className="btn btn-secondary"
                                        style={{ fontSize: '13px', padding: '6px 12px' }}
                                        onClick={() => fileInputRefs.current[scene.id]?.click()}
                                        disabled={uploading[scene.id]}
                                    >
                                        {uploading[scene.id] ? 'アップロード中...' : '📂 画像を選択してアップロード'}
                                    </button>

                                    {scene.manual_image_url && (
                                        <div style={{ marginTop: '12px', position: 'relative', display: 'inline-block' }}>
                                            <img
                                                src={scene.manual_image_url.startsWith('http') ? scene.manual_image_url : `${API_BASE}${scene.manual_image_url}`}
                                                alt="Uploaded preview"
                                                style={{ height: '100px', borderRadius: '4px', objectFit: 'cover', border: '2px solid var(--primary)' }}
                                            />
                                            <button
                                                className="btn btn-icon"
                                                onClick={() => updateScene(i, 'manual_image_url', '')}
                                                style={{
                                                    position: 'absolute', top: '-8px', right: '-8px',
                                                    background: 'var(--danger)', color: 'white',
                                                    borderRadius: '50%', width: '24px', height: '24px',
                                                    fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center'
                                                }}
                                                title="画像を未設定に戻す"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                            <div className="field-group">
                                <label className="field-label">🗣 ナレーション</label>
                                <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                                    <select
                                        className="field-input"
                                        style={{ width: 'auto', flex: 'none' }}
                                        value={scene.character || 'zundamon'}
                                        onChange={(e) => updateScene(i, 'character', e.target.value)}
                                    >
                                        <option value="zundamon">ずんだもん (ノーマル)</option>
                                        <option value="metan">四国めたん (ノーマル)</option>
                                        <option value="tsumugi">春日部つむぎ (ノーマル)</option>
                                    </select>
                                    <select
                                        className="field-input"
                                        style={{ width: '120px', flex: 'none' }}
                                        value={scene.sound_effect || ''}
                                        onChange={(e) => updateScene(i, 'sound_effect', e.target.value)}
                                        title="効果音(SE)"
                                    >
                                        <option value="">(なし)</option>
                                        <option value="pop">pop (ポンッ)</option>
                                        <option value="whoosh">whoosh (シュッ)</option>
                                        <option value="impact">impact (ドーン！)</option>
                                        <option value="chime">chime (チーン)</option>
                                        <option value="drumroll">drumroll (ドラム)</option>
                                        <option value="glitch">glitch (グリッチ)</option>
                                        <option value="sword">sword (シャキン)</option>
                                    </select>
                                </div>
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
