import type { User } from "../api/types";
import { hasPrefsConfiguredForEmail } from "../api/client";
import type { NavigateFunction } from "react-router-dom";

export function redirectAfterAuth(
  me: User,
  navigate: NavigateFunction,
  from = "/offres"
) {
  if (me.must_change_password) {
    navigate("/changer-mot-de-passe", { replace: true });
    return;
  }

  const prefsReady =
    me.preferences_configurees || hasPrefsConfiguredForEmail(me.email);

  if (me.role !== "admin" && !prefsReady) {
    navigate("/mes-preferences", { replace: true });
    return;
  }

  navigate(me.role === "admin" ? "/admin" : from, { replace: true });
}
