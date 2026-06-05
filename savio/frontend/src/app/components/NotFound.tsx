import { Link } from "react-router";
import { Button } from "./ui/button";
import { Compass } from "lucide-react";

export function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center max-w-md">
        <div className="h-16 w-16 mx-auto rounded-full bg-secondary text-primary flex items-center justify-center">
          <Compass className="h-8 w-8" />
        </div>
        <h1 className="mt-4">Page not found</h1>
        <p className="text-sm text-muted-foreground mt-2">
          That track leads off the map. Let's head back to the dashboard.
        </p>
        <Button asChild className="mt-5">
          <Link to="/dashboard">Back to dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
