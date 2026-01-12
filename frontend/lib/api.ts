// API client for backend communication
import { Trend, CollectionSummary } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserProfile {
  username: string;
  user_id: string;
}

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

export const api = {
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new APIError(401, 'Invalid username or password');
      }
      throw new APIError(response.status, 'Login failed');
    }

    return response.json();
  },

  async getProfile(token: string): Promise<UserProfile> {
    const response = await fetch(`${API_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new APIError(response.status, 'Failed to fetch profile');
    }

    return response.json();
  },

  /**
   * Get Top 10 trends from latest collection
   * @param token - JWT authentication token
   * @returns Array of trends sorted by momentum score DESC
   * @throws APIError if request fails (except 404 which returns empty array)
   */
  async getTrends(token: string): Promise<Trend[]> {
    const response = await fetch(`${API_URL}/trends`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
    });

    // Handle 404 as empty state (no collections yet)
    if (response.status === 404) {
      return [];
    }

    if (!response.ok) {
      throw new APIError(response.status, 'Failed to fetch trends');
    }

    return response.json();
  },

  /**
   * Get latest completed data collection metadata
   * @param token - JWT authentication token
   * @returns Collection summary or null if no collections exist
   * @throws APIError if request fails (except 404 which returns null)
   */
  async getLatestCollection(token: string): Promise<CollectionSummary | null> {
    const response = await fetch(`${API_URL}/trends/collections/latest`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
    });

    // Handle 404 as no collections yet
    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new APIError(response.status, 'Failed to fetch collection');
    }

    return response.json();
  },
};
