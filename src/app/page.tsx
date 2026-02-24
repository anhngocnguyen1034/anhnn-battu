"use client";

import { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Compass, Hexagon, Sprout, Droplets, Flame, Mountain, Send } from 'lucide-react';

export default function Home() {
  const [date, setDate] = useState('');
  const [hour, setHour] = useState('12');
  const [baziData, setBaziData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState('我的事业运势如何？');
  const [chatLog, setChatLog] = useState<{ role: string, content: string }[]>([]);
  const [apiKey, setApiKey] = useState('');

  const calculate = async () => {
    if (!date) return alert('请输入出生日期 (阳历)');
    if (!apiKey) return alert('请填入 SiliconFlow API Key');

    setLoading(true);
    setChatLog([...chatLog, { role: 'user', content: `排盘并分析：${question}` }]);

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
    <div className="min-h-screen bg-slate-950 text-emerald-400 font-mono p-4 md:p-8 flex flex-col items-center">

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center space-x-3 mb-12"
      >
        <Compass className="w-10 h-10 text-emerald-500 animate-spin-slow" style={{ animationDuration: '20s' }} />
        <h1 className="text-3xl font-bold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-500">
          CYBER-BAZI 赛博神算
        </h1>
      </motion.div>

      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Left Column: Data Input & Bazi Display */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-900 border border-emerald-500/30 p-6 rounded-xl shadow-[0_0_15px_rgba(16,185,129,0.1)] relative overflow-hidden">
            <div className="absolute top-0 right-0 p-2 opacity-10"><Hexagon className="w-24 h-24" /></div>
            <h2 className="text-xl font-semibold mb-4 text-emerald-300 border-b border-emerald-800 pb-2">SYS.INIT.DATA</h2>

            <div className="space-y-4 relative z-10">
              <div>
                <label className="block text-xs text-emerald-600 mb-1">SILICONFLOW API KEY</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full bg-slate-950 border border-emerald-900 rounded p-2 text-emerald-400 focus:outline-none focus:border-emerald-500 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-emerald-600 mb-1">BIRTH DATE (SOLAR)</label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full bg-slate-950 border border-emerald-900 rounded p-2 text-emerald-400 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs text-emerald-600 mb-1">BIRTH HOUR (0-23)</label>
                <input
                  type="number"
                  min="0" max="23"
                  value={hour}
                  onChange={(e) => setHour(e.target.value)}
                  className="w-full bg-slate-950 border border-emerald-900 rounded p-2 text-emerald-400 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs text-emerald-600 mb-1">INITIAL QUERY</label>
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="w-full bg-slate-950 border border-emerald-900 rounded p-2 text-emerald-400 focus:outline-none focus:border-emerald-500 text-sm"
                />
              </div>

              <button
                onClick={calculate}
                disabled={loading}
                className="w-full mt-4 bg-emerald-900/50 hover:bg-emerald-800/80 border border-emerald-500 text-emerald-300 py-2 rounded transition-all flex justify-center items-center font-bold tracking-widest disabled:opacity-50"
              >
                {loading ? 'CALCULATING DESTINY...' : 'EXECUTE PREDICTION'}
              </button>
            </div>
          </div>

          {/* Render Bazi Result if available */}
          {baziData && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-slate-900 border border-cyan-500/30 p-6 rounded-xl shadow-[0_0_15px_rgba(6,182,212,0.1)]"
            >
              <h2 className="text-sm font-semibold mb-4 text-cyan-400 text-center tracking-widest">DECODED DESTINY MATRIX</h2>

              <div className="grid grid-cols-4 gap-2 mb-6">
                {/*  四柱 */}
                {['YEAR', 'MONTH', 'DAY', 'TIME'].map((title, i) => {
                  const val = i === 0 ? baziData.year : i === 1 ? baziData.month : i === 2 ? baziData.day : baziData.time;
                  return (
                    <div key={title} className="text-center bg-slate-950 border border-slate-800 p-2 rounded">
                      <div className="text-[10px] text-slate-500 mb-1">{title}</div>
                      <div className="text-lg font-bold text-cyan-300">{val.charAt(0)}</div>
                      <div className="text-lg font-bold text-cyan-500">{val.charAt(1)}</div>
                    </div>
                  )
                })}
              </div>

              {/* 五行展示 */}
              <div className="flex justify-between text-slate-400 text-xs mt-4 border-t border-slate-800 pt-4">
                <div className="flex flex-col items-center"><Hexagon className="w-4 h-4 mb-1 text-yellow-500" />金:{baziData.wuxing.metal}</div>
                <div className="flex flex-col items-center"><Sprout className="w-4 h-4 mb-1 text-green-500" />木:{baziData.wuxing.wood}</div>
                <div className="flex flex-col items-center"><Droplets className="w-4 h-4 mb-1 text-blue-500" />水:{baziData.wuxing.water}</div>
                <div className="flex flex-col items-center"><Flame className="w-4 h-4 mb-1 text-red-500" />火:{baziData.wuxing.fire}</div>
                <div className="flex flex-col items-center"><Mountain className="w-4 h-4 mb-1 text-amber-700" />土:{baziData.wuxing.earth}</div>
              </div>
            </motion.div>
          )}

        </div>

        {/* Right Column: AI Chat Session */}
        <div className="lg:col-span-2 bg-slate-900 border border-emerald-500/20 rounded-xl flex flex-col h-[600px] overflow-hidden shadow-2xl relative">

          <div className="bg-slate-950 border-b border-emerald-900/50 p-3 text-center text-xs tracking-widest text-emerald-600 flex justify-between items-center">
            <span>SECURE CHANNEL: ESTABLISHED</span>
            <span className="animate-pulse flex h-2 w-2 rounded-full bg-emerald-500"></span>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {chatLog.length === 0 && (
              <div className="h-full flex items-center justify-center opacity-30 text-emerald-600 flex-col text-sm">
                <Hexagon className="w-16 h-16 mb-4" />
                <span>AWAITING DESTINY INPUT...</span>
              </div>
            )}

            {chatLog.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: msg.role === 'user' ? 20 : -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] rounded-lg p-4 text-sm leading-relaxed ${msg.role === 'user'
                    ? 'bg-emerald-900/30 border border-emerald-500/30 text-emerald-200'
                    : msg.role === 'error'
                      ? 'bg-red-900/30 border border-red-500/50 text-red-400'
                      : 'bg-slate-950 border border-cyan-900/50 text-cyan-100 shadow-[0_0_10px_rgba(6,182,212,0.05)]'
                  }`}>

                  {msg.role === 'ai' && <div className="text-[10px] text-cyan-600 mb-2 font-bold tracking-wider">SYSTEM.ORACLE // DEEPSEEK-V3</div>}
                  {msg.role === 'user' && <div className="text-[10px] text-emerald-600 mb-2 font-bold tracking-wider text-right">USER.QUERY</div>}

                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </motion.div>
            ))}
            {loading && chatLog.length > 0 && (
              <div className="flex justify-start">
                <div className="bg-slate-950 border border-cyan-900/50 p-4 rounded-lg flex items-center space-x-2">
                  <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
