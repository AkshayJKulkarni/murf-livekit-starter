export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'FinSaathi',
  pageTitle: 'Artha — FinSaathi Voice Assistant',
  pageDescription: 'Your personal finance guide in Hindi & English, powered by Murf Falcon',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/murf-logo.svg',
  accent: '#059669',
  logoDark: '/murf-logo-dark.svg',
  accentDark: '#34d399',
  startButtonText: 'Artha se baat karein',

  audioVisualizerType: 'wave',
  audioVisualizerColor: '#059669',
  audioVisualizerColorDark: '#34d399',
  audioVisualizerWaveLineWidth: 3,

  agentName: process.env.AGENT_NAME ?? undefined,
  sandboxId: undefined,
};
