"use client";

import { useState, useEffect } from "react";

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

export default function Home() {
  const [videoUrl, setVideoUrl] = useState("");
  const [persona, setPersona] = useState("");
  const [slideCount, setSlideCount] = useState<number>(5);
  const [colourScheme, setColourScheme] = useState("Yellow and Green");
  const [vibe, setVibe] = useState("modern");

  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("SYSTEM_READY");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [pendingAiConsent, setPendingAiConsent] = useState(false);
  const [consentToken, setConsentToken] = useState<string | null>(null);

  const [sparkles, setSparkles] = useState<
    { id: number; top: string; left: string; size: number; delay: string; duration: string }[]
  >([]);

  useEffect(() => {
    const generatedSparkles = Array.from({ length: 45 }).map((_, i) => ({
      id: i,
      top: `${Math.random() * 100}%`,
      left: `${Math.random() * 100}%`,
      size: Math.random() * 3 + 1,
      delay: `${Math.random() * 5}s`,
      duration: `${Math.random() * 3 + 3}s`,
    }));
    setSparkles(generatedSparkles);
  }, []);

  const handleGenerate = async (e: React.FormEvent | React.MouseEvent<HTMLButtonElement>, approvedToken: string | null = null) => {
    e.preventDefault();
    if (!videoUrl) return;
    setPendingAiConsent(false);

    setLoading(true);
    setError("");
    setResult(null);
    setProgress(15);
    setStatusMessage("EXTRACTING_YOUTUBE_TRANSCRIPT...");

    try {
      // Step 1: Fetch the transcript through the backend service
      const tsResponse = await fetch(`${API_BASE_URL}/transcript`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_url: videoUrl, consent_token: approvedToken }),
      });

      const tsData = await tsResponse.json();

      if (!tsResponse.ok) {
        throw new Error(tsData.detail || tsData.error || "Could not read YouTube captions.");
      }

      if (tsData.status === "ai_consent_required") {
        setConsentToken(tsData.consent_token);
        setPendingAiConsent(true);
        setStatusMessage("AI_TRANSCRIPTION_CONSENT_REQUIRED");
        setProgress(0);
        return;
      }

      if (tsData.status === "generation_in_progress") {
        throw new Error(tsData.message || "Transcript generation is already in progress. Please retry shortly.");
      }

      setConsentToken(null);
      setProgress(45);
      setStatusMessage(`TRANSCRIPT_READY_${(tsData.language || "unknown").toUpperCase()}...`);

      // Step 2: Send transcript text directly to FastAPI backend
      const response = await fetch(`${API_BASE_URL}/generate-carousel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transcript_text: tsData.text,
          persona: persona,
          slide_count: Number(slideCount),
          colour_scheme: colourScheme,
          vibe: vibe,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Agent generation failed.");
      }

      setProgress(100);
      setStatusMessage("ORCHESTRATION_COMPLETE");
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to generate carousel.");
      setStatusMessage("ERROR_ABORTED");
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#070b10] text-slate-100 flex flex-col items-center justify-start p-6 md:p-12 relative overflow-hidden font-sans">
      <style
        dangerouslySetInnerHTML={{
          __html: `
        @keyframes float-sparkle {
          0% { transform: translateY(0px); opacity: 0; }
          50% { opacity: 0.8; }
          100% { transform: translateY(-25px); opacity: 0; }
        }
        .sparkle-dot {
          animation-name: float-sparkle;
          animation-iteration-count: infinite;
          animation-timing-function: ease-in-out;
        }
      `,
        }}
      />

      {/* Floating Sparkles */}
      <div className="absolute inset-0 pointer-events-none z-0">
        {sparkles.map((s) => (
          <div
            key={s.id}
            className="absolute rounded-full bg-cyan-400 sparkle-dot shadow-[0_0_8px_rgba(34,211,238,0.8)]"
            style={{
              top: s.top,
              left: s.left,
              width: `${s.size}px`,
              height: `${s.size}px`,
              animationDelay: s.delay,
              animationDuration: s.duration,
            }}
          />
        ))}
      </div>

      {/* Background Ambient Glows */}
      <div className="absolute top-[-150px] left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-cyan-500/10 blur-[140px] pointer-events-none rounded-full z-0" />
      <div className="absolute bottom-[-100px] right-[-100px] w-[500px] h-[500px] bg-blue-600/10 blur-[160px] pointer-events-none rounded-full z-0" />

      {/* Header Bar */}
      <header className="w-full max-w-2xl mb-8 flex flex-col items-start space-y-1 relative z-10">
        <div className="flex items-center space-x-2">
          <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
          <h2 className="text-sm tracking-widest font-black uppercase text-slate-300">
            Clip2Carousel
          </h2>
        </div>
        <p className="text-[10px] tracking-[0.25em] font-mono text-cyan-400 uppercase font-semibold">
          YOUTUBE-TO-CAROUSEL GENERATOR
        </p>
      </header>

      {/* Main Title Banner */}
      <div className="text-center mb-10 space-y-2 relative z-10">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-500">
          Clip2Carousel
        </h1>
        <p className="text-xs md:text-sm tracking-[0.3em] font-mono text-slate-400 uppercase">
          TURN YOUTUBE VIDEOS INTO SHAREABLE CAROUSELS
        </p>
      </div>

      {/* Central Glass Card */}
      <div className="w-full max-w-2xl bg-[#0c131c]/80 backdrop-blur-xl border border-cyan-900/40 rounded-3xl p-6 md:p-8 shadow-2xl shadow-cyan-950/20 relative z-10 space-y-6">
        <form onSubmit={handleGenerate} className="space-y-6">
          <div className="space-y-2">
            <label className="text-xs font-mono font-bold tracking-wider text-cyan-400 uppercase flex items-center justify-between">
              <span>YOUTUBE VIDEO URL</span>
              <span className="text-[10px] text-slate-500 lowercase font-mono">
                https://youtu.be/...
              </span>
            </label>
            <input
              type="url"
              required
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="Enter a YouTube video URL"
              className="w-full bg-[#121b26] border border-cyan-950 focus:border-cyan-400/80 focus:ring-1 focus:ring-cyan-400 text-slate-200 text-sm rounded-xl px-4 py-3 outline-none transition-all placeholder:text-slate-400 font-mono"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-mono font-bold tracking-wider text-cyan-400 uppercase">
              CONTENT DIRECTION (OPTIONAL)
            </label>
            <textarea
              rows={3}
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              placeholder="E.g., Explain this topic for beginners, use a friendly tone, and focus on practical takeaways. Leave blank to let AI decide."
              className="w-full bg-[#121b26] border border-cyan-950 focus:border-cyan-400/80 focus:ring-1 focus:ring-cyan-400 text-slate-200 text-sm rounded-xl p-4 outline-none transition-all placeholder:text-slate-600 font-sans leading-relaxed resize-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="space-y-2 bg-[#101721] p-3.5 rounded-xl border border-cyan-950/60">
              <div className="flex justify-between items-center text-xs font-mono font-bold text-cyan-400">
                <label>SLIDES</label>
                <span className="text-sky-300 bg-cyan-950 px-2 py-0.5 rounded text-[11px]">
                  {slideCount}
                </span>
              </div>
              <input
                type="range"
                min="3"
                max="10"
                value={slideCount}
                onChange={(e) => setSlideCount(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
              />
            </div>

            <div className="space-y-2 bg-[#101721] p-3.5 rounded-xl border border-cyan-950/60">
              <label className="text-xs font-mono font-bold text-cyan-400 block">
                COLOR THEME
              </label>
              <select
                value={colourScheme}
                onChange={(e) => setColourScheme(e.target.value)}
                className="w-full bg-[#141f2d] border border-cyan-950 text-xs font-mono text-slate-200 rounded-lg p-2 outline-none focus:border-cyan-400"
              >
                <option>Yellow and Green</option>
                <option>Crimson and Black</option>
                <option>Blue and Silver</option>
                <option>Black and White</option>
              </select>
            </div>

            <div className="space-y-2 bg-[#101721] p-3.5 rounded-xl border border-cyan-950/60">
              <label className="text-xs font-mono font-bold text-cyan-400 block">
                VISUAL VIBE
              </label>
              <select
                value={vibe}
                onChange={(e) => setVibe(e.target.value)}
                className="w-full bg-[#141f2d] border border-cyan-950 text-xs font-mono text-slate-200 rounded-lg p-2 outline-none focus:border-cyan-400 capitalize"
              >
                <option value="modern">Modern</option>
                <option value="minimalist">Minimalist</option>
                <option value="cyberpunk">Cyberpunk</option>
                <option value="medieval">Medieval</option>
                <option value="corporate">Corporate</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-sky-400 via-cyan-400 to-blue-500 hover:from-sky-300 hover:to-blue-400 text-[#070b10] font-black tracking-widest text-sm py-4 px-6 rounded-xl transition-all shadow-[0_0_20px_rgba(34,211,238,0.15)] active:scale-[0.99] disabled:opacity-50 uppercase font-mono cursor-pointer"
          >
            {loading ? "ORCHESTRATING AGENTS..." : "GENERATE CAROUSEL"}
          </button>
        </form>

        <div className="pt-2 border-t border-cyan-950/80 space-y-2">
          <div className="flex justify-between items-center text-[10px] font-mono text-cyan-400/80 uppercase">
            <span>{statusMessage}</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full h-1.5 bg-[#121b26] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {pendingAiConsent && (
          <div className="bg-amber-950/40 border border-amber-700/80 text-amber-200 p-4 rounded-xl text-xs font-mono space-y-3">
            <div className="font-bold uppercase tracking-wider text-amber-300">No existing captions found</div>
            <p>Supadata can use AI to generate a transcript. This may consume additional credits based on the video length. Nothing will be generated until you approve.</p>
            <div className="flex flex-col sm:flex-row gap-2">
              <button type="button" onClick={(e) => handleGenerate(e, consentToken)} disabled={loading} className="rounded-lg bg-amber-300 text-slate-950 font-bold px-4 py-2 disabled:opacity-50">Continue with AI transcription</button>
              <button type="button" onClick={() => { setPendingAiConsent(false); setConsentToken(null); setStatusMessage("AI_TRANSCRIPTION_CANCELLED"); }} className="rounded-lg border border-amber-700 px-4 py-2">Cancel</button>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-950/40 border border-red-800/80 text-red-300 p-4 rounded-xl text-xs font-mono space-y-1">
            <div className="font-bold uppercase tracking-wider text-red-400">
              Execution Error
            </div>
            <p className="opacity-90">{error}</p>
          </div>
        )}
      </div>

      {result && (
        <div className="w-full max-w-4xl mt-12 space-y-8 relative z-10">
          <div className="text-center space-y-1">
            <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-blue-400">
              {result.title}
            </h2>
            <p className="text-xs font-mono text-slate-400 uppercase tracking-widest">
              {result.slides_generated} SLIDES RENDERED SUCCESSFULLY
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center justify-items-center">
            {result.files?.map((file: string, idx: number) => {
              const imageUrl = `${API_BASE_URL}/${file.replace(/^\/+/, "")}`;
              return (
                <div key={idx} className="space-y-2 w-full max-w-sm">
                  <div className="flex justify-between text-[11px] font-mono text-cyan-400 px-1">
                    <span>SLIDE 0{idx + 1}</span>
                    <a
                      href={imageUrl}
                      download
                      target="_blank"
                      rel="noreferrer"
                      className="hover:underline hover:text-white transition-colors"
                    >
                      DOWNLOAD ↗
                    </a>
                  </div>
                  <img
                    src={imageUrl}
                    alt={`Slide ${idx + 1}`}
                    className="rounded-2xl border border-cyan-900/50 shadow-2xl shadow-cyan-950/40 w-full object-cover transition-transform hover:scale-[1.01]"
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </main>
  );
}
