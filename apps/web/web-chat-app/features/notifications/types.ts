export type Notice = {
  id: string;
  conversation_id: string | null;
  message_id?: string | null;
  notification_type?: string;
  title: string | null;
  body: string | null;
  preview_mode: string;
  read_at?: string | null;
  created_at?: string;
};
