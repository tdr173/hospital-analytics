export interface ErrorResponse {
  error: boolean;
  message: string;
  code?: string;
  fields?: Record<string, any>;
}
