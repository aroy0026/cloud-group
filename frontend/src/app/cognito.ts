import {
  AuthenticationDetails,
  CognitoUser,
  CognitoUserAttribute,
  CognitoUserPool,
  type CognitoUserSession,
} from "amazon-cognito-identity-js";

const region = import.meta.env.VITE_AWS_REGION ?? "";
const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID ?? "";
const clientId = import.meta.env.VITE_COGNITO_APP_CLIENT_ID ?? import.meta.env.VITE_COGNITO_CLIENT_ID ?? "";

export const cognitoEnabled = Boolean(region && userPoolId && clientId);

const userPool = cognitoEnabled
  ? new CognitoUserPool({
      UserPoolId: userPoolId,
      ClientId: clientId,
    })
  : null;

export type CognitoSession = {
  email: string;
  accessToken: string;
  idToken: string;
};

export function cognitoSignUp(input: {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
}) {
  if (!userPool) throw new Error("Cognito is not configured.");

  const attributes = [
    new CognitoUserAttribute({ Name: "email", Value: input.email }),
    new CognitoUserAttribute({ Name: "given_name", Value: input.firstName }),
    new CognitoUserAttribute({ Name: "family_name", Value: input.lastName }),
  ];

  return new Promise<void>((resolve, reject) => {
    userPool.signUp(input.email, input.password, attributes, [], (err) => {
      if (err) reject(normalizeCognitoError(err));
      else resolve();
    });
  });
}

export function cognitoSignIn(input: { email: string; password: string }) {
  if (!userPool) throw new Error("Cognito is not configured.");

  const user = new CognitoUser({
    Username: input.email,
    Pool: userPool,
  });
  const authDetails = new AuthenticationDetails({
    Username: input.email,
    Password: input.password,
  });

  return new Promise<CognitoSession>((resolve, reject) => {
    user.authenticateUser(authDetails, {
      onSuccess: (session) => resolve(toSession(session, input.email)),
      onFailure: (err) => reject(normalizeCognitoError(err)),
      newPasswordRequired: () => {
        reject(new Error("A new password is required for this account. Use Cognito's temporary password completion flow before signing in here."));
      },
    });
  });
}

export function cognitoConfirmSignUp(input: { email: string; code: string }) {
  if (!userPool) throw new Error("Cognito is not configured.");

  const user = new CognitoUser({
    Username: input.email,
    Pool: userPool,
  });

  return new Promise<void>((resolve, reject) => {
    user.confirmRegistration(input.code, true, (err) => {
      if (err) reject(normalizeCognitoError(err));
      else resolve();
    });
  });
}

export function cognitoResendConfirmationCode(email: string) {
  if (!userPool) throw new Error("Cognito is not configured.");

  const user = new CognitoUser({
    Username: email,
    Pool: userPool,
  });

  return new Promise<void>((resolve, reject) => {
    user.resendConfirmationCode((err) => {
      if (err) reject(normalizeCognitoError(err));
      else resolve();
    });
  });
}

export function cognitoGetCurrentSession() {
  if (!userPool) return Promise.resolve<CognitoSession | null>(null);

  const user = userPool.getCurrentUser();
  if (!user) return Promise.resolve(null);

  return new Promise<CognitoSession | null>((resolve) => {
    user.getSession((err: Error | null, session: CognitoUserSession | null) => {
      if (err || !session?.isValid()) {
        resolve(null);
        return;
      }

      resolve(toSession(session, user.getUsername()));
    });
  });
}

export async function cognitoGetCurrentIdToken() {
  const session = await cognitoGetCurrentSession();
  return session?.idToken ?? null;
}

export function cognitoSignOut() {
  if (!userPool) return;
  userPool.getCurrentUser()?.signOut();
}

function toSession(session: CognitoUserSession, fallbackEmail: string): CognitoSession {
  const idPayload = session.getIdToken().payload as { email?: string };
  return {
    email: idPayload.email ?? fallbackEmail,
    accessToken: session.getAccessToken().getJwtToken(),
    idToken: session.getIdToken().getJwtToken(),
  };
}

function normalizeCognitoError(err: unknown) {
  if (err && typeof err === "object" && "message" in err) {
    return new Error(String((err as { message: unknown }).message));
  }
  return err instanceof Error ? err : new Error("Cognito authentication failed.");
}
