export interface Profile {
  age: number;
  occupation: string;
  state: string;
  income: string;
  caste: string;
  language: string;
}

export interface Scheme {
  scheme_name: string;
  eligibility_status: string;
  reason: string;
  apply_url?: string;
  source_url?: string;
  source?: string;
}

export interface RecommendResponse {
  recommendations: Scheme[];
  error?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
