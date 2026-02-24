import { Solar, Lunar, EightChar } from 'lunar-javascript';

export interface BaziData {
  year: string;
  month: string;
  day: string;
  time: string;
  wuxing: {
    metal: number;
    wood: number;
    water: number;
    fire: number;
    earth: number;
  };
  summary: string;
}

export function calculateBazi(dateString: string, hour: number): BaziData {
  const date = new Date(dateString);
  const solar = Solar.fromYmdHms(
    date.getFullYear(),
    date.getMonth() + 1,
    date.getDate(),
    hour,
    0,
    0
  );
  
  const lunar = solar.getLunar();
  const baZi = lunar.getEightChar();
  
  // 天干地支
  const yearStr = baZi.getYear();
  const monthStr = baZi.getMonth();
  const dayStr = baZi.getDay();
  const timeStr = baZi.getTime();
  
  // 五行粗略计算 (仅计算八个字本身，不计藏干，简化示例)
  // 获取天干和地支的五行
  const getWuxing = (gz: string) => {
      // 这里的逻辑可以引入更复杂的 lunar-javascript 获取五行的方法
      // lunar-javascript 的 EightChar 对象本身就有方法获取五行
      return "";
  };
  
  // lunar-javascript 直接提供了获取四柱五行的方法
  const yearWuXing = baZi.getYearWuXing();
  const monthWuXing = baZi.getMonthWuXing();
  const dayWuXing = baZi.getDayWuXing();
  const timeWuXing = baZi.getTimeWuXing();
  
  const allWuXing = yearWuXing + monthWuXing + dayWuXing + timeWuXing;
  
  const wuxingCount = {
    metal: (allWuXing.match(/金/g) || []).length,
    wood:  (allWuXing.match(/木/g) || []).length,
    water: (allWuXing.match(/水/g) || []).length,
    fire:  (allWuXing.match(/火/g) || []).length,
    earth: (allWuXing.match(/土/g) || []).length,
  };

  return {
    year: yearStr,
    month: monthStr,
    day: dayStr,
    time: timeStr,
    wuxing: wuxingCount,
    summary: `本命八字为：${yearStr}年 ${monthStr}月 ${dayStr}日 ${timeStr}时。五行包含：${yearWuXing}，${monthWuXing}，${dayWuXing}，${timeWuXing}。`
  };
}
