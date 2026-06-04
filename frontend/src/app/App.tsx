import { RouterProvider } from "react-router";
import "./components/eco-theme.css";
import { Toaster } from "./components/ui/sonner";
import { AuthProvider } from "./auth";
import { router } from "./routes";

export default function App() {
  return (
    <AuthProvider>
      <div className="eco-app size-full min-h-screen">
        <RouterProvider router={router} />
        <Toaster richColors position="bottom-right" />
      </div>
    </AuthProvider>
  );
}
