import { useState } from 'react'
import ChatPanel from './components/ChatPanel'
import ScriptEditor from './components/ScriptEditor'
import VideoPreview from './components/VideoPreview'
import ProjectList from './components/ProjectList'

const STEPS = [
    { id: 1, label: '企画' },
    { id: 2, label: '台本編集' },
    { id: 3, label: 'プレビュー' },
]

export default function App() {
    const [viewMode, setViewMode] = useState('wizard') // 'wizard' or 'history'
    const [step, setStep] = useState(1)
    const [chatMessages, setChatMessages] = useState([])
    const [script, setScript] = useState(null)
    const [renderResult, setRenderResult] = useState(null)

    const stepState = (id) => {
        if (id === step) return 'active'
        if (id < step) return 'completed'
        return ''
    }

    return (
        <div className="app">
            {/* Header */}
            <header className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1>AVAP</h1>
                    <span className="version">Video Automation Pipeline v0.4</span>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                        className={`btn ${viewMode === 'wizard' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setViewMode('wizard')}
                        style={{ padding: '6px 16px' }}
                    >
                        ＋ 新規作成
                    </button>
                    <button
                        className={`btn ${viewMode === 'history' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setViewMode('history')}
                        style={{ padding: '6px 16px' }}
                    >
                        📂 履歴
                    </button>
                </div>
            </header>

            {/* Content */}
            <div className="main-content">
                {viewMode === 'history' ? (
                    <ProjectList onSelectProject={(loadedScript) => {
                        setScript(loadedScript)
                        if (loadedScript.video_url) {
                            setRenderResult({ video_url: loadedScript.video_url })
                            setStep(3)
                        } else {
                            setRenderResult(null)
                            setStep(2)
                        }
                        setViewMode('wizard')
                    }} />
                ) : (
                    <>
                        {/* Stepper only in wizard mode */}
                        <nav className="stepper">
                            {STEPS.map((s) => (
                                <button
                                    key={s.id}
                                    className={`step-btn ${stepState(s.id)}`}
                                    onClick={() => {
                                        // Can go back freely, forward only if data exists
                                        if (s.id <= step || (s.id === 2 && script) || (s.id === 3 && script)) {
                                            setStep(s.id)
                                        }
                                    }}
                                >
                                    <span className="step-num">
                                        {stepState(s.id) === 'completed' ? '✓' : s.id}
                                    </span>
                                    {s.label}
                                </button>
                            ))}
                        </nav>

                        {step === 1 && (
                            <ChatPanel
                                messages={chatMessages}
                                setMessages={setChatMessages}
                                onScriptGenerated={(s) => {
                                    setScript(s)
                                    setStep(2)
                                }}
                            />
                        )}
                        {step === 2 && (
                            <ScriptEditor
                                script={script}
                                setScript={setScript}
                                onConfirm={() => setStep(3)}
                            />
                        )}
                        {step === 3 && (
                            <VideoPreview
                                script={script}
                                renderResult={renderResult}
                                setRenderResult={setRenderResult}
                            />
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
