import { useState, useEffect } from "react"
import "./App.css"

const API = "https://fantastic-beasts.onrender.com"

function BeastCard({ beast, onClick }) {
  return (
    <div className="beast-card" onClick={() => onClick(beast)}>
      <div className="card-image">
        {beast.image ? (
          <img src={`${API}/${beast.image}`} alt={beast.name} />
        ) : (
          <div className="no-image">🐉</div>
        )}
      </div>
      <div className="card-body">
        <h3>{beast.name}</h3>
        <p className="card-source">{beast.source}</p>
        <p className="card-comment">{beast.comment}</p>
      </div>
    </div>
  )
}

function DetailModal({ beast, onClose }) {
  if (!beast) return null
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>✕</button>
        <div className="modal-content">
          <div className="modal-image">
            {beast.image ? (
              <img src={`${API}/${beast.image}`} alt={beast.name} />
            ) : (
              <div className="no-image large">🐉</div>
            )}
          </div>
          <div className="modal-info">
            <h2>{beast.name}</h2>
            <p className="modal-source">출처: {beast.source}</p>
            {beast.original && (
              <p className="modal-original">원문: {beast.original}</p>
            )}
            {beast.animals?.length > 0 && (
              <p className="modal-animals">
                구성 동물: {beast.animals.join(", ")}
              </p>
            )}
            <p className="modal-translated">{beast.translated}</p>
            {beast.comment && (
              <p className="modal-comment">💬 {beast.comment}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [beasts, setBeasts] = useState([])
  const [query, setQuery] = useState("")
  const [answer, setAnswer] = useState("")
  const [results, setResults] = useState(null)
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetch(`${API}/beasts`)
      .then((r) => r.json())
      .then((data) => setBeasts(data.beasts))
      .catch(() => console.error("서버에 연결할 수 없습니다."))
  }, [])

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setAnswer("")
    setResults(null)
    try {
      const res = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 4 }),
      })
      const data = await res.json()
      setAnswer(data.answer)
      setResults(data.sources)
    } catch {
      setAnswer("서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인하세요.")
    }
    setLoading(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSearch()
  }

  const handleReset = () => {
    setQuery("")
    setAnswer("")
    setResults(null)
  }

  const displayBeasts = results ?? beasts

  return (
    <div className="app">
      <header className="header">
        <h1 onClick={handleReset} style={{ cursor: "pointer" }}>
          🐲 신비한 동물사전
        </h1>
        <p className="subtitle">산해경과 동아시아 신화 속 신비한 동물들</p>
        <div className="search-bar">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="예: 날개 달린 동물, 불을 다루는 신수, 봉황이 뭐야?"
          />
          <button onClick={handleSearch} disabled={loading}>
            {loading ? "검색 중..." : "검색"}
          </button>
        </div>
      </header>

      {answer && (
        <div className="answer-box">
          <p>{answer}</p>
        </div>
      )}

      <main className="grid-container">
        <p className="grid-label">
          {results ? `관련 동물 ${results.length}개` : `전체 ${beasts.length}개`}
        </p>
        <div className="beast-grid">
          {displayBeasts.map((beast) => (
            <BeastCard key={beast.id} beast={beast} onClick={setSelected} />
          ))}
        </div>
      </main>

      <DetailModal beast={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
