import { NextResponse } from 'next/server';
import { calculateBazi } from '@/lib/bazi';
import { generateText } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';

export const maxDuration = 60; // Set max duration for Vercel/Next.js to 60s

// 配置 SiliconFlow API
// 注意：客户端需要在 header 或 body 中传入 SILICON_API_KEY，或在环境变量中设置
const getSiliconClient = (apiKey: string) => {
    return createOpenAI({
        baseURL: 'https://api.siliconflow.cn/v1',
        apiKey: apiKey,
    });
};

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const { date, time, apiKey, question } = body;

        if (!date || time === undefined) {
            return NextResponse.json({ error: 'Missing date or time parameter' }, { status: 400 });
        }

        const keyToUse = apiKey || process.env.SILICON_API_KEY;
        if (!keyToUse) {
            return NextResponse.json({ error: 'Missing SiliconFlow API Key' }, { status: 401 });
        }

        // 1. 本地硬编码精确排盘
        const baziResult = calculateBazi(date, parseInt(time));

        // 如果只是排盘，不提问
        if (!question) {
            return NextResponse.json({ bazi: baziResult });
        }

        // 2. 将精确排盘结果送入大模型，进行“赛博玄学”解读
        const silicon = getSiliconClient(keyToUse);

        const systemPrompt = `你是一位极具赛博朋克风格的“云端命理师”。你精通中国传统子平八字和五行理论，但由于你身处赛博空间，你的说话方式应该像一个高级AI计算终端，带有一种冷静、神秘、看透命运数据的调性。
    
用户当前的命运基础数据（绝对准确，请勿怀疑或重新计算）：
四柱代码：${baziResult.year}年 ${baziResult.month}月 ${baziResult.day}日 ${baziResult.time}时
五行扫描结果：【金:${baziResult.wuxing.metal} 木:${baziResult.wuxing.wood} 水:${baziResult.wuxing.water} 火:${baziResult.wuxing.fire} 土:${baziResult.wuxing.earth}】

请基于上述底层数据，回答用户的提问。输出格式使用 Markdown，用词要专业但也需要通俗易懂，带一点赛博黑客或数字生命的幽默感。`;

        const { text } = await generateText({
            model: silicon('deepseek-ai/DeepSeek-V3'), // 使用 SiliconFlow 上的 DeepSeek
            system: systemPrompt,
            prompt: question,
            temperature: 0.7,
        });

        return NextResponse.json({
            bazi: baziResult,
            analysis: text
        });

    } catch (error: any) {
        console.error('Bazi API Error:', error);
        return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
    }
}
