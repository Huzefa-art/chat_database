import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement, PointElement, LineElement } from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';
import { ERPResponse } from '../types';
import './ChartDisplay.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

interface ChartDisplayProps {
  erpResponse: ERPResponse;
}

const VIBRANT_PALETTE = [
  '#10b981', // Emerald
  '#8b5cf6', // Violet
  '#f59e0b', // Amber
  '#0ea5e9', // Sky
  '#f43f5e', // Rose
  '#6366f1', // Indigo
  '#ec4899', // Pink
  '#14b8a6', // Teal
];

const getColors = (count: number, alpha: number = 1) => {
  return Array.from({ length: count }, (_, i) => {
    const color = VIBRANT_PALETTE[i % VIBRANT_PALETTE.length];
    if (alpha === 1) return color;
    // Simple hex to rgba conversion
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  });
};

export default function ChartDisplay({ erpResponse }: ChartDisplayProps) {
  const { chart, data } = erpResponse;

  if (chart.type === null) {
    return null;
  }

  if (chart.type === 'table') {
    // ... same table logic
    return (
      <div className="table-container">
        {data.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                {Object.keys(data[0]).map((key) => (
                  <th key={key}>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => (
                <tr key={idx}>
                  {Object.values(row).map((value: any, cellIdx) => (
                    <td key={cellIdx}>{String(value)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    );
  }

  const enhancedDatasets = chart.datasets.map((ds, idx) => {
    if (chart.type === 'pie') {
      return {
        ...ds,
        backgroundColor: getColors(chart.labels.length, 0.8),
        borderColor: getColors(chart.labels.length, 1),
        borderWidth: 1,
      };
    }
    const color = VIBRANT_PALETTE[idx % VIBRANT_PALETTE.length];
    return {
      ...ds,
      backgroundColor: chart.type === 'line' ? `${color}33` : color,
      borderColor: color,
      borderWidth: chart.type === 'line' ? 2 : 0,
      tension: 0.3, // Smoother lines
      pointBackgroundColor: color,
    };
  });

  const chartData = {
    labels: chart.labels,
    datasets: enhancedDatasets,
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#3f3f46',
          boxWidth: 10,
          usePointStyle: true,
          pointStyle: 'circle',
          font: {
            size: 11,
            weight: 'bold' as const,
          },
        },
      },
      tooltip: {
        backgroundColor: '#18181b',
        padding: 12,
        titleFont: { size: 14, weight: 'bold' as const },
        bodyFont: { size: 13 },
        cornerRadius: 8,
        displayColors: true,
      }
    },
    scales: chart.type !== 'pie' ? {
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(0, 0, 0, 0.04)', drawBorder: false },
        ticks: { color: '#71717a', font: { size: 11 } },
      },
      x: {
        grid: { display: false },
        ticks: { color: '#71717a', font: { size: 11 } },
      },
    } : undefined,
  };

  return (
    <div className="chart-container" style={{ height: '350px' }}>
      {chart.type === 'bar' && <Bar data={chartData} options={options} />}
      {chart.type === 'pie' && <Pie data={chartData} options={options} />}
      {chart.type === 'line' && <Line data={chartData} options={options} />}
    </div>
  );
}
