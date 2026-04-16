import type { GreetingRequest, GreetingResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export class GreetingService {
  static async getRegions(accessToken: string): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/greeting/regions`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('지역 목록을 불러오는 중 오류가 발생했습니다.');
    }

    return response.json();
  }

  static async generateGreeting(accessToken: string, data: GreetingRequest): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/greeting/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '인삿말 생성 중 오류가 발생했습니다.');
    }

    const result: GreetingResponse = await response.json();
    return result.greeting;
  }
}
