/**
 * Reusable formatting utilities for BrandShield AI.
 * Ensures consistent two-decimal representation across all scores,
 * percentages, and impact metrics.
 */

/**
 * Formats any numeric score or percentage to exactly two decimal places.
 * Examples:
 *   formatScore(82.79999999999999) -> "82.80"
 *   formatScore(77.89999999999999) -> "77.90"
 *   formatScore(98)                -> "98.00"
 *   formatScore(94.25)             -> "94.25"
 *   formatScore(44.2)              -> "44.20"
 *   formatScore(null)              -> "0.00"
 *
 * @param {number|string} value - The raw numeric or string score
 * @param {number} decimals - Number of decimal places (default 2)
 * @returns {string} Formatted number with exact decimal precision
 */
export function formatScore(value, decimals = 2) {
  if (value === null || value === undefined || value === '') {
    return (0).toFixed(decimals);
  }
  const num = Number(value);
  if (isNaN(num)) {
    return (0).toFixed(decimals);
  }
  return num.toFixed(decimals);
}

export default formatScore;
