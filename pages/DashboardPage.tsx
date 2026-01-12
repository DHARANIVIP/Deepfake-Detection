import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import VideoUploader from '../components/VideoUploader';
import { Search, Filter, MoreHorizontal, Video, Image as ImageIcon } from 'lucide-react';
import { motion } from 'framer-motion';
// Import the central config
import { API_BASE_URL } from '../api/config';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'video' | 'image'>('video');
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setOpenMenuId(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      // Use standard fetch with the centralized URL
      const res = await fetch(`${API_BASE_URL}/api/scans`);
      
      if (!res.ok) {
        throw new Error(`Server responded with ${res.status}`);
      }
      
      const data = await res.json();
      setHistory(data);
    } catch (err) {
      console.error("Failed to load history:", err);
      setError("Could not connect to server. Ensure Backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, scanId: string) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this scan log?")) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/scans/${scanId}`, { method: 'DELETE' });
      if (res.ok) {
        setHistory(prev => prev.filter(s => s.scan_id !== scanId));
      } else {
        alert("Failed to delete scan");
      }
    } catch (err) {
      console.error("Delete error", err);
    }
    setOpenMenuId(null);
  };

  const toggleMenu = (e: React.MouseEvent, scanId: string) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === scanId ? null : scanId);
  };

  const handleFileUpload = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Show loading state or toast here if you want
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      navigate(`/analysis/${data.scan_id}`);
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Failed to upload. Check console for CORS or Network errors.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          <div className="mb-10">
            <h1 className="text-3xl font-bold mb-2 text-slate-900">Forensic Scan</h1>
            <p className="text-slate-500">Upload media for forensic verification or review past audits.</p>
          </div>

          {/* Connection Error Banner */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl flex items-center">
              <span className="font-bold mr-2">Error:</span> {error}
            </div>
          )}

          <div className="flex space-x-4 mb-8">
            <button
              onClick={() => setActiveTab('video')}
              className={`flex items-center space-x-2 px-6 py-2.5 rounded-xl font-bold transition-all ${activeTab === 'video'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                : 'bg-white text-slate-500 hover:bg-slate-100'
                }`}
            >
              <Video className="w-5 h-5" />
              <span>Video Detector</span>
            </button>
            <button
              onClick={() => setActiveTab('image')}
              className={`flex items-center space-x-2 px-6 py-2.5 rounded-xl font-bold transition-all ${activeTab === 'image'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                : 'bg-white text-slate-500 hover:bg-slate-100'
                }`}
            >
              <ImageIcon className="w-5 h-5" />
              <span>Image Detector</span>
            </button>
          </div>

          {/* Upload Area */}
          <div className="mb-16">
            <VideoUploader onUpload={handleFileUpload} type={activeTab} />
          </div>

          {/* History Table */}
          <div className="bg-white rounded-2xl overflow-hidden border border-slate-200 shadow-sm">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-xl font-bold text-slate-800">Recent Scans</h2>
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search scans..."
                    className="bg-slate-50 border border-slate-200 rounded-lg py-1.5 pl-9 pr-4 text-sm focus:outline-none focus:border-blue-500 transition-colors w-64"
                  />
                </div>
                <button className="p-2 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
                  <Filter className="w-4 h-4 text-slate-600" />
                </button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-slate-50/50 text-xs font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100">
                    <th className="px-6 py-4">File Name / ID</th>
                    <th className="px-6 py-4">Analysis Date</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Forensic Result</th>
                    <th className="px-6 py-4">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {loading ? (
                    <tr><td colSpan={5} className="px-6 py-8 text-center text-slate-500">Loading history...</td></tr>
                  ) : history.length === 0 ? (
                    <tr><td colSpan={5} className="px-6 py-8 text-center text-slate-500">No recent scans found.</td></tr>
                  ) : history.map((scan, i) => (
                    <motion.tr
                      key={scan.scan_id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="hover:bg-slate-50 transition-colors group cursor-pointer"
                      onClick={() => navigate(`/analysis/${scan.scan_id}`)}
                    >
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="font-medium text-sm text-slate-800 group-hover:text-blue-600 transition-colors">
                            Investigation_{scan.scan_id.substring(0, 6)}.mp4
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">{scan.scan_id}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500 font-mono">
                        {scan.created_at ? new Date(scan.created_at * 1000).toLocaleString() : 'N/A'}
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-green-50 text-green-600 border border-green-100">
                          COMPLETED
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-2">
                          <span className={`text-sm font-bold ${scan.verdict === 'DEEPFAKE' ? 'text-red-500' : 'text-blue-500'}`}>
                            {scan.verdict === 'DEEPFAKE' ? 'Fake' : 'Real'}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">({scan.confidence_score}%)</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 relative">
                        <div className="relative">
                          <button
                            onClick={(e) => toggleMenu(e, scan.scan_id)}
                            className="text-slate-400 hover:text-slate-700 transition-colors p-1 rounded-full hover:bg-slate-200"
                          >
                            <MoreHorizontal className="w-5 h-5" />
                          </button>

                          {openMenuId === scan.scan_id && (
                            <div className="absolute right-0 top-full mt-1 w-32 bg-white rounded-lg shadow-xl border border-slate-100 z-50 overflow-hidden">
                              <button
                                onClick={(e) => handleDelete(e, scan.scan_id)}
                                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 font-medium flex items-center"
                              >
                                Delete Log
                              </button>
                            </div>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;