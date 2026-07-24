// Pandey Health Clinic — auth.js
// Handles Firebase client-side auth and exchanges the ID token for a
// secure server session cookie via /auth/session.
//
// IMPORTANT: every auth <form> in the templates has method="post" as a
// hard safety net. Previously these forms had no method attribute and
// relied entirely on an inline onsubmit="clinicAuth.xxx(...)" to call
// preventDefault(). If this module was still loading (slow network,
// or the nested Firebase CDN import got blocked) when the user hit
// submit, that inline handler would throw a ReferenceError *before*
// preventDefault() ran, and the browser would fall through to its
// default GET submission — which puts the email and password straight
// into the URL bar and browser history. That's exactly the bug that
// got reported.
//
// Fix, in two layers:
//   1. method="post" on every form — even in total JS failure, the
//      browser POSTs to the current URL instead of leaking creds via
//      GET query params. The matching Flask route below detects this
//      "JS never took over" case and shows a clear message instead of
//      a raw 405.
//   2. Submit handlers are bound here via addEventListener, inside the
//      module's own top-level execution — not via an inline HTML
//      attribute referencing a global that might not exist yet. If
//      this module fails to load at all, no listener attaches and the
//      method="post" safety net above is what catches it.

import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup,
  sendPasswordResetEmail,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

function setFormStatus(form, message, isError = true) {
  const el = form.querySelector(".form-status");
  if (!el) return;
  el.textContent = message;
  el.classList.toggle("form-status--error", isError);
  el.classList.toggle("form-status--ok", !isError);
}

async function exchangeIdTokenForSession(idToken, nextUrl) {
  const resp = await fetch("/auth/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idToken }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || "Login failed.");
  window.location.href = nextUrl || "/dashboard/";
}

async function handleLogin(form, nextUrl) {
  const email = form.email.value.trim();
  const password = form.password.value;
  setFormStatus(form, "Signing in...", false);

  try {
    const auth = getAuth(window.__firebaseApp);
    const cred = await signInWithEmailAndPassword(auth, email, password);
    const idToken = await cred.user.getIdToken();
    await exchangeIdTokenForSession(idToken, nextUrl);
  } catch (err) {
    setFormStatus(form, friendlyError(err), true);
  }
}

async function handleGoogleLogin(nextUrl) {
  try {
    const auth = getAuth(window.__firebaseApp);
    const provider = new GoogleAuthProvider();
    const cred = await signInWithPopup(auth, provider);
    const idToken = await cred.user.getIdToken();
    await exchangeIdTokenForSession(idToken, nextUrl);
  } catch (err) {
    const form = document.getElementById("loginForm");
    if (form) setFormStatus(form, friendlyError(err), true);
  }
}

async function handleRegister(form) {
  const name = form.name.value.trim();
  const phone = form.phone.value.trim();
  const email = form.email.value.trim();
  const password = form.password.value;
  setFormStatus(form, "Creating your account...", false);

  try {
    const auth = getAuth(window.__firebaseApp);
    const cred = await createUserWithEmailAndPassword(auth, email, password);
    const idToken = await cred.user.getIdToken();

    await fetch("/auth/register-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idToken, name, phone }),
    });

    await exchangeIdTokenForSession(idToken, "/dashboard/");
  } catch (err) {
    setFormStatus(form, friendlyError(err), true);
  }
}

async function handleForgotPassword(form) {
  const email = form.email.value.trim();
  setFormStatus(form, "Sending reset link...", false);

  try {
    const auth = getAuth(window.__firebaseApp);
    await sendPasswordResetEmail(auth, email);
    setFormStatus(form, "Check your email for a password reset link.", false);
  } catch (err) {
    setFormStatus(form, friendlyError(err), true);
  }
}

function friendlyError(err) {
  const code = err && err.code ? err.code : "";
  const map = {
    "auth/invalid-email": "That email address doesn't look right.",
    "auth/user-not-found": "No account found with that email.",
    "auth/wrong-password": "Incorrect password. Please try again.",
    "auth/invalid-credential": "Incorrect email or password. Please try again.",
    "auth/email-already-in-use": "An account already exists with that email.",
    "auth/weak-password": "Please choose a password with at least 6 characters.",
    "auth/popup-closed-by-user": "Google sign-in was cancelled.",
    "auth/network-request-failed": "Network error — check your internet connection and try again.",
  };
  return map[code] || err.message || "Something went wrong. Please try again.";
}

function init() {
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", (e) => {
      e.preventDefault();
      handleLogin(loginForm, loginForm.dataset.next || "");
    });
  }

  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", (e) => {
      e.preventDefault();
      handleRegister(registerForm);
    });
  }

  const forgotForm = document.getElementById("forgotForm");
  if (forgotForm) {
    forgotForm.addEventListener("submit", (e) => {
      e.preventDefault();
      handleForgotPassword(forgotForm);
    });
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

// Google button still uses an inline onclick (it's a plain button, not
// a form submit, so there's no native-fallback risk if this is briefly
// undefined) — kept on window for that one case.
window.clinicAuth = { handleGoogleLogin };
