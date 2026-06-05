import { createBrowserRouter, Navigate } from "react-router";
import { AppShell } from "./components/AppShell";
import { AuthScreen } from "./components/AuthScreen";
import { Dashboard } from "./components/Dashboard";
import { UploadPage } from "./components/UploadPage";
import { SearchPage } from "./components/SearchPage";
import { TagsPage } from "./components/TagsPage";
import { HomePage } from "./components/HomePage";
import { NotFound } from "./components/NotFound";
import { VerifyEmailScreen } from "./components/VerifyEmailScreen";
import { ProtectedRoute, RedirectIfAuthed } from "./auth";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: HomePage,
  },
  {
    path: "/signin",
    element: (
      <RedirectIfAuthed>
        <AuthScreen mode="signin" />
      </RedirectIfAuthed>
    ),
  },
  {
    path: "/signup",
    element: (
      <RedirectIfAuthed>
        <AuthScreen mode="signup" />
      </RedirectIfAuthed>
    ),
  },
  {
    path: "/verify-email",
    element: (
      <RedirectIfAuthed>
        <VerifyEmailScreen />
      </RedirectIfAuthed>
    ),
  },
  {
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { path: "/dashboard", Component: Dashboard },
      { path: "/upload", Component: UploadPage },
      { path: "/search", element: <Navigate to="/search/tags" replace /> },
      { path: "/search/:tab", Component: SearchPage },
      { path: "/tags", Component: TagsPage },
      { path: "*", Component: NotFound },
    ],
  },
  { path: "*", Component: NotFound },
]);
