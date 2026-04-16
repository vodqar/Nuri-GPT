export interface GreetingRequest {
  region: string;
  target_date: string;
  user_input?: string;
  enabled_contexts?: string[];
  name_input?: boolean;
  use_emoji?: boolean;
}

export interface GreetingResponse {
  greeting: string;
}

export interface RegionData {
  [key: string]: {
    nx: number;
    ny: number;
    mid_land_reg_id: string;
    mid_temp_reg_id: string;
  };
}
