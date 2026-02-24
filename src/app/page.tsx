"use client";

import { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Compass, Hexagon, Sprout, Droplets, Flame, Mountain, Send, Maximize2, Layers } from 'lucide-react';
import WuxingRadar from '@/components/WuxingRadar';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'BAZI' | 'TAROT'>('BAZI');

  // States for Bazi
  const [date, setDate] = useState('2000-01-01');
  const [hour, setHour] = useState('12');
  const [baziData, setBaziData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState('我的事业天赋在哪里？');
  const [chatLog, setChatLog] = useState<{ role: string, content: string }[]>([]);
  const [apiKey, setApiKey] = useState('');

  const calculateBazi = async () => {
    if (!date) return alert('SYS.ERR: 时间数据缺失');
    if (!apiKey) return alert('SYS.ERR: 缺少认证密钥 (API KEY)');

    setLoading(true);
    setChatLog([...chatLog, { role: 'user', content: `[指令下达] 排盘并分析：${question}` }]);

    try {
      const res = await axios.post('/api/bazi', {
        date,
        time: hour,
        apiKey,
        question
      });

      setBaziData(res.data.bazi);
      setChatLog(prev => [...prev, { role: 'ai', content: res.data.analysis }]);
    } catch (err: any) {
      setChatLog(prev => [...prev, { role: 'error', content: err.response?.data?.error || err.message }]);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#060A0E] text-emerald-400 font-mono p-4 md:p-6 lg:p-8 flex flex-col items-center">

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-6xl flex justify-between items-center mb-8 border-b border-emerald-900/50 pb-4"
      >
        <div className="flex items-center space-x-3">
          <Compass className="w-8 h-8 text-emerald-500 animate-spin-slow" style={{ animationDuration: '30s' }} />
          <h1 className="text-2xl font-bold tracking-[0.2em] text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-500 hidden sm:block">
            CYBER-METAPHYSICS
          </h1>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-2 bg-slate-900/80 p-1 rounded-md border border-emerald-900/30">
          <button
            onClick={() => setActiveTab('BAZI')}
            className={`px-4 py-1.5 text-xs font-bold tracking-widest rounded transition-all ${activeTab === 'BAZI' ? 'bg-emerald-900/80 text-emerald-200' : 'text-emerald-700 hover:text-emerald-500'}`}
          >
            BAZI.CALC
          </button>
          <button
            onClick={() => setActiveTab('TAROT')}
            className={`px-4 py-1.5 text-xs font-bold tracking-widest rounded transition-all ${activeTab === 'TAROT' ? 'bg-violet-900/80 text-violet-200' : 'text-emerald-700 hover:text-violet-500'}`}
          >
            TAROT.SYNC
          </button>
        </div>
      </motion.div>

      {/* Main Content */}
      {activeTab === 'BAZI' ? (
        <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* Left Column: Data Input */}
          <div className="lg:col-span-3 space-y-6">
            <div className="bg-slate-950/50 border border-emerald-500/30 p-5 rounded-xl backdrop-blur-sm relative overflow-hidden group hover:border-emerald-500/60 transition-colors">
              <div className="absolute top-0 right-0 p-2 opacity-5 group-hover:opacity-10 transition-opacity"><Layers className="w-32 h-32" /></div>
              <h2 className="text-xs font-bold mb-4 text-emerald-500 tracking-widest border-b border-emerald-900/50 pb-2">/ SYS.INIT</h2>

              <div className="space-y-4 relative z-10">
                <div>
                  <label className="block text-[10px] text-emerald-600 mb-1 tracking-wider">SILICONFLOW API KEY (DEEPSEEK-V3)</label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="w-full bg-[#0B1215] border border-emerald-900/50 rounded shadow-inner p-2.5 text-emerald-400 focus:outline-none focus:border-emerald-500 text-xs font-sans"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-emerald-600 mb-1 tracking-wider">BIRTH DATE (SOLAR)</label>
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full bg-[#0B1215] border border-emerald-900/50 rounded shadow-inner p-2.5 text-emerald-400 focus:outline-none focus:border-cyan-500 text-sm [&::-webkit-calendar-picker-indicator]:filter [&::-webkit-calendar-picker-indicator]:invert"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-emerald-600 mb-1 tracking-wider">BIRTH HOUR (0-23)</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="range"
                      min="0" max="23"
                      value={hour}
                      onChange={(e) => setHour(e.target.value)}
                      className="w-full accent-emerald-500 h-1 bg-emerald-900/30 rounded-lg appearance-none cursor-pointer"
                    />
                    <span className="text-cyan-400 font-bold w-6 text-center">{hour}</span>
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] text-emerald-600 mb-1 tracking-wider mt-4">DIRECTIVE / QUERY</label>
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    className="w-full bg-[#0B1215] border border-emerald-900/50 rounded shadow-inner p-2.5 text-emerald-400 focus:outline-none focus:border-cyan-500 text-xs"
                  />
                </div>

                <button
                  onClick={calculateBazi}
                  disabled={loading}
                  className="w-full mt-6 bg-gradient-to-r from-emerald-900/80 to-cyan-900/80 hover:from-emerald-800 hover:to-cyan-800 border border-emerald-500/50 text-emerald-100 py-3 rounded-md transition-all flex justify-center items-center text-xs font-bold tracking-[0.2em] disabled:opacity-50 shadow-[0_0_15px_rgba(16,185,129,0.2)]"
                >
                  {loading ? 'COMPUTING FATE...' : 'EXECUTE'}
                </button>
              </div>
            </div>

            {/* Wuxing Radar - only visible if data exists */}
            {baziData && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-slate-950/50 border border-emerald-500/20 p-4 rounded-xl backdrop-blur-sm relative"
              >
                <h2 className="text-[10px] font-bold mb-2 text-emerald-600 tracking-widest text-center">WUXING.MATRIX</h2>
                <WuxingRadar data={baziData.wuxing} />
              </motion.div>
            )}
          </div>

          {/* Middle Column: Bazi Dashboard Display */}
          <div className="lg:col-span-3">
            {baziData ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-slate-950/80 border border-cyan-500/40 p-5 rounded-xl shadow-[0_0_20px_rgba(6,182,212,0.15)] h-full flex flex-col backdrop-blur-md relative"
              >
                <div className="absolute top-2 right-2 text-cyan-900/50"><Maximize2 className="w-5 h-5" /></div>
                <h2 className="text-xs font-bold mb-6 text-cyan-400 tracking-[0.3em] border-b border-cyan-900/50 pb-2">DECODED BAZI</h2>

                <div className="grid grid-cols-2 gap-3 mb-6 flex-1">
                  {['YEAR (年)', 'MONTH (月)', 'DAY (日)', 'TIME (时)'].map((title, i) => {
                    const val = i === 0 ? baziData.year : i === 1 ? baziData.month : i === 2 ? baziData.day : baziData.time;
                    return (
                      <div key={title} className="bg-[#0B1215] border border-cyan-900/30 p-3 flex flex-col items-center justify-center rounded-lg shadow-inner group hover:border-cyan-500/50 transition-colors relative overflow-hidden">
                        <div className="text-[9px] text-cyan-700 mb-2 font-sans tracking-wider">{title}</div>
                        <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-b from-cyan-100 to-emerald-400 group-hover:scale-110 transition-transform">
                          {val.charAt(0)}
                        </div>
                        <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-b from-cyan-300 to-emerald-600 mt-1 group-hover:scale-110 transition-transform">
                          {val.charAt(1)}
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Minimal Wuxing Legend */}
                <div className="flex justify-between text-slate-400 text-[10px] border-t border-cyan-900/30 pt-4 px-2">
                  <div className="flex items-center space-x-1"><div className="w-2 h-2 rounded-full bg-yellow-500"></div><span>M:{baziData.wuxing.metal}</span></div>
                  <div className="flex items-center space-x-1"><div className="w-2 h-2 rounded-full bg-green-500"></div><span>W:{baziData.wuxing.wood}</span></div>
                  <div className="flex items-center space-x-1"><div className="w-2 h-2 rounded-full bg-blue-500"></div><span>W:{baziData.wuxing.water}</span></div>
                  <div className="flex items-center space-x-1"><div className="w-2 h-2 rounded-full bg-red-500"></div><span>F:{baziData.wuxing.fire}</span></div>
                  <div className="flex items-center space-x-1"><div className="w-2 h-2 rounded-full bg-amber-700"></div><span>E:{baziData.wuxing.earth}</span></div>
                </div>
              </motion.div>
            ) : (
              <div className="h-full border border-dashed border-emerald-900/30 rounded-xl flex flex-col items-center justify-center text-emerald-900/50 p-6 min-h-[300px]">
                <Hexagon className="w-16 h-16 mb-4 animate-pulse opacity-50" />
                <span className="text-xs tracking-widest text-center mt-2">CYBER-ORACLE STANDBY<br />AWAITING BIOMETRIC TEMPORAL DATA</span>
              </div>
            )}
          </div>

          {/* Right Column: AI Chat Session */}
          <div className="lg:col-span-6 bg-slate-950/80 border border-emerald-500/30 rounded-xl flex flex-col h-[700px] overflow-hidden shadow-[0_0_30px_rgba(16,185,129,0.05)] backdrop-blur-md relative">

            <div className="bg-[#0B1215] border-b border-emerald-900/50 p-2.5 px-4 text-[10px] tracking-widest text-emerald-600 flex justify-between items-center z-10 box-shadow-sm">
              <span className="flex items-center"><Send className="w-3 h-3 mr-2 text-cyan-500" /> COM.LINK: SECURE</span>
              <div className="flex items-center space-x-2">
                <span className="text-slate-600">DEEPSEEK-V3/SILICON</span>
                <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_5px_#10b981]"></span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-5 md:p-8 space-y-6 relative root-scrollbar">
              {chatLog.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center opacity-10 pointer-events-none">
                  <span className="text-9xl font-bold tracking-tighter mix-blend-overlay">DESTINY</span>
                </div>
              )}

              {chatLog.map((msg, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} relative z-10`}
                >
                  <div className={`max-w-[85%] rounded-lg p-5 text-[13px] leading-[1.8] font-sans ${msg.role === 'user'
                      ? 'bg-gradient-to-br from-emerald-900/40 to-[#0B1215] border border-emerald-500/30 text-emerald-100 shadow-sm'
                      : msg.role === 'error'
                        ? 'bg-red-950/50 border border-red-500/50 text-red-300'
                        : 'bg-gradient-to-r from-[#0B1215] to-[#0d161b] border-l-2 border-l-cyan-500 border-y border-r border-[#15232d] text-cyan-50 shadow-md'
                    }`}>

                    {msg.role === 'ai' && <div className="text-[9px] text-cyan-600/80 mb-3 font-mono tracking-widest flex items-center"><Hexagon className="w-3 h-3 mr-1" /> ORACLE_RESPONSE //</div>}
                    {msg.role === 'user' && <div className="text-[9px] text-emerald-600/80 mb-3 font-mono tracking-widest text-right flex items-center justify-end">CLIENT_DIRECTIVE // <Send className="w-3 h-3 ml-1" /></div>}

                    {/* Render Markdown-like text simply (or ideally plug in react-markdown here) */}
                    <div className="whitespace-pre-wrap selection:bg-cyan-900/60 selection:text-cyan-100">{msg.content}</div>
                  </div>
                </motion.div>
              ))}

              {loading && chatLog.length > 0 && (
                <div className="flex justify-start">
                  <div className="bg-[#0B1215] border border-cyan-900/50 p-4 rounded-lg flex items-center space-x-2">
                    <span className="text-[10px] text-cyan-600 mr-2 font-mono tracking-widest">DECODING</span>
                    <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce shadow-[0_0_5px_#06b6d4]"></div>
                    <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce shadow-[0_0_5px_#06b6d4]" style={{ animationDelay: '0.15s' }}></div>
                    <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce shadow-[0_0_5px_#06b6d4]" style={{ animationDelay: '0.3s' }}></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Placeholder for Tarot Tab */
        <div className="w-full max-w-6xl h-[600px] border border-dashed border-violet-900/50 rounded-xl flex flex-col items-center justify-center text-violet-500/50 relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.05)_0%,transparent_70%)]"></div>
          <Layers className="w-20 h-20 mb-6 animate-pulse" />
          <h2 className="text-2xl font-bold tracking-[0.5em] text-violet-300">TAROT SYSTEM NULL</h2>
          <p className="mt-4 text-sm font-sans tracking-wide">模块正在接入阿卡西记录协议中... (IN DEVELOPMENT)</p>
          <button
            onClick={() => setActiveTab('BAZI')}
            className="mt-8 px-6 py-2 border border-violet-500/50 hover:bg-violet-900/30 text-violet-300 text-xs tracking-widest rounded transition-all z-10"
          >
            RETURN TO BAZI
          </button>
        </div>
      )}

      {/* Global CSS overrides for the scrollbar to make it cyber-themed */}
      <style dangerouslySetInnerHTML={{
        __html: `
        .root-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .root-scrollbar::-webkit-scrollbar-track {
          background: rgba(4, 47, 46, 0.1); 
        }
        .root-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(16, 185, 129, 0.3); 
          border-radius: 4px;
        }
        .root-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(16, 185, 129, 0.6); 
        }
      `}} />
    </div>
  );
}
