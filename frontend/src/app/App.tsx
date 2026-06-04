import { RouterProvider } from "react-router";
import "./components/eco-theme.css";
import { Toaster } from "./components/ui/sonner";
import { AuthProvider } from "./auth";
import { MediaLibraryProvider } from "./media-library";
import { router } from "./routes";

export default function App() {
  return (
    <AuthProvider>
      <MediaLibraryProvider>
        <div className="eco-app size-full min-h-screen">
          <RouterProvider router={router} />
          <Toaster richColors position="bottom-right" />
        </div>
      </MediaLibraryProvider>
    </AuthProvider>
  );
}
