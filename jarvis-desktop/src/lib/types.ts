export type JarvisState =
  | 'idle'
  | 'listening'
  | 'transcribing'
  | 'thinking'
  | 'speaking'
  | 'awaiting_confirmation'
  | 'executing_action'
  | 'error';

export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  streaming?: boolean;
}

export interface AgentAction {
  id: string;
  action: string;
  app_name?: string;
  url?: string;
  query?: string;
  contact?: string;
  message?: string;
}

export interface Confirmation {
  action: AgentAction;
  prompt: string;
}

export interface JarvisEvent {
  id?: string;
  type:
    | 'user_input'
    | 'transcription'
    | 'ai_response_delta'
    | 'ai_response'
    | 'system_state'
    | 'action_confirmation'
    | 'action_result'
    | 'audio_level'
    | 'error';
  payload: Record<string, unknown>;
}
