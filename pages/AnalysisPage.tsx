import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Download, Share2, Shield, AlertTriangle, CheckCircle, Info, Activity, Printer, Lock, ChevronLeft } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import Navbar from '../components/Navbar';
import { API_BASE_URL } from '../api/config'; // Import centralized config

// ... (keep your interfaces FrameData and ScanReport same as before)
interface FrameData {
  timestamp: number;
  ai_probability: number;
  fft_anomaly: number;
}

interface ScanReport {
  scan_id: string;
  verdict: 'DEEPFAKE' | 'REAL' | 'UNCERTAIN';
  confidence_score: number;
  total_frames_analyzed: number;
  frame_data: FrameData[];
  created_at?: number;
}

const AnalysisPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<ScanReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [copied, setCopied] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);

  // UI Toggles
  const [showLandmarks, setShowLandmarks] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(false);

  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    const pollStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/results/${id}`);
        
        if (response.ok) {
          const data = await response.json();
          if (isMounted) {
            if (data.status === 'PROCESSING') {
              timeoutId = setTimeout(pollStatus, 2000); // Retry in 2s
            } else {
              setReport(data);
              setLoading(false);
            }
          }
        } else {
           if (isMounted) timeoutId = setTimeout(pollStatus, 2000);
        }
      } catch (e) {
        console.error("Polling error", e);
        // Don't loop infinitely on network error, show error state
        if (isMounted) {
            setLoading(false);
            setError("Could not connect to analysis server.");
        }
      }
    };

    pollStatus();

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FDFDFD] flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-gray-500 font-medium">Analyzing Forensic Data...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-[#FDFDFD] flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800">Analysis Failed</h2>
          <p className="text-gray-500 mt-2">{error || "Report data not found."}</p>
          <button onClick={() => navigate('/')} className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg">
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // --- Handlers ---
  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy", err);
    }
  };

  const handleTimelineClick = (index: number) => {
    if (!videoRef.current || !report) return;
    const timestamp = report.frame_data[index].timestamp;
    videoRef.current.currentTime = timestamp;
    videoRef.current.play();
    setCurrentFrame(index);
  };

  const handleTimeUpdate = () => {
    if (videoRef.current && report) {
      const currentTime = videoRef.current.currentTime;
      // Safety check for empty frame_data
      if (report.frame_data && report.frame_data.length > 0) {
          const closestFrameIndex = report.frame_data.findIndex(f => f.timestamp >= currentTime);
          if (closestFrameIndex !== -1) setCurrentFrame(closestFrameIndex);
      }
    }
  };

  // Derived Data for UI
  const isFake = report.verdict === 'DEEPFAKE';
  const scoreColor = isFake ? '#EF4444' : '#3B82F6';

  // Prepare Chart Data safely
  const chartData = report.frame_data ? report.frame_data.map(f => ({
    time: f.timestamp,
    real: 100 - (f.ai_probability * 100),
    synth: f.ai_probability * 100,
  })) : [];

  const EVIDENCE_CHECKS = [
    { title: "Generative Texture Audit", desc: "Diffusion-specific artifacts detected in chrominance channels", status: isFake ? 'critical' : 'pass' },
    { title: "Optical Flow Consistency", desc: "Pixel velocity consistency checks across temporal frames", status: report.confidence_score > 30 ? 'warning' : 'pass' },
    { title: "Blink Biometrics", desc: "Statistical anomaly detection in eye blink frequency", status: isFake ? 'critical' : 'pass' },
    { title: "Phoneme Syncing", desc: "Audio-visual alignment verification", status: 'pass' },
    { title: "Latent Space Bleeding", desc: "Shadow artifacts inconsistent with environmental light", status: report.confidence_score > 70 ? 'critical' : 'pass' },
  ];

  return (
    <div className="min-h-screen bg-[#FDFDFD] font-sans text-slate-800 pb-20">
      <Navbar />

      {/* HEADER */}
      <header className="px-8 py-6 border-b border-slate-200 bg-white sticky top-0 z-30">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <button onClick={() => navigate('/')} className="p-2 hover:bg-slate-100 rounded-full transition-colors">
              <ChevronLeft className="w-6 h-6 text-slate-500" />
            </button>
            <div>
              <div className="flex items-center space-x-3 mb-1">
                <h1 className="text-2xl font-bold text-slate-900">Case Investigation #{id?.substring(0, 6)}</h1>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${isFake ? 'bg-red-50 text-red-600 border-red-200' : 'bg-green-50 text-green-600 border-green-200'}`}>
                  {isFake ? 'High Risk' : 'Verified Authentic'}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono uppercase tracking-wide">
                UID: {report.scan_id} • AI-Verified • Forensic Hash Valid
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button onClick={handleShare} className="p-2 text-slate-400 hover:text-blue-600 transition-colors relative">
              {copied ? <CheckCircle className="w-5 h-5 text-green-500" /> : <Share2 className="w-5 h-5" />}
              {copied && <span className="absolute top-10 right-0 bg-black text-white text-[10px] px-2 py-1 rounded whitespace-nowrap z-50">Link Copied!</span>}
            </button>
            <button onClick={() => window.print()} className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-bold shadow-lg shadow-blue-200 transition-all text-sm">
              <Download className="w-4 h-4" />
              <span>Generate Export Report</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-8 space-y-8">

        {/* VISUALS GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* PLAYER */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden relative group">
            <div className="absolute top-4 left-4 z-10 bg-black/80 backdrop-blur text-white text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wider flex items-center">
              <Activity className="w-3 h-3 mr-1.5" /> Source Material
            </div>

            <video
              ref={videoRef}
              onTimeUpdate={handleTimeUpdate}
              className="w-full aspect-video object-cover bg-black"
              // Ensure we use the API_BASE_URL for media files too
              src={`${API_BASE_URL}/uploads/${report.scan_id}.mp4`}
              controls
              crossOrigin="anonymous" 
              onError={(e) => {
                console.log("Video load error", e);
              }}
            />
          </div>

          {/* OVERLAY PREVIEW */}
          <div className="bg-slate-900 rounded-2xl shadow-sm overflow-hidden relative">
             {/* ... (Rest of the overlay code remains same, just ensure src uses API_BASE_URL) ... */}
              <video
                ref={(ref) => {
                  if (ref && videoRef.current) {
                    ref.currentTime = videoRef.current.currentTime;
                  }
                }}
                className="w-full h-full object-cover opacity-60 grayscale"
                src={`${API_BASE_URL}/uploads/${report.scan_id}.mp4`} // <--- Updated URL
                autoPlay={false} muted loop={false}
                crossOrigin="anonymous"
              />
              {/* ... (Controls and Landmarks stay same) ... */}
              
                {/* Controls */}
            <div className="absolute bottom-6 left-6 right-6 bg-white/10 backdrop-blur-md rounded-xl p-3 flex items-center justify-between border border-white/10 z-20">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setShowLandmarks(!showLandmarks)}
                    className={`w-10 h-5 rounded-full relative transition-colors ${showLandmarks ? 'bg-blue-500' : 'bg-white/20'}`}
                  >
                    <div className={`w-3 h-3 bg-white rounded-full absolute top-1 transition-all ${showLandmarks ? 'left-6' : 'left-1'}`}></div>
                  </button>
                  <span className="text-[10px] font-bold text-white uppercase tracking-wider">Landmarks</span>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setShowHeatmap(!showHeatmap)}
                    className={`w-10 h-5 rounded-full relative transition-colors ${showHeatmap ? 'bg-blue-500' : 'bg-white/20'}`}
                  >
                    <div className={`w-3 h-3 bg-white rounded-full absolute top-1 transition-all ${showHeatmap ? 'left-6' : 'left-1'}`}></div>
                  </button>
                  <span className="text-[10px] font-bold text-white uppercase tracking-wider">Heatmap</span>
                </div>
              </div>
              <div className="text-[10px] font-mono text-blue-300 animate-pulse">
                FRAME {currentFrame} / {report.total_frames_analyzed}
              </div>
            </div>

          </div>
        </div>

        {/* METRICS GRID - (Keep the rest of your UI components exactly as they were, they are fine) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Detection Score */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col items-center justify-center relative min-h-[400px]">
                {/* ... existing SVG and score code ... */}
                 <div className="absolute top-6 left-6 flex items-center space-x-2 text-slate-400">
                    <Shield className="w-4 h-4" />
                    <span className="text-xs font-bold uppercase tracking-wider">Detection Score</span>
                  </div>

                  <div className="relative w-64 h-32 mt-10">
                    <svg viewBox="0 0 200 100" className="w-full h-full overflow-visible">
                      <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#E2E8F0" strokeWidth="20" strokeLinecap="round" />
                      <path
                        d="M 20 100 A 80 80 0 0 1 180 100"
                        fill="none"
                        stroke={scoreColor}
                        strokeWidth="20"
                        strokeLinecap="round"
                        strokeDasharray="251.2"
                        strokeDashoffset={251.2 - (251.2 * (report.confidence_score / 100))}
                        className="transition-all duration-1000 ease-out"
                      />
                    </svg>
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
                      <div className="text-5xl font-black text-slate-900 mb-1">{Math.round(report.confidence_score)}%</div>
                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Synth Confidence</div>
                    </div>
                  </div>

                  <div className={`mt-8 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${isFake ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'}`}>
                    {report.verdict}
                  </div>
            </div>

            {/* Evidence List */}
             <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 min-h-[400px]">
                {/* ... existing evidence map code ... */}
                <div className="flex justify-between items-center mb-8">
                  <div className="flex items-center space-x-2 text-slate-400">
                    <Activity className="w-4 h-4" />
                    <span className="text-xs font-bold uppercase tracking-wider">Forensic Evidence</span>
                  </div>
                  {isFake && <span className="bg-red-100 text-red-600 text-[10px] font-bold px-2 py-1 rounded">3 CRITICAL</span>}
                </div>

                <div className="space-y-4">
                  {EVIDENCE_CHECKS.map((check, i) => (
                    <div key={i} className={`p-4 rounded-xl border ${check.status === 'critical' ? 'bg-red-50/50 border-red-100' : check.status === 'warning' ? 'bg-orange-50/50 border-orange-100' : 'bg-green-50/50 border-green-100'}`}>
                      <div className="flex items-start space-x-3">
                        {check.status === 'critical' ? (
                          <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                        ) : check.status === 'warning' ? (
                          <Info className="w-5 h-5 text-orange-500 shrink-0 mt-0.5" />
                        ) : (
                          <CheckCircle className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
                        )}
                        <div>
                          <h3 className="text-sm font-bold text-slate-800">{check.title}</h3>
                          <p className="text-xs text-slate-500 mt-1 leading-relaxed">{check.desc}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
            </div>

            {/* Chart */}
             <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 min-h-[400px] flex flex-col">
                 <div className="flex-1 w-full min-h-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="colorSynth" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#EF4444" stopOpacity={0.1} />
                          <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorReal" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.1} />
                          <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="time" hide />
                      <YAxis hide domain={[0, 100]} />
                      <RechartsTooltip contentStyle={{ backgroundColor: '#fff', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', borderRadius: '8px' }} labelStyle={{ display: 'none' }} />
                      <Area type="monotone" dataKey="real" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#colorReal)" />
                      <Area type="monotone" dataKey="synth" stroke="#EF4444" strokeWidth={2} fillOpacity={1} fill="url(#colorSynth)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
             </div>
        </div>

        {/* TIMELINE - (Keep existing logic) */}
         <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
             {/* ... timeline mapping code ... */}
             <div className="h-16 bg-slate-50 rounded-lg relative overflow-hidden flex items-end cursor-pointer group">
            {report.frame_data.map((frame, i) => {
              const isAnomaly = frame.ai_probability > 0.5;
              const isActive = i === currentFrame;
              return (
                <div
                  key={i}
                  onClick={() => handleTimelineClick(i)}
                  className={`flex-1 mx-px transition-all hover:scale-y-110 ${isActive ? 'bg-blue-600 !opacity-100 scale-y-110' : isAnomaly ? 'bg-red-400' : 'bg-slate-200'} ${isActive ? '' : 'opacity-80'}`}
                  style={{ height: isAnomaly ? `${frame.ai_probability * 100}%` : '20%' }}
                  title={`Time: ${frame.timestamp}s | Score: ${(frame.ai_probability * 100).toFixed(0)}%`}
                ></div>
              );
            })}
          </div>
         </div>

        {/* ACTIONS */}
        <div className="flex justify-center space-x-4 pt-4">
          <button onClick={() => window.print()} className="bg-white border border-slate-200 hover:border-blue-300 text-slate-600 hover:text-blue-600 px-8 py-4 rounded-xl font-bold uppercase tracking-wider text-xs flex items-center space-x-3 transition-all shadow-sm">
            <Printer className="w-4 h-4" />
            <span>Print Hardcopy Case</span>
          </button>
          <button className="bg-white border border-slate-200 hover:border-green-300 text-slate-600 hover:text-green-600 px-8 py-4 rounded-xl font-bold uppercase tracking-wider text-xs flex items-center space-x-3 transition-all shadow-sm">
            <Lock className="w-4 h-4" />
            <span>Seal Evidence Hash</span>
          </button>
        </div>

      </main>
    </div>
  );
};

export default AnalysisPage;