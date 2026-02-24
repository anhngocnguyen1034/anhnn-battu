"use client";

import { ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip } from 'recharts';

interface WuxingData {
    metal: number;
    wood: number;
    water: number;
    fire: number;
    earth: number;
}

export default function WuxingRadar({ data }: { data: WuxingData }) {
    const chartData = [
        { subject: '金 (Metal)', A: data.metal * 20, fullMark: 100 },
        { subject: '水 (Water)', A: data.water * 20, fullMark: 100 },
        { subject: '木 (Wood)', A: data.wood * 20, fullMark: 100 },
        { subject: '火 (Fire)', A: data.fire * 20, fullMark: 100 },
        { subject: '土 (Earth)', A: data.earth * 20, fullMark: 100 },
    ];

    return (
        <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
                    <PolarGrid stroke="#064e3b" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#34d399', fontSize: 12 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#020617', border: '1px solid #065f46', color: '#10b981' }}
                        itemStyle={{ color: '#34d399' }}
                        formatter={(value: any) => [Number(value) / 20, '力量值']}
                    />
                    <Radar name="五行能量" dataKey="A" stroke="#10b981" fill="#10b981" fillOpacity={0.4} />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
}
