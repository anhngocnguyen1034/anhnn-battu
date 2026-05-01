/**
 * Wuxing (Five Elements) color mappings for Bazi characters.
 * Ported from the Streamlit FOR-BAZI application.
 *
 * Each Heavenly Stem (天干) and Earthly Branch (地支) is assigned
 * a color corresponding to its Wuxing element:
 *   Wood (木) = Jade Green  | Fire (火) = Crimson
 *   Earth (土) = Gold       | Metal (金) = Silver
 *   Water (水) = Azure Blue
 */

/** Color hex for each individual Chinese character used in Bazi pillars. */
export const WUXING_CHAR_COLORS: Record<string, string> = {
  // Wood (木) – Jade Green
  "甲": "#50c878",
  "乙": "#50c878",
  "寅": "#50c878",
  "卯": "#50c878",

  // Fire (火) – Crimson
  "丙": "#e94560",
  "丁": "#e94560",
  "巳": "#e94560",
  "午": "#e94560",

  // Earth (土) – Gold
  "戊": "#d4af37",
  "己": "#d4af37",
  "辰": "#d4af37",
  "戌": "#d4af37",
  "丑": "#d4af37",
  "未": "#d4af37",

  // Metal (金) – Silver
  "庚": "#c0c0c0",
  "辛": "#c0c0c0",
  "申": "#c0c0c0",
  "酉": "#c0c0c0",

  // Water (水) – Azure Blue
  "壬": "#4a90d9",
  "癸": "#4a90d9",
  "亥": "#4a90d9",
  "子": "#4a90d9",
};

/** Color hex for each Wuxing element name. */
export const ELEMENT_COLORS: Record<string, string> = {
  "金": "#c0c0c0",
  "木": "#50c878",
  "水": "#4a90d9",
  "火": "#e94560",
  "土": "#d4af37",
};

/**
 * Returns the Wuxing color for a given Bazi character.
 * Falls back to the default text color if the character is unknown.
 */
export function getCharColor(char: string, fallback = "#e6edf3"): string {
  return WUXING_CHAR_COLORS[char] ?? fallback;
}

/**
 * Returns the color for a Wuxing element name.
 * Falls back to the default text color if the element is unknown.
 */
export function getElementColor(element: string, fallback = "#e6edf3"): string {
  return ELEMENT_COLORS[element] ?? fallback;
}
