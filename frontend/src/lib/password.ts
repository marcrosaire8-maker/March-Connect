export const PASSWORD_HINT =
  "8 caractères minimum, avec majuscule, minuscule, chiffre et caractère spécial.";

export interface PasswordValidation {
  valid: boolean;
  errors: string[];
}

export function validatePassword(password: string): PasswordValidation {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push("Au moins 8 caractères");
  }
  if (!/[A-Z]/.test(password)) {
    errors.push("Une lettre majuscule");
  }
  if (!/[a-z]/.test(password)) {
    errors.push("Une lettre minuscule");
  }
  if (!/\d/.test(password)) {
    errors.push("Un chiffre");
  }
  if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]/.test(password)) {
    errors.push("Un caractère spécial");
  }

  return { valid: errors.length === 0, errors };
}
