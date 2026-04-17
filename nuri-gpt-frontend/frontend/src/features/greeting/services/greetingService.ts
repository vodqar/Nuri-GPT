import { api } from '../../../services/api';
import type { GreetingRequest, GreetingResponse } from '../types';

export class GreetingService {
  static async getRegions(): Promise<string[]> {
    const response = await api.get<string[]>('/greeting/regions');
    return response.data;
  }

  static async generateGreeting(data: GreetingRequest): Promise<string> {
    const response = await api.post<GreetingResponse>('/greeting/generate', data, {
      timeout: 120_000, // 날씨 API + Dify LLM 호출로 최대 120초 소요
    });
    return response.data.greeting;
  }
}
