import { api } from '../../../services/api';
import type { GreetingRequest, GreetingResponse } from '../types';

export class GreetingService {
  static async getRegions(): Promise<string[]> {
    const response = await api.get<string[]>('/greeting/regions');
    return response.data;
  }

  static async generateGreeting(data: GreetingRequest): Promise<string> {
    const response = await api.post<GreetingResponse>('/greeting/generate', data);
    return response.data.greeting;
  }
}
