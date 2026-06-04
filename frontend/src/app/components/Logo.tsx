import { Leaf } from "lucide-react";

export function Logo({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dim = size === "lg" ? "h-10 w-10" : size === "sm" ? "h-6 w-6" : "h-8 w-8";
  const text = size === "lg" ? "text-xl" : size === "sm" ? "text-sm" : "text-base";
  return (
    <div className="flex items-center gap-2">
      <div className={`${dim} rounded-lg bg-primary text-primary-foreground flex items-center justify-center shadow-sm`}>
        <Leaf className="h-1/2 w-1/2" />
      </div>
      <div className={`${text} font-medium tracking-tight text-foreground`}>
        Aussie <span className="text-primary">EcoLens</span>
      </div>
    </div>
  );
}
