// Utility for handling timestamp formatting: backend stores UTC, display in IST
export function normalizeTimestamp(timestamp) {
  if (!timestamp) return null;
  let timeString = String(timestamp).trim();

  // Normalize old space-separated ISO timestamps
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(timeString)) {
    timeString = timeString.replace(' ', 'T');
  }

    // If string contains only time, prefix a dummy date so Date.parse can work reliably
  if (/^\d{2}:\d{2}:\d{2}(?:[Zz]|[+\-]\d{2}:?\d{2})?$/.test(timeString)) {
    timeString = `1970-01-01T${timeString}`;
  }

  // If no timezone offset or Z suffix, assume UTC (backend stores UTC)
  if (!/[Zz]|[+\-]\d{2}:?\d{2}$/.test(timeString)) {
    timeString = `${timeString}+00:00`;
  }

  return timeString;
}

export function formatTimeIST(timestamp) {
  const normalized = normalizeTimestamp(timestamp);
  if (!normalized) return "N/A";

  const ms = Date.parse(normalized);
  if (Number.isNaN(ms)) return "N/A";

  const date = new Date(ms);
  const formatter = new Intl.DateTimeFormat("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
    timeZone: "Asia/Kolkata"
  });

  return formatter.format(date);
}
