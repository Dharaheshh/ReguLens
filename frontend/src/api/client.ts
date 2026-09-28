export interface HealthStatus {
  status: string;
}

export const apiClient = {
  async getHealth(): Promise<HealthStatus> {
    const response = await fetch('/api/v1/health');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }
};
