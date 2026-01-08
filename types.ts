
export interface ScanResult {
  id: string;
  fileName: string;
  date: string;
  status: 'Completed' | 'Processing' | 'Failed';
  result: 'Real' | 'Fake';
  probability: number;
}

export interface Artifact {
  label: string;
  status: 'Normal' | 'Abnormal' | 'Warning';
  details: string;
}

export interface FrequencyData {
  freq: number;
  original: number;
  synthetic: number;
}

export interface ForensicReport {
  id: string;
  status: 'Completed' | 'Processing' | 'Failed';
  result: 'Real' | 'Fake';
  probability: number;
  frames_analyzed: number;
  faces_detected: number;
  details: string;
  frame_data: {
    timestamp: number;
    verdict: 'Real' | 'Fake';
    probability: number;
  }[];
}
