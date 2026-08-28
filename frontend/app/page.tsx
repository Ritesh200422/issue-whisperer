"use client";

import { useEffect, useState } from "react";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type HealthResponse = {
  status: string;
  app: string;
  version: string;
};

type Candidate = {
  number: number;
  title: string;
  body: string;
  labels: string[];
  state: string;
  similarity_score: number;
};

type Triage = {
  label: string;
  is_duplicate: boolean;
  duplicate_of: number | null;
  confidence: number;
  evidence_quote: string | null;
  draft_reply: string;
};

type Verification = {
  status: string;
  reason: string;
  evidence_quote: string | null;
};

type AnalysisResult = {
  label: string;
  is_duplicate: boolean;
  duplicate_of: number | null;
  confidence: number;
  evidence_quote: string | null;
  draft_reply: string;
  retrieved_candidates: Candidate[];
  triage: Triage;
  verification: Verification;
};

type ConnectionState = "connecting" | "connected" | "error";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [state, setState] = useState<ConnectionState>("connecting");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Input states
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  // Approval simulation state
  const [editedReply, setEditedReply] = useState("");
  const [isResolving, setIsResolving] = useState(false);
  const [simulatedLogs, setSimulatedLogs] = useState<string[]>([]);
  const [showLogs, setShowLogs] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/health`, {
          signal: AbortSignal.timeout(3000),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: HealthResponse = await res.json();
        setHealth(data);
        setState("connected");
        setErrorMsg(null);
      } catch (err) {
        setState("error");
        setErrorMsg(err instanceof Error ? err.message : "Unknown error");
        setHealth(null);
      }
    };

    check();
    const interval = setInterval(check, 15_000);
    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title) return;
    setIsAnalyzing(true);
    setResult(null);
    setSimulatedLogs([]);
    setShowLogs(false);

    try {
      const res = await fetch(`${BACKEND_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, body }),
      });
      if (!res.ok) throw new Error(`Analysis failed with status ${res.status}`);
      const data: AnalysisResult = await res.json();
      setResult(data);
      setEditedReply(data.draft_reply);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error analyzing issue");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleApprovalAction = async (action: "approve" | "reject" | "edit") => {
    if (!result) return;
    setIsResolving(true);
    try {
      const res = await fetch(`${BACKEND_URL}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          issue_number: 999, // New simulated issue number
          action,
          suggested_label: result.label,
          duplicate_of: result.duplicate_of,
          edited_reply: action === "reject" ? undefined : editedReply,
        }),
      });
      if (!res.ok) throw new Error("Approval resolution failed");
      const data = await res.json();
      setSimulatedLogs(data.simulated_actions);
      setShowLogs(true);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error resolving action");
    } finally {
      setIsResolving(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-800 pb-6">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight">
              <span className="text-white">ISSUE</span>
              <span className="text-blue-500"> WHISPERER</span>
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              AI Duplicate GitHub Issue Detection & Independent verification
            </p>
          </div>

          <div className="flex items-center gap-3 bg-gray-900 border border-gray-850 px-4 py-2 rounded-lg">
            <div className={`w-2.5 h-2.5 rounded-full ${state === "connected" ? "bg-green-400" : state === "connecting" ? "bg-yellow-400 animate-pulse" : "bg-red-500"}`} />
            <span className="text-xs font-semibold text-gray-300">
              {state === "connected" ? `Connected: ${health?.app} v${health?.version}` : state === "connecting" ? "Reconnecting..." : "Disconnected"}
            </span>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Form Input */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-md">
              <h2 className="text-lg font-bold text-white mb-4">Paste New Issue</h2>
              <form onSubmit={handleAnalyze} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">Issue Title</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Memory leak during CSV file parse"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-gray-100 placeholder-gray-600 focus:outline-none focus:border-blue-500 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">Issue Body</label>
                  <textarea
                    rows={8}
                    placeholder="Provide full issue details, logs, or reproduction steps..."
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-gray-100 placeholder-gray-600 focus:outline-none focus:border-blue-500 text-sm font-mono"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isAnalyzing || !title}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg disabled:opacity-50 transition duration-200 text-sm flex items-center justify-center gap-2"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    "Run Duplicate Analysis"
                  )}
                </button>
              </form>
            </div>
            
            {/* Quick Demo Pre-sets */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">Load Demo Scenarios</h3>
              <div className="space-y-2">
                <button
                  onClick={() => {
                    setTitle("Application crashes when uploading files larger than 100MB");
                    setBody("Steps to reproduce:\n1. Open UI\n2. Select 150MB file\n3. Click upload\n4. Server responds with 500 error.");
                  }}
                  className="w-full text-left bg-gray-950 hover:bg-gray-850 border border-gray-800 rounded-lg p-3 text-xs text-gray-300 transition duration-150"
                >
                  <span className="font-semibold text-red-400 block mb-1">Scenario A: Duplicate Issue</span>
                  Crashes when file size exceeds 100MB during file upload.
                </button>

                <button
                  onClick={() => {
                    setTitle("Configure custom port settings in production config");
                    setBody("I want to run the FastAPI app on port 8080 instead of 8000. How can I pass the environment configuration?");
                  }}
                  className="w-full text-left bg-gray-950 hover:bg-gray-850 border border-gray-800 rounded-lg p-3 text-xs text-gray-300 transition duration-150"
                >
                  <span className="font-semibold text-green-400 block mb-1">Scenario B: Distinct Issue (Question)</span>
                  Asks for instructions regarding custom server ports.
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Results & Agent Chain Display */}
          <div className="lg:col-span-7 space-y-6">
            {!result && !isAnalyzing && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center h-full flex flex-col justify-center items-center">
                <div className="text-4xl mb-4">🔍</div>
                <h2 className="text-lg font-bold text-white mb-2">No Analysis Loaded</h2>
                <p className="text-gray-500 text-sm max-w-sm">
                  Paste a new issue and click analyze to run retrieval, triage reasoning, and independent evidence verification.
                </p>
              </div>
            )}

            {isAnalyzing && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center h-full flex flex-col justify-center items-center space-y-4">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <h3 className="text-lg font-bold text-white">Agent Pipeline Running</h3>
                <p className="text-gray-500 text-xs max-w-sm leading-relaxed">
                  1. Retrieving Top-K similar issues via local FAISS.<br />
                  2. Analyzing context with Triage Agent.<br />
                  3. Verifying claims independently with Verifier Agent.
                </p>
              </div>
            )}

            {result && (
              <div className="space-y-6">
                
                {/* 1. Retrieval Section */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">1. FAISS Retrieval (Top-3 Similar Issues)</h3>
                  {result.retrieved_candidates.length === 0 ? (
                    <div className="text-sm text-gray-500 italic">No candidates retrieved above similarity threshold.</div>
                  ) : (
                    <div className="space-y-2">
                      {result.retrieved_candidates.map((c) => (
                        <div key={c.number} className="bg-gray-950 border border-gray-850 p-3 rounded-lg text-xs flex justify-between items-center">
                          <div>
                            <span className="font-mono text-blue-400 mr-2">#{c.number}</span>
                            <span className="text-gray-200 font-semibold">{c.title}</span>
                          </div>
                          <span className="bg-blue-950/50 text-blue-400 border border-blue-900 font-mono px-2 py-0.5 rounded text-[10px]">
                            Similarity: {(c.similarity_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 2. Triage & Verification Result Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Triage Decision */}
                  <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">2. Triage Agent Result</h3>
                    <div>
                      <span className="text-xs text-gray-500 block mb-1">Suggested Label</span>
                      <span className="bg-gray-800 text-gray-300 border border-gray-700 px-2 py-0.5 rounded text-xs font-mono">
                        {result.triage.label}
                      </span>
                    </div>

                    <div>
                      <span className="text-xs text-gray-500 block mb-1">Duplicate Claim</span>
                      <span className={`text-xs font-semibold ${result.triage.is_duplicate ? "text-red-400" : "text-green-400"}`}>
                        {result.triage.is_duplicate ? `Duplicate of #${result.triage.duplicate_of}` : "No Duplicate Found"}
                      </span>
                    </div>

                    <div>
                      <span className="text-xs text-gray-500 block mb-1">Triage Confidence</span>
                      <div className="flex items-center gap-2 mt-1">
                        <div className="w-full bg-gray-800 rounded-full h-1.5 max-w-[100px]">
                          <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${result.triage.confidence * 100}%` }} />
                        </div>
                        <span className="text-xs font-mono font-semibold text-gray-300">{(result.triage.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>

                  {/* Independent Verification */}
                  <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">3. Independent Verifier</h3>
                    <div>
                      <span className="text-xs text-gray-500 block mb-1">Status Verification</span>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        result.verification.status === "confirmed" 
                          ? "bg-green-950/60 text-green-400 border border-green-900" 
                          : result.verification.status === "possibly_related" 
                          ? "bg-yellow-950/60 text-yellow-400 border border-yellow-900" 
                          : "bg-red-950/60 text-red-400 border border-red-900"
                      }`}>
                        {result.verification.status.toUpperCase()}
                      </span>
                    </div>

                    <div>
                      <span className="text-xs text-gray-500 block mb-1">Verifier Reasoning</span>
                      <p className="text-xs text-gray-400 leading-relaxed italic">
                        "{result.verification.reason}"
                      </p>
                    </div>
                  </div>
                </div>

                {/* 3. Evidence Validation */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-3">
                  <div className="flex justify-between items-center">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">4. Literal Evidence Quote Verification</h3>
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${result.evidence_quote ? "bg-green-950 text-green-400 border border-green-900" : "bg-gray-800 text-gray-500"}`}>
                      {result.evidence_quote ? "Programmatically Verified" : "No Verified Evidence"}
                    </span>
                  </div>
                  <div className="bg-gray-950 border border-gray-850 p-4 rounded-lg text-xs leading-relaxed font-mono">
                    {result.evidence_quote ? (
                      <span className="text-green-300">"{result.evidence_quote}"</span>
                    ) : (
                      <span className="text-gray-500 italic">No exact literal duplicate quote validated in target candidate text.</span>
                    )}
                  </div>
                </div>

                {/* 4. Human Approval Layer */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">5. Human Approval Layer</h3>
                  
                  <div>
                    <label className="block text-xs text-gray-400 font-semibold mb-2">Draft Reply Comment</label>
                    <textarea
                      rows={4}
                      value={editedReply}
                      onChange={(e) => setEditedReply(e.target.value)}
                      className="w-full bg-gray-950 border border-gray-850 rounded-lg p-3 text-xs text-gray-200 focus:outline-none focus:border-blue-500 font-mono"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleApprovalAction("approve")}
                      disabled={isResolving}
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 rounded-lg transition text-xs"
                    >
                      Approve & Run
                    </button>
                    <button
                      onClick={() => handleApprovalAction("edit")}
                      disabled={isResolving}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition text-xs"
                    >
                      Edit Action
                    </button>
                    <button
                      onClick={() => handleApprovalAction("reject")}
                      disabled={isResolving}
                      className="flex-1 bg-gray-800 hover:bg-gray-750 text-gray-300 font-medium py-2 rounded-lg transition text-xs"
                    >
                      Reject Action
                    </button>
                  </div>
                </div>

                {/* Simulated Logs Output */}
                {showLogs && (
                  <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-3">
                    <h3 className="text-xs font-semibold text-yellow-400 uppercase tracking-widest">Simulated GitHub Write Actions</h3>
                    <div className="space-y-1.5">
                      {simulatedLogs.map((log, idx) => (
                        <div key={idx} className="text-xs font-mono text-gray-400 flex items-center gap-2">
                          <span className="text-blue-500 font-bold">❯</span>
                          <span>{log}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
              </div>
            )}
          </div>

        </div>
      </div>
    </main>
  );
}
