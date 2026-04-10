import { z } from 'zod';

export const loginSchema = z.object({
  email: z
    .string()
    .trim()
    .email('올바른 이메일 형식이 아닙니다.'),
  password: z
    .string()
    .min(8, '비밀번호는 최소 8자 이상이어야 합니다.'),
  remember: z.boolean(),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
