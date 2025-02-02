import { onCLS, onFID, onLCP, onFCP, onTTFB, Metric } from 'web-vitals';

// This function logs performance metrics or sends them to an analytics service
const reportWebVitals = (onPerfEntry?: (metric: Metric) => void) => {
  if (onPerfEntry && typeof onPerfEntry === 'function') {
    onCLS(onPerfEntry);  // Cumulative Layout Shift
    onFID(onPerfEntry);  // First Input Delay
    onLCP(onPerfEntry);  // Largest Contentful Paint
    onFCP(onPerfEntry);  // First Contentful Paint
    onTTFB(onPerfEntry); // Time to First Byte
  }
};

export default reportWebVitals;
