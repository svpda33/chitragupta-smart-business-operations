import { Link } from "react-router-dom";
import { SearchX } from "lucide-react";
import EmptyState from "../components/common/EmptyState.jsx";

export default function NotFoundPage() {
  return (
    <EmptyState
      icon={SearchX}
      title="Page not found"
      message="The page you are looking for does not exist."
      action={
        <Link
          to="/"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Go to dashboard
        </Link>
      }
    />
  );
}
