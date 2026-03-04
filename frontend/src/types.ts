export interface ERPResponse {
  summary: string;
  data: any[];
  chart: {
    type: 'bar' | 'pie' | 'line' | 'table' | null;
    labels: string[];
    datasets: {
      label: string;
      data: number[];
      backgroundColor?: string[];
      borderColor?: string[];
      borderWidth?: number;
    }[];
  };
}

export interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  erpResponse?: ERPResponse;
}

export interface APIRequest {
  question: string;
  chat_id: number;
}
