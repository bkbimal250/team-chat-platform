const publicApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

export const serviceConfig = {
  organization: publicApiBaseUrl,
  identity: publicApiBaseUrl,
  user: publicApiBaseUrl,
  conversation: publicApiBaseUrl,
  messaging: publicApiBaseUrl,
  media: publicApiBaseUrl,
  notification: publicApiBaseUrl,
} as const;
