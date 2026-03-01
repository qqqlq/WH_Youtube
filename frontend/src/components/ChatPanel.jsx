import { useState, useRef, useEffect } from 'react'
import { sendChat, generateScript } from '../api'

export default function ChatPanel({ messages, setMessages, onScriptGenerated }) {
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [generating, setGenerating] = useState(false)
    const bottomRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSend = async () => {
        const text = input.trim()
        if (!text || loading) return

        const newMessages = [...messages, { role: 'user', content: text }]
        setMessages(newMessages)
        setInput('')
        setLoading(true)

        try {
            const data = await sendChat(newMessages)
            setMessages([...newMessages, { role: 'model', content: data.reply }])
        } catch (err) {
            setMessages([
                ...newMessages,
                { role: 'model', content: `⚠ エラー: ${err.message}` },
            ])
        } finally {
            setLoading(false)
        }
    }

    const handleGenerateScript = async () => {
        if (generating) return
        setGenerating(true)

        // Build context from conversation
        const context = messages.map((m) => `${m.role}: ${m.content}`).join('\n')
        const lastUserMsg =
            [...messages].reverse().find((m) => m.role === 'user')?.content || ''

        try {
            const script = await generateScript(lastUserMsg, context)
            onScriptGenerated(script)
        } catch (err) {
            setMessages([
                ...messages,
                { role: 'model', content: `⚠ 台本生成エラー: ${err.message}` },
            ])
        } finally {
            setGenerating(false)
        }
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="chat-container">
            {/* Messages */}
            <div className="chat-messages">
                {messages.length === 0 && (
                    <div className="empty-state">
                        <div className="icon">💬</div>
                        <h3>企画を始めましょう</h3>
                        <p>
                            「雪国をネットミームで解説する動画」などのアイデアを
                            <br />
                            Gemini と一緒に練り上げましょう。
                        </p>
                    </div>
                )}
                {messages.map((msg, i) => (
                    <div key={i} className={`chat-msg ${msg.role}`}>
                        <div className="chat-avatar">
                            {msg.role === 'user' ? '👤' : '🤖'}
                        </div>
                        <div className="chat-bubble">{msg.content}</div>
                    </div>
                ))}
                {loading && (
                    <div className="chat-msg model">
                        <div className="chat-avatar">🤖</div>
                        <div className="chat-bubble">考え中...</div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="chat-input-row">
                <textarea
                    className="chat-input"
                    rows={2}
                    placeholder="企画のアイデアを入力... (Enter で送信、Shift+Enter で改行)"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={loading}
                />
                <button
                    className="btn btn-primary btn-icon"
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                    title="送信"
                >
                    ▶
                </button>
            </div>

            {/* Actions */}
            <div className="chat-actions">
                <button
                    className="btn btn-success"
                    onClick={handleGenerateScript}
                    disabled={generating || messages.length === 0}
                >
                    {generating ? '生成中...' : '📝 台本を生成'}
                </button>
            </div>
        </div>
    )
}
